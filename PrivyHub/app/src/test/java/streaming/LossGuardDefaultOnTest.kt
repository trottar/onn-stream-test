package com.safeiot.privyhub.streaming

import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.nio.ByteBuffer
import java.util.Collections
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

/**
 * B27: `debug.privyhub.loss_guard` absent / empty / junk = ON (the guard), `0` off (B10's absent, byte for byte),
 * `count` as before. The activity builds the guard as `LossGuardFlag.fromSystem()?.let { LossGuard(it) }`; [built]
 * is that line on a given value. The stream is B10's: I P P [lost] P P P P I P through the real RtpH264Receiver on
 * loopback with a fake decoder.
 */
class LossGuardDefaultOnTest {

    private fun built(property: String?): LossGuard? = LossGuardFlag.parse(property)?.let { LossGuard(it) }

    /** B10's parse, as it was (HEAD 2cd392c): the old absent is its `parse(null)`. */
    private fun b10Parse(value: String?): LossGuardMode? =
        when (value?.trim()) {
            "1" -> LossGuardMode.GUARD
            "count" -> LossGuardMode.COUNT
            else -> null
        }

    @Test
    fun theTable() {
        for (on in listOf(null, "", " ", "1", " 1 ", "on", "true", "2", "yes", "guard")) {
            assertEquals("[$on]", LossGuardMode.GUARD, LossGuardFlag.parse(on))
        }
        for (off in listOf("0", " 0 ", "0\n")) assertNull("[$off]", LossGuardFlag.parse(off))
        assertEquals(LossGuardMode.COUNT, LossGuardFlag.parse("count"))
        assertEquals(LossGuardMode.GUARD, LossGuardFlag.fromSystem())       // off-device the read fails: on
    }

    @Test
    fun zeroIsTodaysAbsent() {
        assertEquals(b10Parse(null), LossGuardFlag.parse("0"))              // both null: no object
        assertNull(built("0"))                                              // no datagram, no report or heartbeat key
        assertEquals(b10Parse("count"), LossGuardFlag.parse("count"))
        assertEquals(b10Parse("1"), LossGuardFlag.parse("1"))
        val today = run(null)
        assertEquals(listOf('I', 'P', 'P', 'P', 'P', 'P', 'I', 'P'), today)
        assertEquals(today, run(built("0")))
    }

    @Test
    fun absentIsTheGuard() {
        val g = built(null)
        assertNotNull(g)
        assertEquals(LossGuardMode.GUARD, g!!.mode)
        assertEquals(listOf('I', 'P', 'P', 'I', 'P'), run(g))
        assertEquals(3L, g.framesAfterDroppedReference.get())
        assertEquals(3L, g.framesHeld.get())
        assertEquals(1L, g.episodes.get())
        assertEquals(0L, g.timeouts.get())
        assertNotNull(g.takeRequest())                                     // one PHK1 per episode
        assertNull(g.takeRequest())
        assertEquals("&frames_after_dropped_reference=3&loss_guard_episodes=1&loss_guard_frames_held=3", g.query())
    }

    @Test
    fun countIsAsBefore() {
        val g = built("count")!!
        assertEquals(listOf('I', 'P', 'P', 'P', 'P', 'P', 'I', 'P'), run(g))
        assertEquals(3L, g.framesAfterDroppedReference.get())
        assertEquals(0L, g.framesHeld.get())
        assertNull(g.takeRequest())
    }

    // --- B10's harness (LossGuardTest's, copied: it is private there) ---------------------------------------------

    private class Wire(val port: Int) {
        private val tx = DatagramSocket()
        private var seq = 100
        private var ts = 90_000L

        fun au(idr: Boolean, skip: Boolean = false) {
            val nal = byteArrayOf(if (idr) 0x65 else 0x41, 0x11, 0x22, 0x33, 0x44)
            val p = ByteBuffer.allocate(12 + nal.size)
            p.put(0x80.toByte()).put((0x80 or 96).toByte()).putShort(seq.toShort()).putInt(ts.toInt()).putInt(0x1234)
            p.put(nal)
            seq = (seq + 1) and 0xffff
            ts += 1500L
            if (!skip) {
                tx.send(DatagramPacket(p.array(), p.capacity(), InetAddress.getLoopbackAddress(), port))
            }
            Thread.sleep(3)
        }

        fun close() = tx.close()
    }

    private fun freePort(): Int = DatagramSocket(0).use { it.localPort }

    private fun run(guard: LossGuard?): List<Char> {
        val queued = Collections.synchronizedList(mutableListOf<Char>())
        val port = freePort()
        val rx = RtpH264Receiver(
            port = port,
            onParameterSets = { _, _ -> },
            onAccessUnit = { au, _ -> queued.add(if (au.any { it == 0x65.toByte() }) 'I' else 'P') },
        )
        rx.start()
        rx.lossGuard = guard
        Thread.sleep(150)
        val w = Wire(port)
        try {
            w.au(true); w.au(false); w.au(false)
            w.au(false, skip = true)
            repeat(4) { w.au(false) }
            w.au(true); w.au(false)
            Thread.sleep(200)
        } finally {
            w.close()
            rx.stop()
        }
        return queued.toList()
    }
}
