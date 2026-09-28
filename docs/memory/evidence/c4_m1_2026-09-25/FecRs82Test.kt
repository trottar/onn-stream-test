package com.safeiot.privyhub.streaming

import java.security.MessageDigest
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

/**
 * C4-M1: the client's xor8_2 decoder. The vector is the Python encoder's
 * (companion/native_fec_rs.py) for the same payloads, so the two
 * implementations are checked against each other.
 */
class FecRs82Test {
    private val lengths = listOf(1188, 1000, 17, 512, 1188, 3, 900, 64)
    private val payloads = lengths.mapIndexed { i, n ->
        ByteArray(n) { k -> ((i * 37 + k * 11 + 5) % 256).toByte() }
    }
    private val maxLen = lengths.max()

    private fun pParity(): ByteArray {
        val acc = ByteArray(maxLen)
        for (p in payloads) for (k in p.indices) acc[k] = (acc[k].toInt() xor p[k].toInt()).toByte()
        return acc
    }

    private fun lengthXor(): Int = lengths.fold(0) { a, n -> a xor n }

    private fun sha256(b: ByteArray): String =
        MessageDigest.getInstance("SHA-256").digest(b).joinToString("") { "%02x".format(it) }

    @Test
    fun encoderMatchesThePythonRelay() {
        // Rule: the Q parity and its length field equal the relay's (Python) bytes.
        val q = FecRs82.qParity(payloads, maxLen)
        assertEquals("be5e52bbe805f19baabf38256748d5e53036f021a7d4fc1765b62803eb85b894", sha256(q))
        assertEquals(37570, FecRs82.lengthQ(lengths))
    }

    @Test
    fun everySingleLossRecoversFromQWhenPIsLost() {
        // Rule: one packet and its P lost -> Q alone recovers it, at every position.
        val q = FecRs82.qParity(payloads, maxLen)
        val lq = FecRs82.lengthQ(lengths)
        for (x in payloads.indices) {
            val known = payloads.indices.filter { it != x }
                .map { FecRs82.Known(it, payloads[it], 0, payloads[it].size) }
            val (out, len) = FecRs82.recoverOneFromQ(q, lq, known, x)
            assertEquals(lengths[x], len)
            assertArrayEquals(payloads[x], out.copyOf(len))
        }
    }

    @Test
    fun everyTwoLossPatternRecovers() {
        // Rule: any two packets lost (consecutive or not) -> P and Q recover both.
        val p = pParity()
        val q = FecRs82.qParity(payloads, maxLen)
        val lq = FecRs82.lengthQ(lengths)
        for (x in payloads.indices) for (y in x + 1 until payloads.size) {
            val known = payloads.indices.filter { it != x && it != y }
                .map { FecRs82.Known(it, payloads[it], 0, payloads[it].size) }
            val r = FecRs82.recoverTwo(p, lengthXor(), q, lq, known, x, y)
            assertEquals(lengths[x], r.xLength)
            assertEquals(lengths[y], r.yLength)
            assertArrayEquals(payloads[x], r.x.copyOf(r.xLength))
            assertArrayEquals(payloads[y], r.y.copyOf(r.yLength))
        }
    }

    @Test
    fun knownPacketsMayCarryAnRtpHeader() {
        // Rule: the receiver passes whole RTP packets with a 12-byte offset.
        val p = pParity()
        val q = FecRs82.qParity(payloads, maxLen)
        val known = (2 until payloads.size).map {
            val rtp = ByteArray(12) + payloads[it]
            FecRs82.Known(it, rtp, 12, payloads[it].size)
        }
        val r = FecRs82.recoverTwo(p, lengthXor(), q, FecRs82.lengthQ(lengths), known, 0, 1)
        assertArrayEquals(payloads[0], r.x.copyOf(r.xLength))
        assertArrayEquals(payloads[1], r.y.copyOf(r.yLength))
    }

    @Test
    fun threeLossesAreNotRecovered() {
        // Rule: three missing exceed two parities -- solving for two of them is wrong.
        val p = pParity()
        val q = FecRs82.qParity(payloads, maxLen)
        val known = (3 until payloads.size).map { FecRs82.Known(it, payloads[it], 0, payloads[it].size) }
        val r = FecRs82.recoverTwo(p, lengthXor(), q, FecRs82.lengthQ(lengths), known, 0, 1)
        assertFalse(r.xLength == lengths[0] && r.x.copyOf(maxOf(0, minOf(r.xLength, r.x.size))).contentEquals(payloads[0]))
    }

    @Test
    fun fieldInverses() {
        // Rule: GF(256)/0x11d: every non-zero element has an inverse.
        for (a in 1 until 256) assertEquals(1, FecRs82.mul(a, FecRs82.inv(a)))
    }
}
