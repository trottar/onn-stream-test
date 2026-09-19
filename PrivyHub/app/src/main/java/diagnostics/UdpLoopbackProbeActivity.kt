package com.safeiot.privyhub.diagnostics

import android.graphics.Color
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
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.Locale
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.locks.LockSupport
import kotlin.math.ceil
import kotlin.math.max
import kotlin.math.min
import kotlin.math.abs

class UdpLoopbackProbeActivity : AppCompatActivity() {

    companion object {
        private const val DEFAULT_PORT = 48121
        private const val DEFAULT_DURATION_SECONDS = 10
        private const val HEADER_BYTES = 40
        private const val PAYLOAD_BYTES = 960
        private const val PACKET_BYTES = HEADER_BYTES + PAYLOAD_BYTES
        private const val VERSION = 1
        private const val REQUESTED_RCVBUF = 1 shl 20
        private const val INTERVAL_NS = 5_000_000L
        private const val SO_TIMESTAMPNS_OLD = 35
        private const val SO_TIMESTAMPNS_NEW = 64

        private val MAGIC = byteArrayOf(
            'U'.code.toByte(), 'T'.code.toByte(), 'P'.code.toByte(), '1'.code.toByte()
        )
    }

    private data class SendRecord(
        val sequence: Long,
        val intendedNs: Long,
        val sendCallNs: Long,
        val sendDoneNs: Long,
        val wallNs: Long,
        val status: String,
    )

    private data class ArrivalRecord(
        val sequence: Long,
        val rxElapsedNs: Long,
        val kernelRxRealtimeNs: Long?,
        val rxWallNs: Long,
        val senderIntendedNs: Long,
        val senderCallNs: Long,
        val senderWallNs: Long,
        val packetBytes: Int,
    )

    private data class ProbeResult(
        val sends: List<SendRecord>,
        val arrivals: List<ArrivalRecord>,
        val invalidPackets: Long,
        val kernelTimestampOption: Int,
        val kernelTimestampMissing: Long,
    )

