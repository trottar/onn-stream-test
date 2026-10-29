package com.safeiot.privyhub.streaming

import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.concurrent.atomic.AtomicLong
import java.util.concurrent.atomic.AtomicReference

/**
 * B10: the client under loss, behind the system property
 * `debug.privyhub.loss_guard=<1|count>` (CL-B7P's convention; a reboot clears
 * it). Absent = today: no object, no datagram, no report or heartbeat key.
 * B27: on by default -- absent / empty / junk read as `1`; `0` is that old absent.
 * B29: the cap on the hold's own clock (`tick`, the controller loop's ~8 ms) and `holdingAgeMs` for the stall
 * signal (a hold with frames still arriving is not a stall); `loss_guard_max_hold_ms` beside the episode's max wait.
 *
 * Today a dropped access unit is simply skipped and the next P-frame goes to
 * MediaCodec, which decodes it against a reference it never received; every
 * frame up to the next IDR (every 15 frames) is drawn from the wrong picture
 * and no counter moves. Here:
 * - `1`: after a drop, non-IDR frames are not queued (the surface keeps the
 *   last complete frame) until the next complete IDR, capped at 600 ms (then
 *   frames pass as today, so the client's own 1-s output-silence recovery is
 *   never tripped by the guard); one `keyframe_request` datagram per episode
 *   on the controller socket;
 * - `count`: nothing held or sent, only the counter;
 * - both: `frames_after_dropped_reference` = the non-IDR frames between a drop
 *   and the next IDR (queued = drawn corrupted; held = would have been).
 */
enum class LossGuardMode(val wire: String) {
    GUARD("guard"),
    COUNT("count"),
}

object LossGuardFlag {
    const val PROPERTY = "debug.privyhub.loss_guard"

    // B27: on unless `0` (the user's "Also adopt", 2026-10-27); `count` as before
    fun parse(value: String?): LossGuardMode? =
        when (value?.trim()) {
            "0" -> null
            "count" -> LossGuardMode.COUNT
            else -> LossGuardMode.GUARD
        }

    /** The property, read through reflection; a failed read is absent, so on (B27). */
    fun fromSystem(): LossGuardMode? =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as? String)
        } catch (_: Throwable) {
            parse(null)
        }
}

object KeyframeRequestPacket {
    const val SIZE = 24
    const val KIND_REQUEST = 1

    /** "PHK1" | kind u8 | flags u8 0 | u16 0 | seq u32 | delivered AUs i64 | drops this episode u32 (little-endian). */
    fun encode(seq: Int, deliveredAus: Long, drops: Long): ByteArray =
        ByteBuffer.allocate(SIZE).order(ByteOrder.LITTLE_ENDIAN).apply {
            put(byteArrayOf('P'.code.toByte(), 'H'.code.toByte(), 'K'.code.toByte(), '1'.code.toByte()))
            put(KIND_REQUEST.toByte())
            put(0.toByte())
            putShort(0)
            putInt(seq)
            putLong(deliveredAus)
            putInt(drops.coerceIn(0L, 0xFFFF_FFFFL).toInt())
        }.array()
}

/**
 * Called from the RTP receive thread (`onDrop`, `deliver`) and the controller
 * sender's loop (`takeRequest`); the report / heartbeat read the counters.
 */
class LossGuard(
    val mode: LossGuardMode,
    private val maxWaitMs: Long = MAX_WAIT_MS,
    private val clockMs: () -> Long = { System.nanoTime() / 1_000_000L },
) {
    companion object {
        const val MAX_WAIT_MS = 600L
    }

    @Volatile
    private var waiting = false

    @Volatile
    private var holding = false
    private var waitStartMs = 0L
    private var episodeDrops = 0L
    private var seq = 0
    private val delivered = AtomicLong(0)
    private val pending = AtomicReference<ByteArray?>(null)

    val framesAfterDroppedReference = AtomicLong(0)
    val framesHeld = AtomicLong(0)
    val episodes = AtomicLong(0)
    val timeouts = AtomicLong(0)
    val requestsSent = AtomicLong(0)
    val maxWaitObservedMs = AtomicLong(0)

    // B29: the hold's own length (<= the cap + one controller loop), and the last access unit seen while waiting
    val maxHoldObservedMs = AtomicLong(0)

    @Volatile
    private var lastArrivalMs = -1L

    /** A dropped access unit (outside a resync's own IDR wait). */
    @Synchronized
    fun onDrop() {
        if (!waiting) {
            waiting = true
            holding = mode == LossGuardMode.GUARD
            waitStartMs = clockMs()
            episodeDrops = 0L
            episodes.incrementAndGet()
            if (mode == LossGuardMode.GUARD) {
                pending.set(KeyframeRequestPacket.encode(seq++, delivered.get(), 1L))
            }
        }
        episodeDrops++
        lastArrivalMs = clockMs()                    // B29: the link still delivers
    }

    /** A complete access unit about to be queued: true = queue it (today), false = hold it (the freeze). */
    @Synchronized
    fun deliver(isIdr: Boolean): Boolean {
        if (!waiting) {
            delivered.incrementAndGet()
            return true
        }
        val waited = clockMs() - waitStartMs
        if (isIdr) {
            if (holding) maxHoldObservedMs.accumulateAndGet(waited) { a, b -> maxOf(a, b) }   // B29
            waiting = false
            holding = false
            maxWaitObservedMs.accumulateAndGet(waited) { a, b -> maxOf(a, b) }
            delivered.incrementAndGet()
            return true
        }
        framesAfterDroppedReference.incrementAndGet()
        if (holding && waited >= maxWaitMs) {
            holding = false
            timeouts.incrementAndGet()
            maxWaitObservedMs.accumulateAndGet(waited) { a, b -> maxOf(a, b) }
            maxHoldObservedMs.accumulateAndGet(waited) { a, b -> maxOf(a, b) }   // B29
        }
        if (holding) {
            framesHeld.incrementAndGet()
            lastArrivalMs = clockMs()                // B29: a held frame: the link still delivers
            return false
        }
        delivered.incrementAndGet()
        return true
    }

    /** The controller sender's tick: the episode's one request, once. */
    fun takeRequest(): ByteArray? =
        pending.getAndSet(null)?.also { requestsSent.incrementAndGet() }

    /** B29: the controller loop's tick: the cap on the hold's own clock (no frame needed), then the request. */
    fun tick(): ByteArray? {
        synchronized(this) {
            if (holding) {
                val waited = clockMs() - waitStartMs
                if (waited >= maxWaitMs) {
                    holding = false
                    timeouts.incrementAndGet()
                    maxWaitObservedMs.accumulateAndGet(waited) { a, b -> maxOf(a, b) }
                    maxHoldObservedMs.accumulateAndGet(waited) { a, b -> maxOf(a, b) }
                }
            }
        }
        return takeRequest()
    }

    /** B29: while holding, the time since the last access unit seen (held or dropped); -1 when not holding. */
    fun holdingAgeMs(): Long {
        if (!holding) return -1L
        val last = lastArrivalMs
        return if (last < 0L) -1L else (clockMs() - last).coerceAtLeast(0L)
    }

    /** The heartbeat's query fragment. */
    fun query(): String =
        "&frames_after_dropped_reference=${framesAfterDroppedReference.get()}" +
            "&loss_guard_episodes=${episodes.get()}" +
            "&loss_guard_frames_held=${framesHeld.get()}"
}
