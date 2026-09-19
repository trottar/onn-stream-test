package com.safeiot.privyhub.diagnostics

import android.content.Context
import android.graphics.Color
import android.net.wifi.WifiManager
import android.os.Build
import android.os.Bundle
import android.os.Process
import android.os.SystemClock
import android.system.ErrnoException
import android.system.Os
import android.system.OsConstants
import android.system.StructCmsghdr
import android.system.StructMsghdr
import android.system.StructTimeval
import android.view.Gravity
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONObject
import java.io.File
import java.io.FileDescriptor
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.net.SocketTimeoutException
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.Locale
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.math.max
import kotlin.math.min

class UdpTransportProbeActivity : AppCompatActivity() {

    companion object {
        private const val DEFAULT_PORT = 48120
        private const val DEFAULT_DURATION_SECONDS = 63
        private const val HEADER_BYTES = 40
        private const val PAYLOAD_BYTES = 960
        private const val PACKET_BYTES = HEADER_BYTES + PAYLOAD_BYTES
        private const val VERSION = 1
        private const val REQUESTED_RCVBUF = 1 shl 20

        // Linux/Android asm-generic socket options. On 64-bit Android, SO_TIMESTAMPNS
        // maps to the legacy value 35. Value 64 is the time64 variant and is tried
        // only as a fallback.
        private const val SO_TIMESTAMPNS_OLD = 35
        private const val SO_TIMESTAMPNS_NEW = 64

        private val MAGIC = byteArrayOf(
            'U'.code.toByte(), 'T'.code.toByte(), 'P'.code.toByte(), '1'.code.toByte()
        )
    }

    private data class ArrivalRecord(
        val sequence: Long,
        val rxElapsedNs: Long,
        val kernelRxRealtimeNs: Long?,
        val rxWallNs: Long,
        val hostIntendedNs: Long,
        val hostPacketStampNs: Long,
        val hostWallNs: Long,
        val packetBytes: Int,
    )

    private data class ReceiveResult(
        val records: ArrayList<ArrivalRecord>,
        val invalidPackets: Long,
        val kernelTimestampOption: Int?,
        val kernelTimestampMissing: Long,
    )

    private val stopRequested = AtomicBoolean(false)
    @Volatile private var datagramSocket: DatagramSocket? = null
    @Volatile private var kernelSocketFd: FileDescriptor? = null
    @Volatile private var wifiLock: WifiManager.WifiLock? = null
    private var worker: Thread? = null
    private lateinit var statusView: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        statusView = TextView(this).apply {
            setBackgroundColor(Color.BLACK)
            setTextColor(Color.WHITE)
            textSize = 18f
            gravity = Gravity.CENTER
            setPadding(48, 48, 48, 48)
            text = "PrivyHub UDP transport probe\nPreparing receiver..."
        }
        setContentView(statusView)

        val port = intent.getIntExtra("udp_port", DEFAULT_PORT).coerceIn(1024, 65535)
        val durationSeconds = intent.getIntExtra("duration_seconds", DEFAULT_DURATION_SECONDS).coerceIn(5, 3600)
        val label = sanitizeLabel(intent.getStringExtra("label") ?: "probe")
        val receiverPriority = intent.getStringExtra("receiver_priority") ?: "default"
        val receiveMode = when (intent.getStringExtra("receive_mode")?.lowercase(Locale.US)) {
            "kernel_timestamp" -> "kernel_timestamp"
            else -> "datagram"
        }
        val wifiLockMode = when (intent.getStringExtra("wifi_lock_mode")?.lowercase(Locale.US)) {
            "low_latency" -> "low_latency"
            else -> "none"
        }
        val wifiLockAcquired = if (wifiLockMode == "low_latency") acquireLowLatencyWifiLock() else false

        val outputDir = File(filesDir, "transport_probe").apply { mkdirs() }
        File(outputDir, "latest_packets.csv").delete()
        File(outputDir, "latest_summary.json").delete()

        statusView.text = buildString {
            append("PrivyHub UDP transport probe\n")
            append("Listening on UDP ").append(port).append("\n")
            append("Duration: ").append(durationSeconds).append(" s\n")
            append("Receive mode: ").append(receiveMode).append("\n")
            append("Receiver priority: ").append(receiverPriority).append("\n")
            append("Wi-Fi lock: ").append(wifiLockMode).append(" (held=").append(wifiLockAcquired).append(")\n\n")
            append("No AudioTrack, RetroArch, MediaCodec, or game-stream receiver is active in this diagnostic.")
        }

