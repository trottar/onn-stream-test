package com.safeiot.privyhub.streaming

import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.nio.ByteBuffer
import java.util.Collections
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B11: the self-restart guard. A simulated 5-s two-way drop the client
 * restarts from (UX-R4 event 2): session A's real RtpH264Receiver on loopback
 * torn down at the surface's loss, session B's built on the same port at the
 * restart, a fake decoder each, a fake host transport. With the guard: the old
 * report, the stop, then the start; absent: the start only (today). The audio:
 * the receiver's sequence state (the real OpusReorder) locked onto the old
 * stream before the host restarts its audio at sequence 0.
 */
class RestartGuardTest {

    @Test
    fun flagTable() {
        assertTrue(RestartGuardFlag.parse("1"))
        // B19: on unless `0`
        for (on in listOf(null, "", "on", "2")) {
            assertTrue(on, RestartGuardFlag.parse(on))
        }
        assertFalse(RestartGuardFlag.parse("0"))
        assertTrue(RestartGuardFlag.fromSystem())
    }

    private fun freePort(): Int = DatagramSocket(0).use { it.localPort }

    private class Wire(val port: Int, var seq: Int = 100) {
        private val tx = DatagramSocket()
        private var ts = 90_000L

        fun au(idr: Boolean) {
            val nal = byteArrayOf(if (idr) 0x65 else 0x41, 0x11, 0x22, 0x33, 0x44)
            val p = ByteBuffer.allocate(12 + nal.size)
            p.put(0x80.toByte()).put((0x80 or 96).toByte()).putShort(seq.toShort()).putInt(ts.toInt()).putInt(0x1234)
            p.put(nal)
            seq = (seq + 1) and 0xffff
            ts += 1500L
            tx.send(DatagramPacket(p.array(), p.capacity(), InetAddress.getLoopbackAddress(), port))
            Thread.sleep(3)
        }

        fun close() = tx.close()
    }

    private fun receiver(port: Int, queued: MutableList<Int>): RtpH264Receiver =
        RtpH264Receiver(
            port = port,
            onParameterSets = { _, _ -> },
            onAccessUnit = { _, _ -> queued.add(1) },
        ).also { it.start(); Thread.sleep(150) }

    /** The activity's sequence around a lost surface, with or without the guard; returns the host's requests. */
    private fun twoWayDrop(guard: RestartGuard?, clock: LongArray): Pair<List<String>, List<Int>> {
        val posts = Collections.synchronizedList(mutableListOf<String>())
        val port = freePort()
        posts.add("start")                                       // session A's native-stream-start
        val a = mutableListOf<Int>()
        val rxA = receiver(port, a)
        val w = Wire(port)
        repeat(5) { w.au(it == 0) }
        Thread.sleep(100)
        // surfaceDestroyed: the report cached, the guard told, the pipeline stopped (no post today)
        val cached = "{\"session\":\"A\",\"rendered\":${a.size}}"
        guard?.onSurfaceLost(cached, 166L, 120L, false)
        rxA.stop()
        clock[0] += 5_000L                                       // the 5-s drop
        // surfaceCreated -> startSession: today's cachedSessionReport = null; the session thread
        val restart = guard?.takePending()
        restart?.let { p -> guard.flush(p, { r -> posts.add("report:$r") }, { posts.add("stop") }) }
        posts.add("start")                                       // session B's native-stream-start
        val b = mutableListOf<Int>()
        val rxB = receiver(port, b)
        repeat(5) { w.au(it == 0) }
        Thread.sleep(100)
        rxB.stop()
        w.close()
        return posts.toList() to listOf(a.size, b.size)
    }

    @Test
    fun withTheGuardTheOldSessionEndsFirst() {
        val clock = longArrayOf(1_000L)
        val g = RestartGuard { clock[0] }
        val (posts, frames) = twoWayDrop(g, clock)
        assertEquals(listOf("start", "report:{\"session\":\"A\",\"rendered\":5}", "stop", "start"), posts)
        assertEquals(listOf(5, 5), frames)                        // A received, then B on the same port
        val c = g.lastCause
        assertNotNull(c)
        assertEquals(5_000L, c!!["away_ms"])
        assertEquals(166L, c["last_frame_age_ms"])
        assertEquals(true, c["old_report_posted"])
        assertEquals(true, c["stop_posted"])
        assertEquals(1L, g.restarts)
    }

    @Test
    fun withoutTheGuardItIsToday() {
        val (posts, frames) = twoWayDrop(null, longArrayOf(0L))
        assertEquals(listOf("start", "start"), posts)              // no stop, the report lost
        assertEquals(listOf(5, 5), frames)
    }

    @Test
    fun anEndedActivityIsTodaysStopNotASecondOne() {
        val g = RestartGuard { 0L }
        g.onSurfaceLost("r", 1L, 1L, false)
        g.onSessionStopped()
        assertNull(g.takePending())
        assertNull(g.lastCause)
    }

    @Test
    fun aNormalStartClearsTheCauseAndFailedPostsAreRecorded() {
        val g = RestartGuard { 0L }
        g.onSurfaceLost("r", 1L, 1L, true)
        val c = g.flush(g.takePending()!!, { throw IllegalStateException("down") }, { throw IllegalStateException("down") })
        assertEquals(false, c["old_report_posted"])
        assertEquals(false, c["stop_posted"])
        assertEquals(true, c["recovery_active"])
        assertNull(g.takePending())                               // the next, normal start
        assertNull(g.lastCause)
    }

    @Test
    fun thePauseBeforeTheLossIsMeasured() {
        val clock = longArrayOf(0L)
        val g = RestartGuard { clock[0] }
        g.notePause()
        clock[0] = 40L
        g.onSurfaceLost(null, 1L, 1L, false)
        assertEquals(40L, g.takePending()!!.pausedBeforeLossMs)
    }

    // --- the audio: the host restarts its sender at sequence 0 --------------------------------------------------

    private fun feed(r: OpusReorder, seqs: IntRange, sink: MutableList<Int>) {
        for (s in seqs) {
            r.offer(s and 0xffff, byteArrayOf(1), 0, { n, p -> if (p != null) sink.add(n) })
        }
    }

    @Test
    fun aReceiverLockedOnTheOldStreamDropsTheRestartedOne() {
        val today = OpusReorder()
        val sink = mutableListOf<Int>()
        feed(today, 5_800..5_899, sink)                           // the old stream, ~58 s in (10-ms frames)
        sink.clear()
        feed(today, 0..299, sink)                                 // the host's restart: 3 s of audio
        assertEquals(0, sink.size)                                // every frame LATE: the underrun storm
    }

    @Test
    fun aRebuiltReceiverPlaysTheRestartedStream() {
        val sink = mutableListOf<Int>()
        val rebuilt = OpusReorder()                               // B11: a fresh receiver after the start response
        feed(rebuilt, 0..299, sink)
        assertEquals((0..299).toList(), sink)
    }
}
