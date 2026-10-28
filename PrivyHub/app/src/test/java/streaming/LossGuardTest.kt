package com.safeiot.privyhub.streaming

import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.Collections
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B10: the loss guard. The flag (absent = off), the 24-byte keyframe request,
 * the guard on a fake clock, and the real RtpH264Receiver on loopback with a
 * fake decoder (the list of access units it was asked to queue): a dropped
 * access unit -> no non-IDR queued -> the IDR queued -> resumed; `count`
 * queues everything and counts the same frames; null = today.
 */
class LossGuardTest {

    @Test
    fun flagTable() {
        assertEquals(LossGuardMode.GUARD, LossGuardFlag.parse("1"))
        assertEquals(LossGuardMode.COUNT, LossGuardFlag.parse(" count "))
        // B27: absent / empty / junk are on, `0` off; off-device the read fails, so on
        for (absent in listOf(null, "", "on", "guard", "2")) {
            assertEquals(absent, LossGuardMode.GUARD, LossGuardFlag.parse(absent))
        }
        assertNull(LossGuardFlag.parse("0"))
        assertEquals(LossGuardMode.GUARD, LossGuardFlag.fromSystem())
    }

    @Test
    fun requestEncoding() {
        val d = KeyframeRequestPacket.encode(7, 1234L, 1L)
        assertEquals(24, d.size)
        val b = ByteBuffer.wrap(d).order(ByteOrder.LITTLE_ENDIAN)
        assertEquals("PHK1", String(d, 0, 4))
        assertEquals(1, d[4].toInt())
        assertEquals(7, b.getInt(8))
        assertEquals(1234L, b.getLong(12))
        assertEquals(1, b.getInt(20))
    }

    @Test
    fun guardHoldsUntilTheIdrAndAsksOnce() {
        var now = 1_000L
        val g = LossGuard(LossGuardMode.GUARD, clockMs = { now })
        assertTrue(g.deliver(true))
        assertTrue(g.deliver(false))
        g.onDrop()
        g.onDrop()                                   // the same episode
        assertNotNull(g.takeRequest())
        assertNull(g.takeRequest())                  // one per episode
        repeat(5) { now += 16; assertEquals(false, g.deliver(false)) }
        now += 16
        assertTrue(g.deliver(true))                  // the IDR ends it
        assertTrue(g.deliver(false))
        assertEquals(5L, g.framesAfterDroppedReference.get())
        assertEquals(5L, g.framesHeld.get())
        assertEquals(1L, g.episodes.get())
        assertEquals(1L, g.requestsSent.get())
        assertEquals(96L, g.maxWaitObservedMs.get())
        assertEquals(
            "&frames_after_dropped_reference=5&loss_guard_episodes=1&loss_guard_frames_held=5",
            g.query()
        )
        g.onDrop()
        assertNotNull(g.takeRequest())               // a new episode asks again
    }

    @Test
    fun countHoldsNothingAndSendsNothing() {
        val g = LossGuard(LossGuardMode.COUNT)
        g.onDrop()
        repeat(7) { assertTrue(g.deliver(false)) }
        assertTrue(g.deliver(true))
        assertEquals(7L, g.framesAfterDroppedReference.get())
        assertEquals(0L, g.framesHeld.get())
        assertNull(g.takeRequest())
    }

    @Test
    fun theFreezeIsCappedAt600Ms() {
        var now = 0L
        val g = LossGuard(LossGuardMode.GUARD, clockMs = { now })
        g.onDrop()
        now = 584
        assertEquals(false, g.deliver(false))
        now = 600
        assertTrue(g.deliver(false))                 // the IDRs were lost too: frames pass as today
        assertTrue(g.deliver(false))
        assertEquals(3L, g.framesAfterDroppedReference.get())
        assertEquals(1L, g.framesHeld.get())
        assertEquals(1L, g.timeouts.get())
        now = 640
        assertTrue(g.deliver(true))
        assertEquals(640L, g.maxWaitObservedMs.get())
    }

    // --- the real receiver on loopback, a fake decoder ---------------------------------------------------------

    private class Wire(val port: Int) {
        private val tx = DatagramSocket()
        private var seq = 100
        private var ts = 90_000L

        /** One access unit = one RTP packet (a single NAL, marker set). `skip` = the packet is lost. */
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

    /** I P P [lost] P P P P I P: returns the kinds the fake decoder was asked to queue ('I' / 'P'). */
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

    @Test
    fun receiverWithoutAGuardIsToday() {
        // the AU after the loss carries the gap and is dropped; the 3 after it are queued (decoded from a lost reference)
        assertEquals(listOf('I', 'P', 'P', 'P', 'P', 'P', 'I', 'P'), run(null))
    }

    @Test
    fun receiverWithTheGuardQueuesNothingUntilTheIdr() {
        val g = LossGuard(LossGuardMode.GUARD)
        assertEquals(listOf('I', 'P', 'P', 'I', 'P'), run(g))
        assertEquals(3L, g.framesAfterDroppedReference.get())
        assertEquals(3L, g.framesHeld.get())
        assertEquals(1L, g.episodes.get())
        assertNotNull(g.takeRequest())
    }

    @Test
    fun receiverCountingIsTodayWithTheNumber() {
        val g = LossGuard(LossGuardMode.COUNT)
        assertEquals(listOf('I', 'P', 'P', 'P', 'P', 'P', 'I', 'P'), run(g))
        assertEquals(3L, g.framesAfterDroppedReference.get())
        assertNull(g.takeRequest())
    }
}
