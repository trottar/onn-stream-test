package com.safeiot.privyhub.streaming

import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * CL-B4: the pure parts of the client's Opus path (G4-W2's PHA1 version 2),
 * so the JVM unit tests check them without Android: the decoder's csd
 * buffers, the copy offset, the split of a decoded frame into the queue's
 * 5-ms packets, and the in-order release that waits for a redundant copy.
 *
 * Host contract: `companion/audio_codec.py` and
 * `docs/memory/evidence/G4_W2_OPUS_AUDIO_PATH_2026-10-18.md` §1, §5.1.
 */
object OpusFraming {
    const val PHA_VERSION_OPUS = 2
    const val SAMPLE_RATE = 48_000
    const val CHANNELS = 2
    const val PRE_SKIP_SAMPLES = 120          // the host encoder's lookahead (RESTRICTED_LOWDELAY)
    const val SEEK_PRE_ROLL_NS = 80_000_000L
    const val QUEUE_PACKET_FRAMES = 240       // the PCM queue's 5-ms packet
    const val QUEUE_PACKET_BYTES = QUEUE_PACKET_FRAMES * CHANNELS * 2
    const val MAX_PAYLOAD_BYTES = 1500
    const val PCM_PACKET_MS = 5
    val FRAME_SAMPLES = setOf(240, 480, 960)  // 5 / 10 / 20 ms, the host's accepted frames

    /** csd-0: the OpusHead (RFC 7845 §5.1), mapping family 0. */
    fun opusHead(channels: Int = CHANNELS, preSkip: Int = PRE_SKIP_SAMPLES, rate: Int = SAMPLE_RATE): ByteArray =
        ByteBuffer.allocate(19).order(ByteOrder.LITTLE_ENDIAN).apply {
            put("OpusHead".toByteArray(Charsets.US_ASCII))
            put(1)                      // version
            put(channels.toByte())
            putShort(preSkip.toShort())
            putInt(rate)
            putShort(0)                 // output gain
            put(0)                      // mapping family
        }.array()

    /** csd-1 / csd-2: a duration in ns as an 8-byte long, in the given order (the device's native one). */
    fun nsBuffer(ns: Long, order: ByteOrder = ByteOrder.nativeOrder()): ByteArray =
        ByteBuffer.allocate(8).order(order).putLong(ns).array()

    fun preSkipNs(preSkip: Int = PRE_SKIP_SAMPLES): Long = preSkip * 1_000_000_000L / SAMPLE_RATE

    /** The host's `copy_offset_packets`: the copy the same ~20 ms behind; 0 with redundancy off. */
    fun copyOffsetFrames(copies: Int, offsetPcmPackets: Int, frameSamples: Int): Int {
        if (copies < 2) return 0
        val frameMs = frameSamples * 1000 / SAMPLE_RATE
        return maxOf(1, Math.rint(offsetPcmPackets * PCM_PACKET_MS.toDouble() / frameMs).toInt())
    }

    /**
     * A decoded output as queue packets of [QUEUE_PACKET_BYTES]. An output that
     * is not a whole number of them (the pre-skip's first, 360 frames) is
     * left-padded with silence, so the packets after it stay aligned.
     */
    fun split(pcm: ByteArray, length: Int = pcm.size): List<ByteArray> {
        if (length <= 0) return emptyList()
        val usable = length - length % 4
        val pad = (QUEUE_PACKET_BYTES - usable % QUEUE_PACKET_BYTES) % QUEUE_PACKET_BYTES
        val whole = ByteArray(pad + usable)
        System.arraycopy(pcm, 0, whole, pad, usable)
        return (0 until whole.size / QUEUE_PACKET_BYTES).map {
            whole.copyOfRange(it * QUEUE_PACKET_BYTES, (it + 1) * QUEUE_PACKET_BYTES)
        }
    }
}

/**
 * CL-B4: release Opus frames strictly in sequence order (the decoder is
 * stateful). A missing sequence holds the frames after it until its copy can
 * no longer come: a frame more than `k` sequences ahead of it has arrived
 * (the host sends the copy of n right after the original of n + k). Then it
 * is released as lost. Receive thread only.
 */
class OpusReorder(private val window: Int = 64) {
    enum class Kind { IN_ORDER, RECOVERED, LATE, DUPLICATE, JUMP }

    data class Offer(val kind: Kind, val newGap: Int)

    private val slots = arrayOfNulls<ByteArray>(window)
    private val slotSeq = IntArray(window) { -1 }

    var next = -1
        private set
    var highest = -1
        private set
    var held = 0
        private set
    var maxHeld = 0
        private set

    private fun ahead(a: Int, b: Int): Int = (a - b) and 0xffff   // how far a is ahead of b

    /**
     * Offer one de-duplicated frame; [emit] gets (sequence, payload) in order,
     * payload null for a frame given up as lost. A JUMP (a gap of a window or
     * more, an outage) first releases what is held, then [onJump] gets the
     * number of sequences skipped, and the frame starts a new run.
     */
    fun offer(seq: Int, payload: ByteArray, k: Int, emit: (Int, ByteArray?) -> Unit, onJump: (Int) -> Unit = {}): Offer {
        if (next < 0) {
            next = seq
            highest = seq
            store(seq, payload)
            drain(k, emit)
            return Offer(Kind.IN_ORDER, 0)
        }
        val behindNext = ahead(seq, next)
        if (behindNext > 32767) return Offer(Kind.LATE, 0)
        if (behindNext >= window) {
            flush(emit)
            val skipped = ahead(seq, highest) - 1
            onJump(maxOf(0, skipped))
            next = seq
            highest = seq
            store(seq, payload)
            drain(k, emit)
            return Offer(Kind.JUMP, maxOf(0, skipped))
        }
        val idx = seq % window
        if (slotSeq[idx] == seq) return Offer(Kind.DUPLICATE, 0)
        val pastHighest = ahead(seq, highest)
        val offer =
            if (pastHighest in 1..32767) {
                val gap = pastHighest - 1
                highest = seq
                Offer(Kind.IN_ORDER, gap)
            } else {
                Offer(Kind.RECOVERED, 0)
            }
        store(seq, payload)
        drain(k, emit)
        return offer
    }

    private fun store(seq: Int, payload: ByteArray) {
        val idx = seq % window
        slots[idx] = payload
        slotSeq[idx] = seq
        held += 1
        if (held > maxHeld) maxHeld = held
    }

    private fun drain(k: Int, emit: (Int, ByteArray?) -> Unit) {
        while (true) {
            val distance = ahead(highest, next)
            if (distance > 32767) return               // next is past highest: nothing held
            val idx = next % window
            if (slotSeq[idx] == next) {
                val p = slots[idx]
                slots[idx] = null
                slotSeq[idx] = -1
                held -= 1
                emit(next, p)
            } else if (distance > k) {
                emit(next, null)                       // its copy can no longer come
            } else {
                return
            }
            next = (next + 1) and 0xffff
        }
    }

    /** Release everything up to [highest]: held frames in order, the missing ones as lost. */
    fun flush(emit: (Int, ByteArray?) -> Unit) {
        if (next < 0) return
        drain(-1, emit)
    }
}
