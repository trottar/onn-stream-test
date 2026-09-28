package com.safeiot.privyhub.streaming

/**
 * C4-M1: the second parity of the `xor8_2` comparison arm.
 *
 * The relay sends today's XOR parity (`PHF1` version 1) unchanged and, only
 * under `PRIVYHUB_FEC_SCHEME=xor8_2`, a second datagram (`PHF1` version 2)
 * carrying a Reed-Solomon "Q" parity over GF(2^8), polynomial 0x11d,
 * generator 2 (the RAID-6 construction): Q = sum g^i * D_i, payloads
 * zero-padded to the group's longest; its header's length field is the same
 * combination of the payload lengths (high and low byte separately).
 *
 * With P and Q the receiver recovers any two missing packets of a group, or
 * one missing packet whose P was lost. Mirrors `companion/native_fec_rs.py`.
 */
object FecRs82 {
    private const val POLY = 0x11d
    private val EXP = IntArray(512)
    private val LOG = IntArray(256)

    init {
        var x = 1
        for (i in 0 until 255) {
            EXP[i] = x
            LOG[x] = i
            x = x shl 1
            if (x and 0x100 != 0) x = x xor POLY
        }
        for (i in 255 until 512) EXP[i] = EXP[i - 255]
    }

    fun mul(a: Int, b: Int): Int =
        if (a == 0 || b == 0) 0 else EXP[LOG[a] + LOG[b]]

    fun inv(a: Int): Int {
        require(a != 0) { "GF(256) inverse of 0" }
        return EXP[255 - LOG[a]]
    }

    fun genPow(i: Int): Int = EXP[i % 255]

    /** acc ^= c * src over the first `n` bytes of src (acc zero-padded conceptually). */
    private fun mulAccumulate(acc: ByteArray, src: ByteArray, srcOffset: Int, n: Int, c: Int) {
        val limit = minOf(n, acc.size)
        if (c == 1) {
            for (k in 0 until limit) acc[k] = (acc[k].toInt() xor src[srcOffset + k].toInt()).toByte()
            return
        }
        val lc = LOG[c]
        for (k in 0 until limit) {
            val v = src[srcOffset + k].toInt() and 0xff
            if (v != 0) acc[k] = (acc[k].toInt() xor EXP[LOG[v] + lc]).toByte()
        }
    }

    private fun lenMul(g: Int, len: Int): Int =
        (mul(g, (len shr 8) and 0xff) shl 8) or mul(g, len and 0xff)

    /** Encoder, for tests: Q over the payloads, zero-padded to `length`. */
    fun qParity(payloads: List<ByteArray>, length: Int): ByteArray {
        val acc = ByteArray(length)
        payloads.forEachIndexed { i, p -> mulAccumulate(acc, p, 0, p.size, genPow(i)) }
        return acc
    }

    fun lengthQ(lengths: List<Int>): Int {
        var v = 0
        lengths.forEachIndexed { i, n -> v = v xor lenMul(genPow(i), n) }
        return v
    }

    /** A known packet of the group: its index and its RTP payload (offset into data). */
    class Known(val index: Int, val data: ByteArray, val offset: Int, val length: Int)

    /** One missing packet, P lost: D_x = g^-x (Q + sum_{i != x} g^i D_i). */
    fun recoverOneFromQ(
        q: ByteArray, lengthQ: Int, known: List<Known>, missing: Int
    ): Pair<ByteArray, Int> {
        val acc = q.copyOf()
        var lq = lengthQ
        for (k in known) {
            val g = genPow(k.index)
            mulAccumulate(acc, k.data, k.offset, k.length, g)
            lq = lq xor lenMul(g, k.length)
        }
        val gi = inv(genPow(missing))
        val length = lenMul(gi, lq)
        val out = ByteArray(acc.size)
        mulAccumulate(out, acc, 0, acc.size, gi)
        return Pair(out, length)
    }

    /** Two missing packets x != y with P and Q. Returns (payload x, length x, payload y, length y). */
    fun recoverTwo(
        p: ByteArray, lengthXor: Int, q: ByteArray, lengthQ: Int,
        known: List<Known>, x: Int, y: Int
    ): RecoveredPair {
        val n = maxOf(p.size, q.size)
        val pxy = p.copyOf(n)
        val qxy = q.copyOf(n)
        var lp = lengthXor
        var lq = lengthQ
        for (k in known) {
            val g = genPow(k.index)
            mulAccumulate(pxy, k.data, k.offset, k.length, 1)
            mulAccumulate(qxy, k.data, k.offset, k.length, g)
            lp = lp xor k.length
            lq = lq xor lenMul(g, k.length)
        }
        val gx = genPow(x)
        val gy = genPow(y)
        val d = inv(gx xor gy)
        // D_x = (g^y * Pxy + Qxy) / (g^x + g^y); D_y = Pxy + D_x
        val t = qxy.copyOf()
        mulAccumulate(t, pxy, 0, n, gy)
        val dx = ByteArray(n)
        mulAccumulate(dx, t, 0, n, d)
        val dy = pxy.copyOf()
        mulAccumulate(dy, dx, 0, n, 1)
        val lx = lenMul(d, lenMul(gy, lp) xor lq)
        val ly = lp xor lx
        return RecoveredPair(dx, lx, dy, ly)
    }

    class RecoveredPair(val x: ByteArray, val xLength: Int, val y: ByteArray, val yLength: Int)
}
