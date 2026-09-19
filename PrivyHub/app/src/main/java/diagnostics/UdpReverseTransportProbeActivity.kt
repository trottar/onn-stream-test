package com.safeiot.privyhub.diagnostics

import android.graphics.Color
import android.os.Bundle
import android.os.Process
import android.os.SystemClock
import android.util.Log
import android.view.Gravity
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONObject
import java.io.File
import java.net.InetAddress
import java.net.InetSocketAddress
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.channels.DatagramChannel
import java.util.Locale
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.locks.LockSupport

class UdpReverseTransportProbeActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "PrivyHubReverseUdp"
        private const val DEFAULT_PORT = 48102
        private const val DEFAULT_DURATION_SECONDS = 20
        private const val HEADER_BYTES = 40
        private const val PAYLOAD_BYTES = 960
        private const val PACKET_BYTES = HEADER_BYTES + PAYLOAD_BYTES
        private const val VERSION = 1
        private const val INTERVAL_NS = 5_000_000L
        private val probeRunning = AtomicBoolean(false)
        private val MAGIC = byteArrayOf(
            'U'.code.toByte(), 'T'.code.toByte(), 'R'.code.toByte(), '1'.code.toByte()
        )
    }

    private data class SendRecord(
        val sequence: Long,
        val intendedNs: Long,
        val sendCallNs: Long,
        val sendDoneNs: Long,
        val senderWallNs: Long,
        val status: String,
    )

    private var worker: Thread? = null
    private lateinit var statusView: TextView
    @Volatile private var activityDestroyedDuringProbe = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        statusView = TextView(this).apply {
            setBackgroundColor(Color.BLACK)
            setTextColor(Color.WHITE)
            textSize = 18f
            gravity = Gravity.CENTER
            setPadding(48, 48, 48, 48)
            text = "PrivyHub reverse UDP transport probe\nPreparing..."
        }
        setContentView(statusView)

        val targetIp = intent.getStringExtra("target_ip")?.trim().orEmpty()
        val port = intent.getIntExtra("udp_port", DEFAULT_PORT).coerceIn(1024, 65535)
        val durationSeconds = intent.getIntExtra("duration_seconds", DEFAULT_DURATION_SECONDS).coerceIn(5, 300)
        val label = sanitizeLabel(intent.getStringExtra("label") ?: "reverse_udp")
        val senderPriority = intent.getStringExtra("sender_priority") ?: "urgent_audio"

        val outputDir = File(filesDir, "transport_reverse").apply { mkdirs() }
        File(outputDir, "latest_sender.csv").delete()
        File(outputDir, "latest_summary.json").delete()
        File(outputDir, "latest_progress.json").delete()

        if (targetIp.isBlank() || targetIp == "PC_IP") {
            writeFailureSummary(
                outputDir = outputDir,
                label = label,
                port = port,
                durationSeconds = durationSeconds,
                senderPriority = senderPriority,
                error = "target_ip was not supplied",
            )
            statusView.text = "Reverse UDP probe failed\nPC target address was not supplied."
            return
        }

        if (!probeRunning.compareAndSet(false, true)) {
            statusView.text = "Reverse UDP probe already running\nThe existing process-level diagnostic sender will continue."
            return
        }

        statusView.text = buildString {
            append("PrivyHub reverse UDP transport probe\n")
            append("Android -> Windows\n")
            append("UDP port: ").append(port).append("\n")
            append("Duration: ").append(durationSeconds).append(" s\n")
            append("Packet cadence: 5 ms\n")
            append("Packet bytes: ").append(PACKET_BYTES).append("\n")
            append("Sender: nonblocking DatagramChannel\n")
            append("Sender priority: ").append(senderPriority).append("\n\n")
            append("Target address is supplied locally and is not written to diagnostic output.")
        }

        worker = Thread({
            try {
                runProbe(
                    targetIp = targetIp,
                    port = port,
                    durationSeconds = durationSeconds,
                    label = label,
                    senderPriority = senderPriority,
                    outputDir = outputDir,
                )
            } catch (exc: Throwable) {
                Log.e(TAG, "Unhandled reverse-probe worker failure", exc)
                try {
                    writeFailureSummary(
                        outputDir = outputDir,
                        label = label,
                        port = port,
                        durationSeconds = durationSeconds,
                        senderPriority = senderPriority,
                        error = "Unhandled worker failure: ${exc.javaClass.simpleName}: ${exc.message}",
                    )
                } catch (summaryExc: Throwable) {
                    Log.e(TAG, "Could not write reverse-probe failure summary", summaryExc)
                }
                if (!activityDestroyedDuringProbe) {
                    try {
                        runOnUiThread {
                            statusView.text = "Reverse UDP probe failed\n${exc.javaClass.simpleName}: ${exc.message}"
                        }
                    } catch (_: Throwable) {
                    }
                }
            } finally {
                probeRunning.set(false)
            }
        }, "PrivyHubUdpReverseProbe").also { it.start() }
    }

    override fun onDestroy() {
        if (worker?.isAlive == true) {
            activityDestroyedDuringProbe = true
        }
        // Sender lifetime is intentionally independent of Activity teardown for this diagnostic.
        super.onDestroy()
    }

    private fun runProbe(
        targetIp: String,
        port: Int,
        durationSeconds: Int,
        label: String,
        senderPriority: String,
        outputDir: File,
    ) {
        applyThreadPriority(senderPriority)
        val plannedPackets = durationSeconds * 200
        val startElapsedNs = SystemClock.elapsedRealtimeNanos()
        val startWallNs = System.currentTimeMillis() * 1_000_000L
        val records = ArrayList<SendRecord>(plannedPackets)

        val targetAddress = InetAddress.getByName(targetIp)
        val target = InetSocketAddress(targetAddress, port)
        val channel = DatagramChannel.open()
        channel.configureBlocking(false)
        try {
            try { channel.socket().sendBufferSize = 1_048_576 } catch (_: Throwable) {}
            val actualSendBufferBytes = try { channel.socket().sendBufferSize } catch (_: Throwable) { -1 }
            val bytes = ByteArray(PACKET_BYTES)
            val sendBuffer = ByteBuffer.wrap(bytes)
            val firstDeadlineNs = SystemClock.elapsedRealtimeNanos() + 250_000_000L

            writeProgress(outputDir, label, plannedPackets, 0, 0, 0, 0, actualSendBufferBytes)

            for (index in 0 until plannedPackets) {
                val intendedNs = firstDeadlineNs + index.toLong() * INTERVAL_NS
                waitUntil(intendedNs)

                val callNs = SystemClock.elapsedRealtimeNanos()
                val wallNs = System.currentTimeMillis() * 1_000_000L
                fillPacket(bytes, index.toLong(), intendedNs, callNs, wallNs)
                sendBuffer.clear()

                var status: String
                val sentBytes: Int
                try {
                    sentBytes = channel.send(sendBuffer, target)
                    status = when (sentBytes) {
                        PACKET_BYTES -> "sent"
                        0 -> "would_block"
                        else -> "partial:$sentBytes"
                    }
                } catch (exc: Throwable) {
                    status = "error:${exc.javaClass.simpleName}"
                }
                val doneNs = SystemClock.elapsedRealtimeNanos()

                records.add(
                    SendRecord(
                        sequence = index.toLong(),
                        intendedNs = intendedNs,
                        sendCallNs = callNs,
                        sendDoneNs = doneNs,
                        senderWallNs = wallNs,
                        status = status,
                    )
                )

                if ((index + 1) % 200 == 0 || index + 1 == plannedPackets) {
                    val successes = records.count { it.status == "sent" }
                    val wouldBlock = records.count { it.status == "would_block" }
                    val errors = records.size - successes - wouldBlock
                    writeProgress(
                        outputDir, label, plannedPackets, records.size, successes, wouldBlock, errors,
                        actualSendBufferBytes,
                    )
                }
            }

            val endElapsedNs = SystemClock.elapsedRealtimeNanos()
            val endWallNs = System.currentTimeMillis() * 1_000_000L
            val successes = records.count { it.status == "sent" }
            val wouldBlock = records.count { it.status == "would_block" }
            val errors = records.size - successes - wouldBlock

            writeSender(File(outputDir, "latest_sender.csv"), records)
            writeSummary(
                file = File(outputDir, "latest_summary.json"),
                label = label,
                port = port,
                durationSeconds = durationSeconds,
                senderPriority = senderPriority,
                plannedPackets = plannedPackets,
                attempts = records.size,
                successes = successes,
                wouldBlock = wouldBlock,
                errors = errors,
                startElapsedNs = startElapsedNs,
                endElapsedNs = endElapsedNs,
                startWallNs = startWallNs,
                endWallNs = endWallNs,
                activityDestroyedDuringProbe = activityDestroyedDuringProbe,
                actualSendBufferBytes = actualSendBufferBytes,
            )

            if (!activityDestroyedDuringProbe) runOnUiThread {
                statusView.text = buildString {
                    append("Reverse UDP probe complete\n\n")
                    append("Attempted: ").append(records.size).append("\n")
                    append("Sent: ").append(successes).append("\n")
                    append("Would-block: ").append(wouldBlock).append("\n")
                    append("Other errors: ").append(errors).append("\n")
                    append("Cadence target: 5 ms")
                }
            }
        } finally {
            try { channel.close() } catch (_: Throwable) {}
        }
    }

    private fun waitUntil(deadlineNs: Long) {
        while (true) {
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

    private fun writeSender(file: File, records: List<SendRecord>) {
        file.bufferedWriter().use { out ->
            out.appendLine("sequence,intended_ns,send_call_ns,send_done_ns,sender_wall_ns,status")
            for (record in records) {
                out.append(record.sequence.toString()).append(',')
                out.append(record.intendedNs.toString()).append(',')
                out.append(record.sendCallNs.toString()).append(',')
                out.append(record.sendDoneNs.toString()).append(',')
                out.append(record.senderWallNs.toString()).append(',')
                out.append(csvEscape(record.status)).appendLine()
            }
        }
    }

    private fun writeProgress(
        outputDir: File,
        label: String,
        plannedPackets: Int,
        attempts: Int,
        successes: Int,
        wouldBlock: Int,
        errors: Int,
        actualSendBufferBytes: Int,
    ) {
        val json = JSONObject()
            .put("probe", "PrivyHub reverse UDP transport progress")
            .put("format_version", 1)
            .put("label", label)
            .put("sender_mode", "datagram_channel_nonblocking")
            .put("planned_packets", plannedPackets)
            .put("sender_attempts", attempts)
            .put("sender_successes", successes)
            .put("sender_would_block", wouldBlock)
            .put("sender_other_errors", errors)
            .put("actual_socket_send_buffer_bytes", actualSendBufferBytes)
            .put("android_elapsed_now_ns", SystemClock.elapsedRealtimeNanos())
            .put("target_address_persisted", false)
        File(outputDir, "latest_progress.json").writeText(json.toString(2) + "\n")
    }

    private fun writeSummary(
        file: File,
        label: String,
        port: Int,
        durationSeconds: Int,
        senderPriority: String,
        plannedPackets: Int,
        attempts: Int,
        successes: Int,
        wouldBlock: Int,
        errors: Int,
        startElapsedNs: Long,
        endElapsedNs: Long,
        startWallNs: Long,
        endWallNs: Long,
        activityDestroyedDuringProbe: Boolean,
        actualSendBufferBytes: Int,
    ) {
        val json = JSONObject()
            .put("probe", "PrivyHub reverse UDP transport laboratory")
            .put("format_version", 3)
            .put("label", label)
            .put("packet_magic", "UTR1")
            .put("packet_bytes", PACKET_BYTES)
            .put("header_bytes", HEADER_BYTES)
            .put("payload_bytes", PAYLOAD_BYTES)
            .put("port", port)
            .put("duration_seconds_requested", durationSeconds)
            .put("interval_ms_requested", 5.0)
            .put("sender_priority", senderPriority)
            .put("sender_mode", "datagram_channel_nonblocking")
            .put("planned_packets", plannedPackets)
            .put("sender_attempts", attempts)
            .put("sender_successes", successes)
            .put("sender_would_block", wouldBlock)
            .put("sender_errors", errors)
            .put("actual_socket_send_buffer_bytes", actualSendBufferBytes)
            .put("android_elapsed_start_ns", startElapsedNs)
            .put("android_elapsed_end_ns", endElapsedNs)
            .put("android_wall_start_ns", startWallNs)
            .put("android_wall_end_ns", endWallNs)
            .put("activity_destroyed_during_probe", activityDestroyedDuringProbe)
            .put("sender_lifetime_scope", "process")
            .put("target_address_persisted", false)
        file.writeText(json.toString(2) + "\n")
    }

    private fun writeFailureSummary(
        outputDir: File,
        label: String,
        port: Int,
        durationSeconds: Int,
        senderPriority: String,
        error: String,
    ) {
        val json = JSONObject()
            .put("probe", "PrivyHub reverse UDP transport laboratory")
            .put("format_version", 3)
            .put("label", label)
            .put("packet_magic", "UTR1")
            .put("port", port)
            .put("duration_seconds_requested", durationSeconds)
            .put("sender_priority", senderPriority)
            .put("sender_mode", "datagram_channel_nonblocking")
            .put("error", error)
            .put("target_address_persisted", false)
        File(outputDir, "latest_summary.json").writeText(json.toString(2) + "\n")
    }

    private fun applyThreadPriority(priority: String) {
        try {
            when (priority.lowercase(Locale.US)) {
                "urgent_audio" -> Process.setThreadPriority(Process.THREAD_PRIORITY_URGENT_AUDIO)
                "audio" -> Process.setThreadPriority(Process.THREAD_PRIORITY_AUDIO)
                else -> Process.setThreadPriority(Process.THREAD_PRIORITY_DEFAULT)
            }
        } catch (_: Throwable) {
        }
    }

    private fun sanitizeLabel(value: String): String {
        val cleaned = value.replace(Regex("[^A-Za-z0-9_.-]+"), "_").trim('_')
        return if (cleaned.isBlank()) "reverse_udp" else cleaned.take(80)
    }

    private fun csvEscape(value: String): String {
        if (!value.contains(',') && !value.contains('"') && !value.contains('\n')) return value
        return "\"" + value.replace("\"", "\"\"") + "\""
    }
}