    private val stopRequested = AtomicBoolean(false)
    @Volatile private var receiverFd: FileDescriptor? = null
    @Volatile private var senderSocket: DatagramSocket? = null
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
            text = "PrivyHub Android UDP loopback probe\nPreparing..."
        }
        setContentView(statusView)

        val port = intent.getIntExtra("udp_port", DEFAULT_PORT).coerceIn(1024, 65535)
        val durationSeconds = intent.getIntExtra("duration_seconds", DEFAULT_DURATION_SECONDS).coerceIn(5, 300)
        val label = sanitizeLabel(intent.getStringExtra("label") ?: "android_loopback")
        val senderPriority = intent.getStringExtra("sender_priority") ?: "urgent_audio"
        val receiverPriority = intent.getStringExtra("receiver_priority") ?: "default"

        val outputDir = File(filesDir, "transport_loopback").apply { mkdirs() }
        File(outputDir, "latest_sender.csv").delete()
        File(outputDir, "latest_packets.csv").delete()
        File(outputDir, "latest_summary.json").delete()

        statusView.text = buildString {
            append("PrivyHub Android UDP loopback probe\n")
            append("127.0.0.1:").append(port).append("\n")
            append("Duration: ").append(durationSeconds).append(" s\n")
            append("Packet cadence: 5 ms\n")
            append("Packet bytes: ").append(PACKET_BYTES).append("\n")
            append("Sender priority: ").append(senderPriority).append("\n")
            append("Receiver priority: ").append(receiverPriority).append("\n\n")
            append("No Wi-Fi path, Windows sender, AudioTrack, MediaCodec, RetroArch, or game stream is active in this probe.")
        }

        worker = Thread({
            runProbe(
                port = port,
                durationSeconds = durationSeconds,
                label = label,
                senderPriority = senderPriority,
                receiverPriority = receiverPriority,
                outputDir = outputDir,
            )
        }, "PrivyHubUdpLoopbackProbe").also { it.start() }
    }

    override fun onDestroy() {
        stopRequested.set(true)
        senderSocket?.close()
        receiverFd?.let { fd ->
            try { Os.close(fd) } catch (_: Exception) {}
        }
        receiverFd = null
        super.onDestroy()
    }

    @Suppress("NewApi")
    private fun runProbe(
        port: Int,
        durationSeconds: Int,
        label: String,
        senderPriority: String,
        receiverPriority: String,
        outputDir: File,
    ) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) {
            writeFailureSummary(outputDir, label, port, durationSeconds, senderPriority, receiverPriority,
                "kernel loopback probe requires Android API 31+")
            return
        }

        applyThreadPriority(receiverPriority)
        val startElapsedNs = SystemClock.elapsedRealtimeNanos()
        val startWallNs = System.currentTimeMillis() * 1_000_000L

        val result = try {
            runLoopbackTransport(port, durationSeconds, senderPriority)
        } catch (exc: Exception) {
            val error = "Probe failed: ${exc.javaClass.simpleName}: ${exc.message}"
            runOnUiThread { statusView.text = error }
            writeFailureSummary(outputDir, label, port, durationSeconds, senderPriority, receiverPriority, error)
            receiverFd = null
            senderSocket = null
            return
        }

        receiverFd = null
        senderSocket = null
        val endElapsedNs = SystemClock.elapsedRealtimeNanos()
        val endWallNs = System.currentTimeMillis() * 1_000_000L
        val stats = computeStats(result.sends, result.arrivals)

        writeSender(File(outputDir, "latest_sender.csv"), result.sends)
        writePackets(File(outputDir, "latest_packets.csv"), result.arrivals)
        writeSummary(
            file = File(outputDir, "latest_summary.json"),
            label = label,
            port = port,
            durationSeconds = durationSeconds,
            senderPriority = senderPriority,
            receiverPriority = receiverPriority,
            startElapsedNs = startElapsedNs,
            endElapsedNs = endElapsedNs,
            startWallNs = startWallNs,
            endWallNs = endWallNs,
            invalidPackets = result.invalidPackets,
            kernelTimestampOption = result.kernelTimestampOption,
            kernelTimestampMissing = result.kernelTimestampMissing,
            stats = stats,
        )

        runOnUiThread {
            val send = stats.getJSONObject("sender_intervals")
            val kernel = stats.getJSONObject("kernel_arrival_intervals")
            statusView.text = buildString {
                append("Android UDP loopback probe complete\n\n")
                append("Sent: ").append(stats.getLong("sender_successes")).append("\n")
                append("Unique received: ").append(stats.getLong("unique_packets")).append("\n")
                append("Missing: ").append(stats.getLong("missing_packets")).append("\n")
                append("Duplicates: ").append(stats.getLong("duplicate_packets")).append("\n")
                append("Sender p99: ").append(formatMs(send.optDouble("p99_ms"))).append("\n")
                append("Kernel p99: ").append(formatMs(kernel.optDouble("p99_ms"))).append("\n")
                append("5ms send -> kernel <2ms: ").append(stats.getLong("sender_4_to_6_ms_but_kernel_lt_2_ms")).append("\n")
                append("5ms send -> kernel >=20ms: ").append(stats.getLong("sender_4_to_6_ms_but_kernel_ge_20_ms"))
            }
        }
    }

    @Suppress("NewApi")
    private fun runLoopbackTransport(
        port: Int,
        durationSeconds: Int,
        senderPriority: String,
    ): ProbeResult {
        val fd = Os.socket(OsConstants.AF_INET, OsConstants.SOCK_DGRAM, OsConstants.IPPROTO_UDP)
        receiverFd = fd
        val arrivals = ArrayList<ArrivalRecord>(durationSeconds * 220)
        val sends = ArrayList<SendRecord>(durationSeconds * 200)
        var invalidPackets = 0L
        var missingKernelTimestamp = 0L

        try {
            Os.setsockoptInt(fd, OsConstants.SOL_SOCKET, OsConstants.SO_RCVBUF, REQUESTED_RCVBUF)
            Os.setsockoptTimeval(
                fd,
                OsConstants.SOL_SOCKET,
                OsConstants.SO_RCVTIMEO,
                StructTimeval.fromMillis(100L),
            )
            val timestampOption = enableKernelTimestamp(fd)
            val loopback = InetAddress.getByName("127.0.0.1")
            Os.bind(fd, loopback, port)

            val plannedPackets = durationSeconds * 200
            val senderStartNs = SystemClock.elapsedRealtimeNanos() + 250_000_000L
            val senderDone = AtomicBoolean(false)
            val senderThread = Thread({
                applyThreadPriority(senderPriority)
                val bytes = ByteArray(PACKET_BYTES)
                val packet = DatagramPacket(bytes, bytes.size, loopback, port)
                val socket = DatagramSocket()
                senderSocket = socket
                try {
                    for (index in 0 until plannedPackets) {
                        if (stopRequested.get()) break
                        val intendedNs = senderStartNs + index.toLong() * INTERVAL_NS
                        waitUntil(intendedNs)
                        if (stopRequested.get()) break

                        val callNs = SystemClock.elapsedRealtimeNanos()
                        val wallNs = System.currentTimeMillis() * 1_000_000L
                        fillPacket(bytes, index.toLong(), intendedNs, callNs, wallNs)
                        var status = "sent"
                        val doneNs: Long
                        try {
                            socket.send(packet)
                            doneNs = SystemClock.elapsedRealtimeNanos()
                        } catch (exc: Exception) {
                            status = "error:${exc.javaClass.simpleName}"
                            sends.add(SendRecord(index.toLong(), intendedNs, callNs, SystemClock.elapsedRealtimeNanos(), wallNs, status))
                            continue
                        }
                        sends.add(SendRecord(index.toLong(), intendedNs, callNs, doneNs, wallNs, status))
                    }
                } finally {
                    try { socket.close() } catch (_: Exception) {}
                    senderSocket = null
                    senderDone.set(true)
                }
            }, "PrivyHubUdpLoopbackSender")
            senderThread.start()

            val receiveBuffer = ByteBuffer.allocate(2048)
            val hardDeadlineNs = senderStartNs + durationSeconds * 1_000_000_000L + 1_500_000_000L
            var lastArrivalElapsedNs = 0L

            while (!stopRequested.get() && SystemClock.elapsedRealtimeNanos() < hardDeadlineNs) {
                receiveBuffer.clear()
                val message = StructMsghdr(null, arrayOf(receiveBuffer), null, 0)
                val bytesRead = try {
                    Os.recvmsg(fd, message, 0)
                } catch (exc: ErrnoException) {
                    if (exc.errno == OsConstants.EAGAIN || exc.errno == OsConstants.ETIMEDOUT) {
                        if (senderDone.get() && lastArrivalElapsedNs != 0L &&
                            SystemClock.elapsedRealtimeNanos() - lastArrivalElapsedNs > 250_000_000L
                        ) {
                            break
                        }
                        continue
                    }
                    throw exc
                }

                val rxElapsedNs = SystemClock.elapsedRealtimeNanos()
                lastArrivalElapsedNs = rxElapsedNs
                val rxWallNs = System.currentTimeMillis() * 1_000_000L
                val kernelNs = extractKernelTimestampNs(message.msg_control, timestampOption)
                if (kernelNs == null) missingKernelTimestamp += 1L

                val parsed = parsePacket(
                    data = receiveBuffer.array(),
                    length = bytesRead,
                    rxElapsedNs = rxElapsedNs,
                    kernelRxRealtimeNs = kernelNs,
                    rxWallNs = rxWallNs,
                )
                if (parsed == null) invalidPackets += 1L else arrivals.add(parsed)
            }

            senderThread.join(2000L)
            if (senderThread.isAlive) {
                throw IllegalStateException("loopback sender thread did not terminate")
            }

            return ProbeResult(
                sends = sends.toList(),
                arrivals = arrivals,
                invalidPackets = invalidPackets,
                kernelTimestampOption = timestampOption,
                kernelTimestampMissing = missingKernelTimestamp,
            )
        } finally {
            try { Os.close(fd) } catch (_: Exception) {}
            receiverFd = null
        }
    }

    private fun waitUntil(deadlineNs: Long) {
        while (!stopRequested.get()) {
            val remaining = deadlineNs - SystemClock.elapsedRealtimeNanos()
            if (remaining <= 0L) return
            if (remaining > 1_500_000L) {
                LockSupport.parkNanos(remaining - 750_000L)
            } else {
                Thread.yield()
            }
        }
    }

    private fun fillPacket(
        bytes: ByteArray,
        sequence: Long,
        intendedNs: Long,
        sendCallNs: Long,
        wallNs: Long,
    ) {
        val bb = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)
        bb.put(MAGIC)
        bb.put(VERSION.toByte())
        bb.put(0)
        bb.putShort(HEADER_BYTES.toShort())
        bb.putInt(sequence.toInt())
        bb.putLong(intendedNs)
        bb.putLong(sendCallNs)
        bb.putLong(wallNs)
        bb.putInt(PAYLOAD_BYTES)
        while (bb.position() < PACKET_BYTES) {
            bb.put(((sequence + bb.position()) and 0xFFL).toByte())
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
                data.size >= 16 -> bb.getLong(0) * 1_000_000_000L + bb.getLong(8)
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
        length: Int,
        rxElapsedNs: Long,
        kernelRxRealtimeNs: Long?,
        rxWallNs: Long,
    ): ArrivalRecord? {
        if (length != PACKET_BYTES) return null
        val bb = ByteBuffer.wrap(data, 0, length).order(ByteOrder.LITTLE_ENDIAN)
        val magic = ByteArray(4)
        bb.get(magic)
        if (!magic.contentEquals(MAGIC)) return null

        val version = bb.get().toInt() and 0xFF
        bb.get()
        val headerBytes = bb.short.toInt() and 0xFFFF
        val sequence = bb.int.toLong() and 0xFFFF_FFFFL
        val intendedNs = bb.long
        val sendCallNs = bb.long
        val senderWallNs = bb.long
        val payloadBytes = bb.int
        if (version != VERSION || headerBytes != HEADER_BYTES || payloadBytes != PAYLOAD_BYTES) return null

        return ArrivalRecord(
            sequence = sequence,
            rxElapsedNs = rxElapsedNs,
            kernelRxRealtimeNs = kernelRxRealtimeNs,
            rxWallNs = rxWallNs,
            senderIntendedNs = intendedNs,
            senderCallNs = sendCallNs,
            senderWallNs = senderWallNs,
            packetBytes = length,
        )
    }

    private fun computeStats(sends: List<SendRecord>, arrivals: List<ArrivalRecord>): JSONObject {
        val successfulSends = sends.filter { it.status == "sent" }.sortedBy { it.sequence }
        val sendBySeq = successfulSends.associateBy { it.sequence }

        val uniqueArrivals = ArrayList<ArrivalRecord>(arrivals.size)
        val seen = HashMap<Long, Long>(arrivals.size * 2)
        var duplicates = 0L
        var sameStampDuplicates = 0L
        var conflictingStampDuplicates = 0L
        var reordered = 0L
        var maxSeen = Long.MIN_VALUE

        for (record in arrivals) {
            val prior = seen.putIfAbsent(record.sequence, record.senderCallNs)
            if (prior != null) {
                duplicates += 1L
                if (prior == record.senderCallNs) sameStampDuplicates += 1L else conflictingStampDuplicates += 1L
                continue
            }
            if (maxSeen != Long.MIN_VALUE && record.sequence < maxSeen) reordered += 1L
            maxSeen = max(maxSeen, record.sequence)
            uniqueArrivals.add(record)
        }
        uniqueArrivals.sortBy { it.sequence }
        val arrivalBySeq = uniqueArrivals.associateBy { it.sequence }

        val senderIntervals = intervalsMs(successfulSends) { it.sendCallNs }
        val senderDurations = successfulSends.map { (it.sendDoneNs - it.sendCallNs) / 1_000_000.0 }
        val pacingLateness = successfulSends.map { (it.sendCallNs - it.intendedNs) / 1_000_000.0 }
        val appIntervals = intervalsMs(uniqueArrivals) { it.rxElapsedNs }
        val kernelRecords = uniqueArrivals.filter { it.kernelRxRealtimeNs != null }
        val kernelIntervals = intervalsMs(kernelRecords) { it.kernelRxRealtimeNs!! }

        val kernelMinusSender = ArrayList<Double>()
        val appMinusKernel = ArrayList<Double>()
        var sendCleanKernelBurst = 0L
        var sendCleanKernelGap = 0L
        var matchedSteps = 0L

        for (seq in 1L until successfulSends.size.toLong()) {
            val prevSend = sendBySeq[seq - 1] ?: continue
            val curSend = sendBySeq[seq] ?: continue
            val prevArrival = arrivalBySeq[seq - 1] ?: continue
            val curArrival = arrivalBySeq[seq] ?: continue
            val prevKernel = prevArrival.kernelRxRealtimeNs ?: continue
            val curKernel = curArrival.kernelRxRealtimeNs ?: continue

            val sendMs = (curSend.sendCallNs - prevSend.sendCallNs) / 1_000_000.0
            val kernelMs = (curKernel - prevKernel) / 1_000_000.0
            val appMs = (curArrival.rxElapsedNs - prevArrival.rxElapsedNs) / 1_000_000.0
            kernelMinusSender.add(kernelMs - sendMs)
            appMinusKernel.add(appMs - kernelMs)
            matchedSteps += 1L
            if (sendMs >= 4.0 && sendMs < 6.0) {
                if (kernelMs < 2.0) sendCleanKernelBurst += 1L
                if (kernelMs >= 20.0) sendCleanKernelGap += 1L
            }
        }

        val expected = successfulSends.size.toLong()
        val uniqueReceivedFromSuccessfulSends = uniqueArrivals.count { sendBySeq.containsKey(it.sequence) }.toLong()
        val missing = max(0L, expected - uniqueReceivedFromSuccessfulSends)

        return JSONObject().apply {
            put("sender_attempts", sends.size)
            put("sender_successes", successfulSends.size)
            put("sender_errors", sends.size - successfulSends.size)
            put("valid_arrivals", arrivals.size)
            put("unique_packets", uniqueArrivals.size)
            put("missing_packets", missing)
            put("duplicate_packets", duplicates)
            put("duplicate_same_sender_stamp", sameStampDuplicates)
            put("duplicate_conflicting_sender_stamp", conflictingStampDuplicates)
            put("reordered_packets", reordered)
            put("kernel_timestamped_unique_packets", kernelRecords.size)
            put("sender_intervals", timingSummary(senderIntervals))
            put("sender_send_call_duration_ms", valueSummary(senderDurations))
            put("sender_pacing_lateness_ms", valueSummary(pacingLateness))
            put("app_arrival_intervals", timingSummary(appIntervals))
            put("kernel_arrival_intervals", timingSummary(kernelIntervals))
            put("kernel_minus_sender_interval_ms", deltaSummary(kernelMinusSender))
            put("app_minus_kernel_interval_ms", deltaSummary(appMinusKernel))
            put("matched_consecutive_sequence_steps", matchedSteps)
            put("sender_4_to_6_ms_but_kernel_lt_2_ms", sendCleanKernelBurst)
            put("sender_4_to_6_ms_but_kernel_ge_20_ms", sendCleanKernelGap)
        }
    }

    private fun <T> intervalsMs(records: List<T>, selector: (T) -> Long): List<Double> {
        if (records.size < 2) return emptyList()
        val out = ArrayList<Double>(records.size - 1)
        for (i in 1 until records.size) {
            out.add((selector(records[i]) - selector(records[i - 1])) / 1_000_000.0)
        }
        return out
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
        val h = JSONObject()
        for ((key, value) in histogram) h.put(key, value)
        h.put("lt_2_ms_total", histogram.getValue("lt_1_ms") + histogram.getValue("1_to_2_ms"))
        return valueSummary(values).apply { put("histogram", h) }
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

    private fun deltaSummary(values: List<Double>): JSONObject {
        val base = valueSummary(values)
        if (values.isEmpty()) {
            base.put("max_abs_ms", JSONObject.NULL)
            base.put("abs_p95_ms", JSONObject.NULL)
            base.put("abs_p99_ms", JSONObject.NULL)
            return base
        }
        val absolute = values.map { abs(it) }.sorted()
        base.put("max_abs_ms", absolute.last())
        base.put("abs_p95_ms", percentile(absolute, 0.95))
        base.put("abs_p99_ms", percentile(absolute, 0.99))
        return base
    }

    private fun percentile(sorted: List<Double>, fraction: Double): Double {
        if (sorted.size == 1) return sorted[0]
        val rank = (sorted.size - 1) * fraction
        val low = rank.toInt()
        val high = ceil(rank).toInt()
        if (low == high) return sorted[low]
        val weight = rank - low
        return sorted[low] * (1.0 - weight) + sorted[high] * weight
    }

    private fun writeSender(file: File, records: List<SendRecord>) {
        file.bufferedWriter().use { writer ->
            writer.appendLine("sequence,intended_ns,send_call_ns,send_done_ns,wall_ns,status")
            for (r in records) {
                writer.append(r.sequence.toString()).append(',')
                    .append(r.intendedNs.toString()).append(',')
                    .append(r.sendCallNs.toString()).append(',')
                    .append(r.sendDoneNs.toString()).append(',')
                    .append(r.wallNs.toString()).append(',')
                    .append(r.status).append('\n')
            }
        }
    }

    private fun writePackets(file: File, records: List<ArrivalRecord>) {
        file.bufferedWriter().use { writer ->
            writer.appendLine(
                "sequence,rx_elapsed_ns,kernel_rx_realtime_ns,rx_wall_ns," +
                    "sender_intended_ns,sender_call_ns,sender_wall_ns,packet_bytes,valid"
            )
            for (r in records) {
                writer.append(r.sequence.toString()).append(',')
                    .append(r.rxElapsedNs.toString()).append(',')
                    .append(r.kernelRxRealtimeNs?.toString() ?: "").append(',')
                    .append(r.rxWallNs.toString()).append(',')
                    .append(r.senderIntendedNs.toString()).append(',')
                    .append(r.senderCallNs.toString()).append(',')
                    .append(r.senderWallNs.toString()).append(',')
                    .append(r.packetBytes.toString()).append(",1\n")
            }
        }
    }

    private fun writeSummary(
        file: File,
        label: String,
        port: Int,
        durationSeconds: Int,
        senderPriority: String,
        receiverPriority: String,
        startElapsedNs: Long,
        endElapsedNs: Long,
        startWallNs: Long,
        endWallNs: Long,
        invalidPackets: Long,
        kernelTimestampOption: Int,
        kernelTimestampMissing: Long,
        stats: JSONObject,
    ) {
        val root = JSONObject().apply {
            put("probe", "PrivyHub Android UDP loopback transport laboratory")
            put("format_version", 1)
            put("label", label)
            put("source", "android_loopback_127.0.0.1")
            put("packet_magic", "UTP1")
            put("packet_bytes", PACKET_BYTES)
            put("header_bytes", HEADER_BYTES)
            put("payload_bytes", PAYLOAD_BYTES)
            put("packet_interval_ms", 5)
            put("port", port)
            put("duration_seconds_requested", durationSeconds)
            put("sender_priority", senderPriority)
            put("receiver_priority", receiverPriority)
            put("kernel_timestamp_option", kernelTimestampOption)
            put("kernel_timestamp_missing_packets", kernelTimestampMissing)
            put("requested_socket_receive_buffer_bytes", REQUESTED_RCVBUF)
            put("android_elapsed_start_ns", startElapsedNs)
            put("android_elapsed_end_ns", endElapsedNs)
            put("android_wall_start_ns", startWallNs)
            put("android_wall_end_ns", endWallNs)
            put("invalid_packets", invalidPackets)
            put("stats", stats)
            put("interpretation_note",
                "Sender send-call and post-recv timestamps use elapsedRealtimeNanos; kernel SO_TIMESTAMPNS uses realtime. " +
                    "Cross-layer comparisons use sequence-correlated interval deltas, not absolute timestamp subtraction."
            )
        }
        file.writeText(root.toString(2) + "\n")
    }

    private fun writeFailureSummary(
        outputDir: File,
        label: String,
        port: Int,
        durationSeconds: Int,
        senderPriority: String,
        receiverPriority: String,
        error: String,
    ) {
        val root = JSONObject().apply {
            put("probe", "PrivyHub Android UDP loopback transport laboratory")
            put("format_version", 1)
            put("label", label)
            put("source", "android_loopback_127.0.0.1")
            put("port", port)
            put("duration_seconds_requested", durationSeconds)
            put("sender_priority", senderPriority)
            put("receiver_priority", receiverPriority)
            put("error", error)
        }
        File(outputDir, "latest_summary.json").writeText(root.toString(2) + "\n")
        runOnUiThread { statusView.text = error }
    }

    private fun applyThreadPriority(value: String) {
        val priority = when (value.lowercase(Locale.US)) {
            "audio" -> Process.THREAD_PRIORITY_AUDIO
            "urgent_audio" -> Process.THREAD_PRIORITY_URGENT_AUDIO
            else -> Process.THREAD_PRIORITY_DEFAULT
        }
        try { Process.setThreadPriority(priority) } catch (_: Exception) {}
    }

    private fun formatMs(value: Double): String =
        if (value.isFinite()) String.format(Locale.US, "%.3f ms", value) else "n/a"

    private fun sanitizeLabel(value: String): String =
        value.replace(Regex("[^A-Za-z0-9_.-]+"), "_").take(64).ifBlank { "android_loopback" }
}
