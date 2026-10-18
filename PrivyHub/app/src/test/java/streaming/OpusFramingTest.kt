package com.safeiot.privyhub.streaming

import java.nio.ByteOrder
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * CL-B4: the client's Opus framing (csd bytes, the copy offset, the split)
 * and the in-order release ([OpusReorder]), including the host's send
 * pattern (`companion/audio_codec.py` `run_opus_sender`: original n, then the
 * copy of n - k) under seeded independent loss.
 */
class OpusFramingTest {

    private fun hex(b: ByteArray) = b.joinToString("") { "%02x".format(it.toInt() and 0xff) }

    @Test
    fun opusHeadIsRfc7845() {
        // "OpusHead", v1, 2 ch, pre-skip 120, 48000 Hz, gain 0, family 0
        assertEquals("4f7075734865616401027800" + "80bb0000" + "0000" + "00", hex(OpusFraming.opusHead()))
        assertEquals(19, OpusFraming.opusHead().size)
    }

    @Test
    fun csdDurations() {
        assertEquals(2_500_000L, OpusFraming.preSkipNs())
        assertEquals("a025260000000000", hex(OpusFraming.nsBuffer(2_500_000L, ByteOrder.LITTLE_ENDIAN)))
        assertEquals("0000000004c4b400", hex(OpusFraming.nsBuffer(80_000_000L, ByteOrder.BIG_ENDIAN)))
    }

    @Test
    fun copyOffsetMatchesTheHost() {
        // audio_codec.copy_offset_packets(4, frame): 5 ms -> 4, 10 -> 2, 20 -> 1; redundancy off -> 0
        assertEquals(4, OpusFraming.copyOffsetFrames(2, 4, 240))
        assertEquals(2, OpusFraming.copyOffsetFrames(2, 4, 480))
        assertEquals(1, OpusFraming.copyOffsetFrames(2, 4, 960))
        assertEquals(1, OpusFraming.copyOffsetFrames(2, 1, 960))
        assertEquals(0, OpusFraming.copyOffsetFrames(1, 4, 480))
    }

    @Test
    fun splitIntoQueuePackets() {
        val frame = ByteArray(1920) { (it % 251).toByte() }
        val parts = OpusFraming.split(frame)
        assertEquals(2, parts.size)
        assertArrayEquals(frame.copyOfRange(0, 960), parts[0])
        assertArrayEquals(frame.copyOfRange(960, 1920), parts[1])
        // the pre-skip's first output: 360 frames, left-padded with 120 frames of silence
        val first = ByteArray(1440) { 7 }
        val padded = OpusFraming.split(first)
        assertEquals(2, padded.size)
        assertTrue(padded[0].copyOfRange(0, 480).all { it.toInt() == 0 })
        assertTrue(padded[0].copyOfRange(480, 960).all { it.toInt() == 7 })
        assertTrue(padded[1].all { it.toInt() == 7 })
        assertEquals(0, OpusFraming.split(ByteArray(0)).size)
        assertEquals(1, OpusFraming.split(ByteArray(4000), 960).size)
    }

    private class Sink {
        val order = mutableListOf<Int>()
        val lost = mutableListOf<Int>()
        val emit: (Int, ByteArray?) -> Unit = { seq, p -> order += seq; if (p == null) lost += seq }
    }

    private fun p(seq: Int) = byteArrayOf(seq.toByte())

    @Test
    fun inOrderIsReleasedAtOnce() {
        val r = OpusReorder()
        val s = Sink()
        for (q in 0..9) assertEquals(OpusReorder.Kind.IN_ORDER, r.offer(q, p(q), 2, s.emit).kind)
        assertEquals((0..9).toList(), s.order)
        assertEquals(0, r.held)
    }

    @Test
    fun aMissingFrameWaitsForItsCopy() {
        val r = OpusReorder()
        val s = Sink()
        for (q in 0..2) r.offer(q, p(q), 2, s.emit)
        assertEquals(1, r.offer(4, p(4), 2, s.emit).newGap)
        r.offer(5, p(5), 2, s.emit)
        assertEquals(listOf(0, 1, 2), s.order)          // 4 and 5 held for 3
        assertEquals(OpusReorder.Kind.RECOVERED, r.offer(3, p(3), 2, s.emit).kind)
        assertEquals(listOf(0, 1, 2, 3, 4, 5), s.order)
        assertTrue(s.lost.isEmpty())
        assertEquals(3, r.maxHeld)
    }

