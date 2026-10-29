package com.safeiot.privyhub.streaming

import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.Collections
import kotlin.random.Random
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B29: a loss-guard hold with frames still arriving is not a stall (the stall monitor decides on the time since the
 * last frame while the guard holds), and the guard's cap runs on the hold's own clock (`tick`, the controller loop).
 * The guard on a fake clock beside B7's `StallMonitor` at its default 150 ms; B10's receiver harness on loopback; and
 * today's monitor (the predecessor's `tick`, copied below) for the no-guard case, byte for byte.
 */
class GuardQuietStallTest {

    private fun age(d: ByteArray): Long =
        ByteBuffer.wrap(d).order(ByteOrder.LITTLE_ENDIAN).getInt(20).toLong() and 0xFFFF_FFFFL

    private fun kind(d: ByteArray): Int = d[4].toInt()

    /** One stream on a shared clock: the guard, the monitor ticking every 8 ms, the output's last frame. */
    private class Rig(threshold: Long = StallSignalFlag.DEFAULT_MS) {
        var now = 10_000L
        val guard = LossGuard(LossGuardMode.GUARD, clockMs = { now })
        val monitor = StallMonitor(threshold)
        var lastOutputMs = now
        var rendered = 100L
        val sent = mutableListOf<ByteArray>()

        fun inputs() = StallInputs(now - lastOutputMs, rendered, inGate = false, released = true,
            holdingAgeMs = guard.holdingAgeMs())

        fun advance(ms: Long, frameEveryMs: Long? = null, idrAt: Long? = null) {
            val end = now + ms
            var nextFrame = if (frameEveryMs != null) now + frameEveryMs else Long.MAX_VALUE
            while (now < end) {
                now += 1
                if (now >= nextFrame) {
                    val isIdr = idrAt != null && now >= idrAt
                    if (guard.deliver(isIdr)) {
                        lastOutputMs = now
                        rendered++
                    }
                    nextFrame += frameEveryMs!!
                }
                if (now % 8L == 0L) {
                    guard.tick()
                    monitor.tick(now, inputs())?.let { sent.add(it) }
                }
            }
        }
    }

    @Test
    fun a450MsHoldWithFramesArrivingSendsNoStall() {
        val r = Rig()
        r.advance(100, frameEveryMs = 16)
        r.guard.onDrop()
        r.advance(450, frameEveryMs = 16)                    // every frame held: the output 450 ms old
        assertTrue(r.inputs().outputAgeMs >= 440)
        assertTrue(r.guard.framesHeld.get() >= 27)
        assertEquals(emptyList<Int>(), r.sent.map { kind(it) })
        r.advance(20, frameEveryMs = 16, idrAt = r.now + 1)   // the IDR ends it
        assertEquals(-1L, r.guard.holdingAgeMs())
        assertEquals(0, r.sent.size)
        assertEquals(0L, r.guard.timeouts.get())
    }

    @Test
    fun aRealStallWithNoHoldIsTodays() {
        val r = Rig()
        r.advance(100, frameEveryMs = 16)
        r.advance(450)                                       // no frame at all, no guard episode
        assertTrue(r.sent.isNotEmpty())
        assertEquals(StallPacket.KIND_STALL, kind(r.sent.first()))
        assertTrue(age(r.sent.first()) in 150L..160L)
        assertTrue(age(r.sent.last()) >= 400L)               // the host's 400 is reached as today
    }

    @Test
    fun aHoldThenTheFramesStopIsAStallFromTheLastFrame() {
        val r = Rig()
        r.advance(100, frameEveryMs = 16)
        r.guard.onDrop()
        r.advance(200, frameEveryMs = 16)                    // held, no stall
        assertEquals(0, r.sent.size)
        val lastFrame = r.now
        r.advance(300)                                       // the link stops inside the hold
        assertTrue(r.sent.isNotEmpty())
        val first = r.sent.first()
        assertEquals(StallPacket.KIND_STALL, kind(first))
        assertTrue("age ${age(first)}", age(first) in 150L..175L)   // from the last frame, not the hold's start
        assertTrue(r.inputs().outputAgeMs - (r.now - lastFrame) >= 190L)
    }

