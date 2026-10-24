package com.safeiot.privyhub.streaming

import java.io.File
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.nio.ByteBuffer
import java.nio.file.Files
import java.util.Collections
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B15: the restart guard on every path. B11's guard kept its pending in the activity object, so a start in another
 * instance -- CL-B10 cell 1's Home press: the old process gone, the activity re-created in a new one -- found nothing
 * (no report, no stop, `restart_cause` null, the audio storm). Here the pending is kept in a store (a temp file) and
 * each path is modelled as the activity calls the guard (B11's `twoWayDrop` shape): the surface's loss, the start's
 * take + flush, `stopSession`'s hand-over. The real RtpH264Receiver on loopback with a fake decoder; the real
 * OpusReorder as the audio's sequence state; a fake host transport.
 */
class RestartGuardAllPathsTest {

    private val dir: File = Files.createTempDirectory("b15_store_").toFile()
    private var n = 0

    private fun storeFile(): File = File(dir, "pending_${n++}.properties")

    private fun guard(clock: LongArray, file: File?, instance: Long, mark: Long): RestartGuard =
        RestartGuard { clock[0] }.also { g -> file?.let { g.attach(FilePendingStore(it), instance, mark) } }

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

    private fun feed(r: OpusReorder, seqs: IntRange, sink: MutableList<Int>) {
        for (s in seqs) {
            r.offer(s and 0xffff, byteArrayOf(1), 0, { n, p -> if (p != null) sink.add(n) })
        }
    }

    /** The activity's start: the take, the flush (report, stop), the start; the audio rebuilt when it restarted. */
    private class Host {
        val posts: MutableList<String> = Collections.synchronizedList(mutableListOf<String>())

        fun start(g: RestartGuard?, carriedAudio: OpusReorder): OpusReorder {
            val restart = g?.takePending()
            restart?.let { p -> g.flush(p, { r -> posts.add("report:$r") }, { posts.add("stop") }) }
            posts.add("start")
            return if (restart != null) OpusReorder() else carriedAudio
        }

        /** `stopSession`: B15's hand-over first, then B11's clear and today's posts. */
        fun stopSession(g: RestartGuard?, changing: Boolean, live: Boolean, report: String?) {
            if (g?.handOver(changing, live) { report } == true) {
                return
            }
            g?.onSessionStopped()
            report?.let { posts.add("report:$it") }
            posts.add("stop")
        }
    }

    /** A session of 5 frames on the real receiver, its surface then lost (the report cached, the guard told). */
    private fun sessionThenLoss(g: RestartGuard?, port: Int, w: Wire, name: String): Int {
        val got = mutableListOf<Int>()
        val rx = receiver(port, got)
        repeat(5) { w.au(it == 0) }
        Thread.sleep(100)
        g?.onSurfaceLost("{\"session\":\"$name\",\"rendered\":${got.size}}", 166L, 120L, false)
        rx.stop()
        return got.size
    }

    private fun sessionFrames(port: Int, w: Wire): Int {
        val got = mutableListOf<Int>()
        val rx = receiver(port, got)
        repeat(5) { w.au(it == 0) }
        Thread.sleep(100)
        rx.stop()
        return got.size
    }

    /** The host's audio restarted at sequence 0 into [audio]; [lockedOnOld] first plays the old stream ~58 s in. */
    private fun framesAfterHostRestart(audio: OpusReorder, lockedOnOld: Boolean): Int {
        if (lockedOnOld) {
            feed(audio, 5_800..5_899, mutableListOf())
        }
        val sink = mutableListOf<Int>()
        feed(audio, 0..299, sink)
        return sink.size
    }

    @Test
    fun aFiveSecondSurfaceLossInTheSameInstance() {
        val clock = longArrayOf(10_000L)
        val g = guard(clock, storeFile(), 1L, 100L)
        val host = Host()
        val port = freePort()
        val w = Wire(port)
        val carried = OpusReorder()
        host.start(g, carried)
        assertEquals(5, sessionThenLoss(g, port, w, "A"))
        clock[0] += 5_000L                                       // Home for 5 s, then back
        val audio = host.start(g, carried)
        assertEquals(5, sessionFrames(port, w))
        w.close()
        assertEquals(listOf("start", "report:{\"session\":\"A\",\"rendered\":5}", "stop", "start"), host.posts)
        val c = g.lastCause!!
        assertEquals("surface", c["trigger"])
        assertEquals(5_000L, c["away_ms"])
        assertEquals(true, c["old_report_posted"])
        assertEquals(true, c["stop_posted"])
        assertTrue(audio !== carried)                             // rebuilt after the host's start
        assertEquals(300, framesAfterHostRestart(audio, lockedOnOld = false))    // the restarted stream plays
        assertEquals(0, framesAfterHostRestart(carried, lockedOnOld = true))     // carried: every frame late (the storm)
    }

    @Test
    fun theProcessPathCellOnesHomePress() {
        val clock = longArrayOf(50_000L)
        val f = storeFile()
        val a = guard(clock, f, 1L, 100L)                         // the first process
        val host = Host()
        val port = freePort()
        val w = Wire(port)
        host.start(a, OpusReorder())
        sessionThenLoss(a, port, w, "A")
        assertTrue(f.length() > 0L)
        clock[0] += 6_100L                                       // the process dies; the activity is re-created in a new one
        val b = guard(clock, f, 1L, 7_000L)                       // instance 1 of another process
        val carried = OpusReorder()
        val audio = host.start(b, carried)
        assertEquals(5, sessionFrames(port, w))
        w.close()
        assertEquals(listOf("start", "report:{\"session\":\"A\",\"rendered\":5}", "stop", "start"), host.posts)
        assertEquals("process", b.lastCause!!["trigger"])
        assertEquals(6_100L, b.lastCause!!["away_ms"])
        assertTrue(audio !== carried)                             // the audio rebuilt with its hold re-armed
        assertEquals(0L, f.length())                              // taken once
        // B11's memory-only guard in the new process: a normal start (cell 1's rows)
        val f2 = storeFile()
        val a2 = guard(clock, f2, 1L, 100L)
        a2.onSurfaceLost("{\"session\":\"A2\"}", 1L, 1L, false)
        val b11 = RestartGuard { clock[0] }
        val today = Host()
        today.start(b11, OpusReorder())
        assertEquals(listOf("start"), today.posts)
        assertNull(b11.lastCause)
    }

    @Test
    fun aRecreationHandsOverInsteadOfRacing() {
        val clock = longArrayOf(0L)
        val f = storeFile()
        val a = guard(clock, f, 1L, 100L)
        val host = Host()
        host.start(a, OpusReorder())
        a.onSurfaceLost("{\"session\":\"A\"}", 20L, 20L, false)
        host.stopSession(a, changing = true, live = false, report = "{\"session\":\"A\"}")   // onDestroy, recreated
        assertEquals(listOf("start"), host.posts)                // no stop raced against the next start
        clock[0] += 900L
        val b = guard(clock, f, 2L, 100L)                         // the next instance, the same process
        host.start(b, OpusReorder())
        assertEquals(listOf("start", "report:{\"session\":\"A\"}", "stop", "start"), host.posts)
        assertEquals("recreate", b.lastCause!!["trigger"])
        assertEquals(900L, b.lastCause!!["away_ms"])
        // the surface not lost before the destroy: the hand-over makes the pending from the cached report
        val f2 = storeFile()
        val c = guard(clock, f2, 3L, 100L)
        assertTrue(c.handOver(true, true) { "{\"session\":\"C\"}" })
        val d = guard(clock, f2, 4L, 100L)
        val p = d.takePending()
        assertNotNull(p)
        assertEquals("{\"session\":\"C\"}", p!!.report)
        assertEquals("recreate", p.trigger)
        // nothing open: no hand-over (today's stop path)
        assertFalse(guard(clock, storeFile(), 5L, 100L).handOver(true, false) { null })
    }

    @Test
    fun anOldInstanceDestroyedAfterAnotherTookItsPendingPostsNothing() {
        val clock = longArrayOf(0L)
        val f = storeFile()
        val a = guard(clock, f, 1L, 100L)
        val host = Host()
        host.start(a, OpusReorder())
        a.onSurfaceLost("{\"session\":\"A\"}", 1L, 1L, false)
        val b = guard(clock, f, 2L, 100L)                         // a second launch while A stays stopped
        host.start(b, OpusReorder())
        host.stopSession(a, changing = false, live = false, report = "{\"session\":\"A\"}")   // A destroyed later
        assertEquals(listOf("start", "report:{\"session\":\"A\"}", "stop", "start"), host.posts)   // one stop
        assertNull(a.takePending())                                // A's surface back: a normal start, no re-flush
    }

    @Test
    fun aNormalEndClearsOnlyItsOwnPending() {
        val clock = longArrayOf(0L)
        val f = storeFile()
        val a = guard(clock, f, 1L, 100L)
        a.onSurfaceLost("{\"session\":\"A\"}", 1L, 1L, false)
        val host = Host()
        host.stopSession(a, changing = false, live = false, report = "{\"session\":\"A\"}")   // the back-out
        assertEquals(listOf("report:{\"session\":\"A\"}", "stop"), host.posts)              // today's path
        assertEquals(0L, f.length())
        assertNull(guard(clock, f, 1L, 999L).takePending())                                 // the next start: normal
        // another instance's normal end leaves this one's pending in the store
        val g = guard(clock, f, 2L, 100L)
        g.onSurfaceLost("{\"session\":\"G\"}", 1L, 1L, false)
        val other = guard(clock, f, 3L, 100L)
        Host().stopSession(other, changing = false, live = true, report = "{\"session\":\"O\"}")
        assertEquals("{\"session\":\"G\"}", FilePendingStore(f).load()!!.report)
    }

    @Test
    fun aCorruptOrMissingStoreIsANormalStartAndAFailedWriteFallsBackToMemory() {
        val clock = longArrayOf(0L)
        val bad = storeFile().also { it.writeText("lost_at_ms=abc\n") }
        assertNull(FilePendingStore(bad).load())
        assertNull(guard(clock, bad, 1L, 100L).takePending())
        assertNull(FilePendingStore(File(dir, "missing.properties")).load())
        val unwritable = Files.createTempDirectory(dir.toPath(), "a_dir_").toFile()       // a directory: the write fails
        val g = guard(clock, unwritable, 1L, 100L)
        g.onSurfaceLost("{\"session\":\"M\"}", 1L, 1L, false)
        val p = g.takePending()
        assertEquals("{\"session\":\"M\"}", p!!.report)
        assertEquals("surface", p.trigger)
    }

    @Test
    fun theStoreKeepsTheFieldsAndNoAddress() {
        val f = storeFile()
        val p = PendingRestart("{\"r\":1}", 1234L, 166L, 120L, true, 40L, instance = 2L, processMark = 77L)
        assertTrue(FilePendingStore(f).save(p))
        assertEquals(p, FilePendingStore(f).load())
        val keys = f.readLines().filter { !it.startsWith("#") }.map { it.substringBefore('=') }.sorted()
        assertEquals(listOf("instance", "last_frame_age_ms", "lost_at_ms", "paused_before_loss_ms", "process_mark",
            "recovery_active", "report", "rtp_silence_ms"), keys)
    }

    @Test
    fun theFlagAbsentIsToday() {
        val host = Host()
        val port = freePort()
        val w = Wire(port)
        val carried = OpusReorder()
        host.start(null, carried)
        sessionThenLoss(null, port, w, "A")
        val audio = host.start(null, carried)
        assertEquals(5, sessionFrames(port, w))
        w.close()
        assertEquals(listOf("start", "start"), host.posts)        // no stop, the report lost
        assertTrue(audio === carried)                             // the receiver carried over (the storm's state)
        assertFalse(RestartGuardFlag.parse("0"))                 // B19: `0` is today's off
    }
}