    @Test
    fun aFrameWhoseCopyIsAlsoLostIsGivenUp() {
        val r = OpusReorder()
        val s = Sink()
        for (q in listOf(0, 1, 2, 4, 5)) r.offer(q, p(q), 2, s.emit)
        r.offer(6, p(6), 2, s.emit)                      // 6 - 3 > k: 3 cannot come any more
        assertEquals(listOf(0, 1, 2, 3, 4, 5, 6), s.order)
        assertEquals(listOf(3), s.lost)
        assertEquals(OpusReorder.Kind.LATE, r.offer(3, p(3), 2, s.emit).kind)
    }

    @Test
    fun redundancyOffGivesUpAtOnce() {
        val r = OpusReorder()
        val s = Sink()
        r.offer(0, p(0), 0, s.emit)
        r.offer(2, p(2), 0, s.emit)
        assertEquals(listOf(0, 1, 2), s.order)
        assertEquals(listOf(1), s.lost)
    }

    @Test
    fun theSequenceWraps() {
        val r = OpusReorder()
        val s = Sink()
        for (q in listOf(65534, 65535, 0, 1)) r.offer(q, p(q), 2, s.emit)
        assertEquals(listOf(65534, 65535, 0, 1), s.order)
    }

    @Test
    fun anOutageIsAJump() {
        val r = OpusReorder()
        val s = Sink()
        var skipped = -1
        r.offer(0, p(0), 2, s.emit)
        val o = r.offer(200, p(200), 2, s.emit) { skipped = it }
        assertEquals(OpusReorder.Kind.JUMP, o.kind)
        assertEquals(199, skipped)
        assertEquals(listOf(0, 200), s.order)
    }

    /** The host's datagram order, each datagram dropped with probability [loss]; the client de-duplicates first. */
    private fun simulate(loss: Double, seed: Long, k: Int, n: Int = 20_000): Triple<Sink, Int, OpusReorder> {
        val rnd = java.util.Random(seed)
        val wire = mutableListOf<Int>()
        for (q in 0 until n) {
            wire += q
            if (q - k >= 0) wire += q - k
        }
        val received = wire.filter { rnd.nextDouble() >= loss }
        val r = OpusReorder()
        val s = Sink()
        val seen = IntArray(64) { -1 }
        for (q16 in received.map { it and 0xffff }) {
            if (seen[q16 and 63] == q16) continue
            seen[q16 and 63] = q16
            r.offer(q16, p(q16), k, s.emit)
        }
        r.flush(s.emit)
        val got = received.toHashSet()
        val bothLost = (s.order[0] until n - k).count { q -> q !in got }
        return Triple(s, bothLost, r)
    }

    @Test
    fun theHostsPatternUnderLoss() {
        for ((loss, seed) in listOf(0.01 to 1L, 0.05 to 2L, 0.2 to 3L)) {
            val (s, bothLost, r) = simulate(loss, seed, 2)
            // every sequence released once, in order (mod 2^16)
            val expected = (0 until s.order.size).map { (s.order[0] + it) and 0xffff }
            assertEquals("order at $loss", expected, s.order)
            // a frame is given up only if neither datagram of it arrived
            val lostInRange = s.lost.count { it < 20_000 - 2 }
            assertEquals("lost at $loss", bothLost, lostInRange)
            assertTrue(r.maxHeld <= 2 + 2)
        }
    }

    @Test
    fun aGivenUpFrameIsNullAndOthersCarryTheirPayload() {
        val r = OpusReorder()
        val got = mutableMapOf<Int, ByteArray?>()
        val emit: (Int, ByteArray?) -> Unit = { q, b -> got[q] = b }
        for (q in listOf(0, 2, 3, 4)) r.offer(q, p(q), 2, emit)
        assertNull(got[1])
        assertArrayEquals(p(4), got[4])
    }
}