    @Test
    fun theCapRunsOnTheHoldsOwnClock() {
        var now = 0L
        val g = LossGuard(LossGuardMode.GUARD, clockMs = { now })
        g.onDrop()
        now = 584
        assertEquals(false, g.deliver(false))                // held
        for (t in 592L..608L step 8L) {                      // no frame after 584: the controller loop's ticks
            now = t
            g.tick()
        }
        assertEquals(1L, g.timeouts.get())
        assertTrue(g.maxHoldObservedMs.get() in 600L..608L)
        assertEquals(-1L, g.holdingAgeMs())
        now = 685
        assertTrue(g.deliver(false))                         // the next frame passes (the cap's purpose)
        now = 700
        assertTrue(g.deliver(true))
        assertEquals(700L, g.maxWaitObservedMs.get())        // the episode: drop -> IDR, as B10 defines it
        assertTrue(g.maxHoldObservedMs.get() <= 608L)        // the hold: its own clock
        assertEquals(1L, g.timeouts.get())
    }

    @Test
    fun aHoldEndedByItsIdrRecordsItsLength() {
        var now = 0L
        val g = LossGuard(LossGuardMode.GUARD, clockMs = { now })
        g.onDrop()
        now = 120; g.deliver(false)
        now = 233; assertTrue(g.deliver(true))
        assertEquals(233L, g.maxHoldObservedMs.get())
        assertEquals(233L, g.maxWaitObservedMs.get())
        assertEquals(0L, g.timeouts.get())
        val c = LossGuard(LossGuardMode.COUNT, clockMs = { now })   // count holds nothing
        c.onDrop(); now = 400; c.deliver(true)
        assertEquals(0L, c.maxHoldObservedMs.get())
        assertEquals(-1L, c.holdingAgeMs())
    }

    @Test
    fun withNoGuardTheMonitorIsTodaysByteForByte() {
        val rnd = Random(29)
        val now = StallMonitor(150)
        val today = TodayMonitor(150)
        var t = 1_000L
        repeat(5_000) {
            t += 8
            val inp = StallInputs(
                outputAgeMs = if (rnd.nextInt(50) == 0) -1L else rnd.nextLong(0, 900),
                renderedFrames = rnd.nextLong(0, 1_000_000),
                inGate = rnd.nextInt(40) == 0,
                released = rnd.nextInt(30) != 0,
            )                                                // holdingAgeMs: the default -1 (no guard)
            if (rnd.nextInt(2_000) == 0) { now.requestBye(); today.requestBye() }
            val a = now.tick(t, inp)
            val b = today.tick(t, inp)
            if (a == null || b == null) assertEquals(a, b) else assertArrayEquals(b, a)
        }
        assertEquals(today.stallsSent, now.stallsSent)
        assertEquals(today.endsSent, now.endsSent)
    }

    @Test
    fun theReceiverHarnessIsB10s() {
        val g = LossGuard(LossGuardMode.GUARD)
        assertEquals(listOf('I', 'P', 'P', 'I', 'P'), run(g))
        assertEquals(3L, g.framesHeld.get())
        assertNotNull(g.tick())                              // the episode's request, through the new tick
        assertNull(g.tick())
    }

    /** The predecessor's `StallMonitor.tick` (HEAD 42a2ab6), copied: today's decisions. */
    private class TodayMonitor(val thresholdMs: Long, private val intervalMs: Long = 50L) {
        private var stalled = false
        private var lastSentMs = 0L
        private var seq = 0
        var stallsSent = 0L
        var endsSent = 0L
        private var byesDue = 0

        fun requestBye() {
            byesDue = StallMonitor.BYE_COUNT
        }

        fun tick(nowMs: Long, inp: StallInputs): ByteArray? {
            if (byesDue > 0) {
                byesDue--
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