        worker = Thread({
            runProbe(
                port = port,
                durationSeconds = durationSeconds,
                label = label,
                receiverPriority = receiverPriority,
                receiveMode = receiveMode,
                wifiLockMode = wifiLockMode,
                wifiLockAcquired = wifiLockAcquired,
                outputDir = outputDir,
            )
        }, "PrivyHubUdpTransportProbe").also { it.start() }
    }

    override fun onDestroy() {
        stopRequested.set(true)
        datagramSocket?.close()
        kernelSocketFd?.let { fd ->
            try {
                Os.close(fd)
            } catch (_: Exception) {
            }
        }
        kernelSocketFd = null
        releaseWifiLock()
        super.onDestroy()
    }

    private fun runProbe(
        port: Int,
        durationSeconds: Int,
        label: String,
        receiverPriority: String,
        receiveMode: String,
        wifiLockMode: String,
        wifiLockAcquired: Boolean,
        outputDir: File,
    ) {
        applyReceiverPriority(receiverPriority)

        val startElapsedNs = SystemClock.elapsedRealtimeNanos()
        val startWallNs = System.currentTimeMillis() * 1_000_000L
        val endDeadlineNs = startElapsedNs + durationSeconds * 1_000_000_000L

        val result = try {
            if (receiveMode == "kernel_timestamp") {
                if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) {
                    throw IllegalStateException("kernel_timestamp mode requires Android API 31+")
                }
                receiveWithKernelTimestamps(port, durationSeconds, endDeadlineNs)
            } else {
                receiveWithDatagramSocket(port, durationSeconds, endDeadlineNs)
            }
        } catch (exc: Exception) {
            val error = "Probe failed: ${exc.javaClass.simpleName}: ${exc.message}"
            runOnUiThread { statusView.text = error }
            writeFailureSummary(
                outputDir = outputDir,
                label = label,
                port = port,
                durationSeconds = durationSeconds,
                receiverPriority = receiverPriority,
                receiveMode = receiveMode,
                wifiLockMode = wifiLockMode,
                wifiLockAcquired = wifiLockAcquired,
                error = error,
            )
            datagramSocket = null
            kernelSocketFd = null
            return
        }

        datagramSocket = null
        kernelSocketFd = null

        val endElapsedNs = SystemClock.elapsedRealtimeNanos()
        val endWallNs = System.currentTimeMillis() * 1_000_000L
        val stats = computeStats(result.records)
        writePackets(File(outputDir, "latest_packets.csv"), result.records)
        writeSummary(
            file = File(outputDir, "latest_summary.json"),
            label = label,
            port = port,
            durationSeconds = durationSeconds,
            receiverPriority = receiverPriority,
            receiveMode = receiveMode,
            wifiLockMode = wifiLockMode,
            wifiLockAcquired = wifiLockAcquired,
            requestedReceiveBufferBytes = REQUESTED_RCVBUF,
            kernelTimestampOption = result.kernelTimestampOption,
            kernelTimestampMissing = result.kernelTimestampMissing,
            startElapsedNs = startElapsedNs,
            endElapsedNs = endElapsedNs,
            startWallNs = startWallNs,
            endWallNs = endWallNs,
            invalidPackets = result.invalidPackets,
            stats = stats,
        )

        releaseWifiLock()

        runOnUiThread {
            val kernel = stats.optJSONObject("kernel_arrival_intervals_unique")
            statusView.text = buildString {
                append("UDP transport probe complete\n\n")
                append("Valid packets: ").append(result.records.size).append("\n")
                append("Missing: ").append(stats.getLong("missing_packets")).append("\n")
                append("Duplicates: ").append(stats.getLong("duplicate_packets")).append("\n")
                append("App max gap: ")
                    .append(formatMs(stats.getJSONObject("app_arrival_intervals_unique").optDouble("max_ms")))
                    .append("\n")
                if (kernel != null && kernel.optInt("count", 0) > 0) {
                    append("Kernel max gap: ").append(formatMs(kernel.optDouble("max_ms")))
                } else {
                    append("Kernel timestamps: unavailable")
                }
            }
        }
    }

    private fun receiveWithDatagramSocket(
        port: Int,
        durationSeconds: Int,
        endDeadlineNs: Long,
    ): ReceiveResult {
        val records = ArrayList<ArrivalRecord>(durationSeconds * 220)
        var invalidPackets = 0L

        DatagramSocket(port).use { sock ->
            datagramSocket = sock
            sock.soTimeout = 250
            sock.receiveBufferSize = REQUESTED_RCVBUF

            val buffer = ByteArray(2048)
            val packet = DatagramPacket(buffer, buffer.size)

            while (!stopRequested.get() && SystemClock.elapsedRealtimeNanos() < endDeadlineNs) {
                packet.length = buffer.size
                try {
                    sock.receive(packet)
                    val rxElapsedNs = SystemClock.elapsedRealtimeNanos()
                    val rxWallNs = System.currentTimeMillis() * 1_000_000L

                    val parsed = parsePacket(
                        data = packet.data,
                        offset = packet.offset,
                        length = packet.length,
                        rxElapsedNs = rxElapsedNs,
                        kernelRxRealtimeNs = null,
                        rxWallNs = rxWallNs,
                    )
                    if (parsed == null) invalidPackets += 1 else records.add(parsed)
                } catch (_: SocketTimeoutException) {
                }
            }
        }

        return ReceiveResult(records, invalidPackets, null, 0L)
    }

    @Suppress("NewApi")
    private fun receiveWithKernelTimestamps(
        port: Int,
        durationSeconds: Int,
        endDeadlineNs: Long,
    ): ReceiveResult {
        val records = ArrayList<ArrivalRecord>(durationSeconds * 220)
        var invalidPackets = 0L
        var missingKernelTimestamp = 0L

        val fd = Os.socket(OsConstants.AF_INET, OsConstants.SOCK_DGRAM, OsConstants.IPPROTO_UDP)
        kernelSocketFd = fd

        try {
            Os.setsockoptInt(fd, OsConstants.SOL_SOCKET, OsConstants.SO_RCVBUF, REQUESTED_RCVBUF)
            Os.setsockoptTimeval(
                fd,
                OsConstants.SOL_SOCKET,
                OsConstants.SO_RCVTIMEO,
                StructTimeval.fromMillis(250L),
            )
            val timestampOption = enableKernelTimestamp(fd)
            Os.bind(fd, InetAddress.getByName("0.0.0.0"), port)

            val receiveBuffer = ByteBuffer.allocate(2048)

            while (!stopRequested.get() && SystemClock.elapsedRealtimeNanos() < endDeadlineNs) {
                receiveBuffer.clear()
                val message = StructMsghdr(
                    null,
                    arrayOf(receiveBuffer),
                    null,
                    0,
                )

                val bytesRead = try {
                    Os.recvmsg(fd, message, 0)
                } catch (exc: ErrnoException) {
                    if (exc.errno == OsConstants.EAGAIN || exc.errno == OsConstants.ETIMEDOUT) {
                        continue
                    }
                    throw exc
                }

                val rxElapsedNs = SystemClock.elapsedRealtimeNanos()
                val rxWallNs = System.currentTimeMillis() * 1_000_000L
                val kernelRxRealtimeNs = extractKernelTimestampNs(message.msg_control, timestampOption)
                if (kernelRxRealtimeNs == null) missingKernelTimestamp += 1L

                val parsed = parsePacket(
                    data = receiveBuffer.array(),
                    offset = 0,
                    length = bytesRead,
                    rxElapsedNs = rxElapsedNs,
                    kernelRxRealtimeNs = kernelRxRealtimeNs,
                    rxWallNs = rxWallNs,
                )
                if (parsed == null) invalidPackets += 1 else records.add(parsed)
            }

            return ReceiveResult(records, invalidPackets, timestampOption, missingKernelTimestamp)
        } finally {
            try {
                Os.close(fd)
            } catch (_: Exception) {
            }
            kernelSocketFd = null
        }
    }

    @Suppress("NewApi")
    private fun enableKernelTimestamp(fd: FileDescriptor): Int {
        val errors = ArrayList<String>()
        for (option in intArrayOf(SO_TIMESTAMPNS_OLD, SO_TIMESTAMPNS_NEW)) {
            try {
                Os.setsockoptInt(fd, OsConstants.SOL_SOCKET, option, 1)
                return option
            } catch (exc: Exception) {
                errors.add("$option:${exc.javaClass.simpleName}:${exc.message}")
            }
        }
        throw IllegalStateException("SO_TIMESTAMPNS could not be enabled (${errors.joinToString("; ")})")
    }

    private fun extractKernelTimestampNs(control: Array<StructCmsghdr>?, timestampOption: Int): Long? {
        if (control == null) return null
        for (cmsg in control) {
            if (cmsg.cmsg_level != OsConstants.SOL_SOCKET) continue
            if (cmsg.cmsg_type != timestampOption &&
                cmsg.cmsg_type != SO_TIMESTAMPNS_OLD &&
                cmsg.cmsg_type != SO_TIMESTAMPNS_NEW
            ) continue

            val data = cmsg.cmsg_data
            val bb = ByteBuffer.wrap(data).order(ByteOrder.nativeOrder())
            return when {
                data.size >= 16 -> {
                    val seconds = bb.getLong(0)
                    val nanos = bb.getLong(8)
                    seconds * 1_000_000_000L + nanos
                }
                data.size >= 8 -> {
                    val seconds = bb.getInt(0).toLong() and 0xFFFF_FFFFL
                    val nanos = bb.getInt(4).toLong() and 0xFFFF_FFFFL
                    seconds * 1_000_000_000L + nanos
                }
                else -> null
            }
        }
        return null
    }

    private fun parsePacket(
        data: ByteArray,
        offset: Int,
        length: Int,
        rxElapsedNs: Long,
        kernelRxRealtimeNs: Long?,
        rxWallNs: Long,
    ): ArrivalRecord? {
        if (length != PACKET_BYTES) return null

        val bb = ByteBuffer.wrap(data, offset, length).order(ByteOrder.LITTLE_ENDIAN)
        val magic = ByteArray(4)
        bb.get(magic)
        if (!magic.contentEquals(MAGIC)) return null

        val version = bb.get().toInt() and 0xFF
        bb.get()
        val headerBytes = bb.short.toInt() and 0xFFFF
        val sequence = bb.int.toLong() and 0xFFFF_FFFFL
        val hostIntendedNs = bb.long
        val hostPacketStampNs = bb.long
        val hostWallNs = bb.long
        val payloadBytes = bb.int

        if (version != VERSION || headerBytes != HEADER_BYTES || payloadBytes != PAYLOAD_BYTES) return null

        return ArrivalRecord(
            sequence = sequence,
            rxElapsedNs = rxElapsedNs,
            kernelRxRealtimeNs = kernelRxRealtimeNs,
            rxWallNs = rxWallNs,
            hostIntendedNs = hostIntendedNs,
            hostPacketStampNs = hostPacketStampNs,
            hostWallNs = hostWallNs,
            packetBytes = length,
        )
    }

    private fun computeStats(records: List<ArrivalRecord>): JSONObject {
        val uniqueRecords = ArrayList<ArrivalRecord>(records.size)
        val seen = HashMap<Long, Long>(records.size * 2)
        var duplicates = 0L
        var exactStampDuplicates = 0L
        var conflictingStampDuplicates = 0L
        var reordered = 0L
        var minSequence = Long.MAX_VALUE
        var maxSequence = Long.MIN_VALUE
        var maxSeen = Long.MIN_VALUE

        for (record in records) {
            val priorStamp = seen.putIfAbsent(record.sequence, record.hostPacketStampNs)
            if (priorStamp != null) {
                duplicates += 1L
                if (priorStamp == record.hostPacketStampNs) exactStampDuplicates += 1L
                else conflictingStampDuplicates += 1L
                continue
            }
            if (maxSeen != Long.MIN_VALUE && record.sequence < maxSeen) reordered += 1L
            maxSeen = max(maxSeen, record.sequence)
            minSequence = min(minSequence, record.sequence)
            maxSequence = max(maxSequence, record.sequence)
            uniqueRecords.add(record)
        }

        val uniquePackets = uniqueRecords.size.toLong()
        val expectedSpan = if (uniquePackets > 0) maxSequence - minSequence + 1L else 0L
        val missingPackets = max(0L, expectedSpan - uniquePackets)

        val appIntervalsMs = intervalsMs(uniqueRecords) { it.rxElapsedNs }
        val kernelRecords = uniqueRecords.filter { it.kernelRxRealtimeNs != null }
        val kernelIntervalsMs = intervalsMs(kernelRecords) { it.kernelRxRealtimeNs!! }

        return JSONObject().apply {
            put("timing_stream", "first_arrival_per_sequence")
            put("valid_arrivals", records.size)
            put("unique_packets", uniquePackets)
            put("duplicate_packets", duplicates)
            put("duplicate_same_host_packet_stamp", exactStampDuplicates)
            put("duplicate_conflicting_host_packet_stamp", conflictingStampDuplicates)
            put("reordered_packets", reordered)
            put("first_sequence", if (uniquePackets > 0) minSequence else JSONObject.NULL)
            put("last_sequence", if (uniquePackets > 0) maxSequence else JSONObject.NULL)
            put("missing_packets", missingPackets)
            put("app_arrival_intervals_unique", timingSummary(appIntervalsMs))
            put("kernel_timestamped_unique_packets", kernelRecords.size)
            put("kernel_arrival_intervals_unique", timingSummary(kernelIntervalsMs))
            put("burst_definition", "consecutive first-arrival intervals <2 ms")
        }
    }

    private fun intervalsMs(records: List<ArrivalRecord>, selector: (ArrivalRecord) -> Long): List<Double> {
        if (records.size < 2) return emptyList()
        val values = ArrayList<Double>(records.size - 1)
        for (i in 1 until records.size) {
            values.add((selector(records[i]) - selector(records[i - 1])) / 1_000_000.0)
        }
        return values
    }

    private fun timingSummary(values: List<Double>): JSONObject {
        val histogram = linkedMapOf(
            "lt_1_ms" to 0L,
            "1_to_2_ms" to 0L,
            "2_to_4_ms" to 0L,
            "4_to_6_ms" to 0L,
            "6_to_10_ms" to 0L,
            "10_to_15_ms" to 0L,
            "15_to_20_ms" to 0L,
            "20_to_30_ms" to 0L,
            "ge_30_ms" to 0L,
        )

        for (value in values) {
            val key = when {
                value < 1.0 -> "lt_1_ms"
                value < 2.0 -> "1_to_2_ms"
                value < 4.0 -> "2_to_4_ms"
                value < 6.0 -> "4_to_6_ms"
                value < 10.0 -> "6_to_10_ms"
                value < 15.0 -> "10_to_15_ms"
                value < 20.0 -> "15_to_20_ms"
                value < 30.0 -> "20_to_30_ms"
                else -> "ge_30_ms"
            }
            histogram[key] = histogram.getValue(key) + 1L
        }

        val histogramJson = JSONObject()
        for ((key, value) in histogram) histogramJson.put(key, value)
        histogramJson.put("lt_2_ms_total", histogram.getValue("lt_1_ms") + histogram.getValue("1_to_2_ms"))

        return valueSummary(values).apply { put("histogram", histogramJson) }
    }

    private fun valueSummary(values: List<Double>): JSONObject {
        if (values.isEmpty()) {
            return JSONObject().apply {
                put("count", 0)
                put("avg_ms", JSONObject.NULL)
                put("min_ms", JSONObject.NULL)
                put("max_ms", JSONObject.NULL)
                put("p50_ms", JSONObject.NULL)
                put("p95_ms", JSONObject.NULL)
                put("p99_ms", JSONObject.NULL)
            }
        }
        val sorted = values.sorted()
        return JSONObject().apply {
            put("count", values.size)
            put("avg_ms", values.average())
            put("min_ms", sorted.first())
            put("max_ms", sorted.last())
            put("p50_ms", percentile(sorted, 0.50))
            put("p95_ms", percentile(sorted, 0.95))
            put("p99_ms", percentile(sorted, 0.99))
        }
    }

    private fun percentile(sorted: List<Double>, fraction: Double): Double {
        if (sorted.size == 1) return sorted[0]
        val rank = (sorted.size - 1) * fraction
        val low = rank.toInt()
        val high = kotlin.math.ceil(rank).toInt()
        if (low == high) return sorted[low]
        val weight = rank - low
        return sorted[low] * (1.0 - weight) + sorted[high] * weight
    }

    private fun writePackets(file: File, records: List<ArrivalRecord>) {
        file.bufferedWriter().use { writer ->
            writer.appendLine(
                "sequence,rx_elapsed_ns,kernel_rx_realtime_ns,rx_wall_ns," +
                    "host_intended_ns,host_packet_stamp_ns,host_wall_ns,packet_bytes,valid"
            )
            for (record in records) {
                writer.append(record.sequence.toString()).append(',')
                    .append(record.rxElapsedNs.toString()).append(',')
                    .append(record.kernelRxRealtimeNs?.toString() ?: "").append(',')
                    .append(record.rxWallNs.toString()).append(',')
                    .append(record.hostIntendedNs.toString()).append(',')
                    .append(record.hostPacketStampNs.toString()).append(',')
                    .append(record.hostWallNs.toString()).append(',')
                    .append(record.packetBytes.toString()).append(",1\n")
            }
        }
    }

    private fun writeSummary(
        file: File,
        label: String,
        port: Int,
        durationSeconds: Int,
        receiverPriority: String,
        receiveMode: String,
        wifiLockMode: String,
        wifiLockAcquired: Boolean,
        requestedReceiveBufferBytes: Int,
        kernelTimestampOption: Int?,
        kernelTimestampMissing: Long,
        startElapsedNs: Long,
        endElapsedNs: Long,
        startWallNs: Long,
        endWallNs: Long,
        invalidPackets: Long,
        stats: JSONObject,
    ) {
        val root = JSONObject().apply {
            put("probe", "PrivyHub UDP transport laboratory")
            put("format_version", 2)
            put("label", label)
            put("packet_magic", "UTP1")
            put("packet_bytes", PACKET_BYTES)
            put("header_bytes", HEADER_BYTES)
            put("payload_bytes", PAYLOAD_BYTES)
            put("port", port)
            put("duration_seconds_requested", durationSeconds)
            put("receiver_priority", receiverPriority)
            put("receive_mode", receiveMode)
            put("wifi_lock_mode", wifiLockMode)
            put("wifi_lock_acquired", wifiLockAcquired)
            put("requested_socket_receive_buffer_bytes", requestedReceiveBufferBytes)
            put("kernel_timestamp_option", kernelTimestampOption ?: JSONObject.NULL)
            put("kernel_timestamp_missing_packets", kernelTimestampMissing)
            put("android_elapsed_start_ns", startElapsedNs)
            put("android_elapsed_end_ns", endElapsedNs)
            put("android_wall_start_ns", startWallNs)
            put("android_wall_end_ns", endWallNs)
            put("invalid_packets", invalidPackets)
            put("stats", stats)
            put(
                "clock_note",
                "Kernel SO_TIMESTAMPNS, Android elapsedRealtimeNanos, and host perf_counter_ns have unrelated " +
                    "epochs. Cross-layer comparisons therefore use sequence-correlated interval deltas."
            )
        }
        file.writeText(root.toString(2) + "\n")
    }

    private fun writeFailureSummary(
        outputDir: File,
        label: String,
        port: Int,
        durationSeconds: Int,
        receiverPriority: String,
        receiveMode: String,
        wifiLockMode: String,
        wifiLockAcquired: Boolean,
        error: String,
    ) {
        val root = JSONObject().apply {
            put("probe", "PrivyHub UDP transport laboratory")
            put("format_version", 2)
            put("label", label)
            put("port", port)
            put("duration_seconds_requested", durationSeconds)
            put("receiver_priority", receiverPriority)
            put("receive_mode", receiveMode)
            put("wifi_lock_mode", wifiLockMode)
            put("wifi_lock_acquired", wifiLockAcquired)
            put("error", error)
        }
        File(outputDir, "latest_summary.json").writeText(root.toString(2) + "\n")
    }

    private fun acquireLowLatencyWifiLock(): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) {
            throw IllegalStateException("WIFI_MODE_FULL_LOW_LATENCY requires Android API 29+")
        }
        val manager = applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
        val lock = manager.createWifiLock(
            WifiManager.WIFI_MODE_FULL_LOW_LATENCY,
            "PrivyHubUdpProbeLowLatency",
        )
        lock.setReferenceCounted(false)
        lock.acquire()
        wifiLock = lock
        return lock.isHeld
    }

    private fun releaseWifiLock() {
        val lock = wifiLock
        wifiLock = null
        if (lock != null && lock.isHeld) {
            try { lock.release() } catch (_: Exception) {}
        }
    }

    private fun applyReceiverPriority(value: String) {
        val priority = when (value.lowercase(Locale.US)) {
            "audio" -> Process.THREAD_PRIORITY_AUDIO
            "urgent_audio" -> Process.THREAD_PRIORITY_URGENT_AUDIO
            else -> Process.THREAD_PRIORITY_DEFAULT
        }
        try {
            Process.setThreadPriority(priority)
        } catch (_: Exception) {
        }
    }

    private fun formatMs(value: Double): String {
        return if (value.isFinite()) String.format(Locale.US, "%.3f ms", value) else "n/a"
    }

    private fun sanitizeLabel(value: String): String {
        return value.replace(Regex("[^A-Za-z0-9_.-]+"), "_").take(64).ifBlank { "probe" }
    }
}
