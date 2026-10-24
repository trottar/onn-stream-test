package com.safeiot.privyhub.streaming

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * B7: the client's stall signal, behind the system property
 * `debug.privyhub.stall_signal=<1|ms>` (CL-B7P's convention; a reboot clears
 * it). Absent = today: no monitor, no datagram, the controller loop as is.
 *
 * While the player cannot see the game — the output older than S ms (`1` =
 * 150, the floor above the gate's 120-ms clean bound; or 121-2000), or the
 * client inside its recovery gate (the full-screen "Reconnecting" overlay) —
 * the controller sender's loop sends a 24-byte `PHS1` stall datagram on the
 * controller socket every 50 ms (20/s), then one `stall_end` when gameplay is
 * shown again. The host decides whether to act (PRIVYHUB_STALL_SIGNAL).
 * Only after the session passed its startup gate.
 */
object StallSignalFlag {
    const val PROPERTY = "debug.privyhub.stall_signal"
    const val DEFAULT_MS = 150L
    const val MIN_MS = 121L
    const val MAX_MS = 2_000L

    fun parse(value: String?): Long? {
        val v = value?.trim() ?: return null
        if (v == "1") return DEFAULT_MS
        val n = v.toLongOrNull() ?: return null
        return if (n in MIN_MS..MAX_MS) n else null
    }

    /** The property, read through reflection; any failure is off. */
    fun fromSystem(): Long? =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as? String)
        } catch (_: Throwable) {
            null
        }
}

object StallPacket {
    const val SIZE = 24
    const val KIND_STALL = 1
    const val KIND_END = 2
    // B18: the session is ending (a finishing activity, before its sender stops)
    const val KIND_BYE = 3
    const val FLAG_IN_GATE = 1

    /** "PHS1" | kind u8 | flags u8 | u16 0 | seq u32 | rendered frames i64 | output age ms u32 (little-endian). */
    fun encode(kind: Int, inGate: Boolean, seq: Int, renderedFrames: Long, outputAgeMs: Long): ByteArray =
        ByteBuffer.allocate(SIZE).order(ByteOrder.LITTLE_ENDIAN).apply {
            put(byteArrayOf('P'.code.toByte(), 'H'.code.toByte(), 'S'.code.toByte(), '1'.code.toByte()))
            put(kind.toByte())
            put((if (inGate) FLAG_IN_GATE else 0).toByte())
            putShort(0)
            putInt(seq)
            putLong(renderedFrames)
            putInt(outputAgeMs.coerceIn(0L, 0xFFFF_FFFFL).toInt())
        }.array()
}

/** What the monitor reads each loop: the output's age (-1 before the first frame), the frame count, the gate. */
data class StallInputs(
    val outputAgeMs: Long,
    val renderedFrames: Long,
    val inGate: Boolean,
    val released: Boolean,
)

/** Pure: called from the controller loop (~every 8 ms); returns a datagram when one is due. */
class StallMonitor(val thresholdMs: Long, private val intervalMs: Long = 50L) {
    companion object {
        const val BYE_COUNT = 3
    }

    private var stalled = false
    private var lastSentMs = 0L
    private var seq = 0
    var stallsSent = 0L
        private set
    var endsSent = 0L
        private set

    // B18: the bye, sent on the next BYE_COUNT ticks whatever the stall state
    @Volatile
    private var byesDue = 0

    @Volatile
    var byesSent = 0L
        private set

    /** B18: a finishing activity, before its sender stops. */
    fun requestBye() {
        byesDue = BYE_COUNT
    }

    fun tick(nowMs: Long, inp: StallInputs): ByteArray? {
        if (byesDue > 0) {
            byesDue--
            byesSent++
            return StallPacket.encode(StallPacket.KIND_BYE, false, seq++, inp.renderedFrames, inp.outputAgeMs.coerceAtLeast(0L))
        }
        if (!stalled && (!inp.released || inp.outputAgeMs < 0L)) {
            return null
        }
        val stallNow = inp.outputAgeMs >= thresholdMs || inp.inGate
        if (stallNow) {
            if (stalled && nowMs - lastSentMs < intervalMs) {
                return null
            }
            stalled = true
            lastSentMs = nowMs
            stallsSent++
            return StallPacket.encode(StallPacket.KIND_STALL, inp.inGate, seq++, inp.renderedFrames,
                inp.outputAgeMs.coerceAtLeast(0L))
        }
        if (stalled) {
            stalled = false
            endsSent++
            return StallPacket.encode(StallPacket.KIND_END, false, seq++, inp.renderedFrames,
                inp.outputAgeMs.coerceAtLeast(0L))
        }
        return null
    }
}
