package com.safeiot.privyhub.streaming

import java.io.File
import java.nio.file.Files
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B17: the audio waits for the guard's start, and the old session's end rides in the start. B15's harness (a temp
 * file as the store, an injected clock, the activity's calls modelled in order) with a slow fake host: 300 ms per post,
 * on the clock. CL-B11 cell 1: the new instance's `startSession` ran 0.67 s after its creation; B15's two posts before
 * the start (report, stop) then held the start back while the new receiver played the host's old stream and starved
 * (221 underruns). The audio's sequence state is the real OpusReorder.
 */
class RestartGuardAudioOrderTest {

    private val dir: File = Files.createTempDirectory("b17_store_").toFile()
    private var n = 0
    private fun storeFile(): File = File(dir, "pending_${n++}.properties")

    private val surfaceMs = 670L                                   // CL-B11: creation -> startSession

    private class Audio(val clock: LongArray) {
        var startedAtMs = -1L
        val reorder = OpusReorder()
        fun start() { startedAtMs = clock[0] }
    }

    /** 300 ms per post on the clock; the start answers `guard_end` only when [acks]. */
    private class SlowHost(val clock: LongArray, val acks: Boolean = true) {
        val posts = mutableListOf<Pair<String, Long>>()
        fun post(what: String): Boolean {
            posts.add(what to clock[0])
            clock[0] += 300L
            return acks && what.endsWith("&guard_end=1")
        }
        fun names() = posts.map { it.first }
        fun at(prefix: String) = posts.first { it.first.startsWith(prefix) }.second
    }

    private class Run(val audioAtStart: Audio, val audioAfter: Audio, val startResponseAt: Long)

    /** The activity, B17: the surface, `startSession` (prepare, the receiver held or started), the session thread. */
    private fun startB17(g: RestartGuard?, host: SlowHost, clock: LongArray): Run {
        clock[0] += surfaceMs
        val holds = g?.prepareStart() == true
        val audio = Audio(clock).also { if (!holds) it.start() }
        val restart = g?.takePending()
        restart?.let { p -> g.beginViaStart(p) }
        val acked = host.post("start?port=48100" + (if (restart != null) "&guard_end=1" else ""))
        val responseAt = clock[0]
        var after = audio
        if (restart != null) {
            g.noteStartResponse(acked)
            after = Audio(clock).also { it.start() }                 // B11's rebuild after the response
            g.reportAfterStart(restart) { r -> host.post("report:$r") }   // its own thread in the app
        }
        return Run(audio, after, responseAt)
    }

    /** The old instance: a session, then its surface lost (the pending written). */
    private fun lose(g: RestartGuard, clock: LongArray, name: String) {
        g.onSurfaceLost("{\"session\":\"$name\"}", 15L, 10L, false)
        clock[0] += 19_500L                                         // away (CL-B11: ~19.5 s to the new instance)
    }

    @Test
    fun theRecreatePathWithASlowHost() {
        val clock = longArrayOf(1_000L)
        val f = storeFile()
        val a = RestartGuard { clock[0] }.also { it.attach(FilePendingStore(f), 1L, 100L) }
        lose(a, clock, "A")
        val created = clock[0]
        val b = RestartGuard { clock[0] }.also { it.attach(FilePendingStore(f), 2L, 100L) }   // a new instance
        val host = SlowHost(clock)
        val r = startB17(b, host, clock)
        assertEquals(listOf("start?port=48100&guard_end=1", "report:{\"session\":\"A\"}"), host.names())
        assertEquals(0, host.names().count { it.startsWith("stop") })                  // no separate stop
        val createToStart = host.at("start") - created
        assertTrue(createToStart <= 1_000L)                                            // R2
        assertEquals(surfaceMs, createToStart)
        assertEquals(-1L, r.audioAtStart.startedAtMs)                                  // held: never started
        assertTrue(r.audioAfter.startedAtMs >= r.startResponseAt)                      // after the start's response
        val c = b.lastCause!!
        assertEquals("recreate", c["trigger"])
        assertEquals("via_start", c["flush"])
        assertEquals(createToStart, c["create_to_start_ms"])
        assertEquals(true, c["host_ended_session"])
        assertEquals(true, c["old_report_posted"])
        assertEquals(false, c["stop_posted"])
        assertEquals(19_500L + surfaceMs, c["away_ms"])
        // the rebuilt audio plays the host's restarted stream from sequence 0
        val sink = mutableListOf<Int>()
        for (s in 0..299) r.audioAfter.reorder.offer(s, byteArrayOf(1), 0, { k, p -> if (p != null) sink.add(k) })
        assertEquals(300, sink.size)
        // B15's order with the same host: report, stop, then the start at 1.27 s (and the host's ~2.3-s stop besides)
        val clock2 = longArrayOf(0L)
        val old = SlowHost(clock2)
        clock2[0] += surfaceMs
        old.post("report"); old.post("stop"); old.post("start")
        assertEquals(1_270L, old.at("start"))
    }

    @Test
    fun theSurfaceAndProcessPathsTheSameWay() {
        for ((mark, trigger) in listOf(100L to "surface", 7_000L to "process")) {
            val clock = longArrayOf(5_000L)
            val f = storeFile()
            val a = RestartGuard { clock[0] }.also { it.attach(FilePendingStore(f), 1L, 100L) }
            lose(a, clock, "A")
            val g = if (trigger == "surface") a else RestartGuard { clock[0] }.also { it.attach(FilePendingStore(f), 1L, mark) }
            val host = SlowHost(clock)
            val r = startB17(g, host, clock)
            assertEquals(trigger, listOf("start?port=48100&guard_end=1", "report:{\"session\":\"A\"}"), host.names())
            assertEquals(trigger, g.lastCause!!["trigger"])
            assertEquals(-1L, r.audioAtStart.startedAtMs)
            assertTrue(r.audioAfter.startedAtMs >= r.startResponseAt)
        }
    }

    @Test
    fun aHostWithoutGuardEndIsRecordedNotWorkedAround() {
        val clock = longArrayOf(0L)
        val f = storeFile()
        val a = RestartGuard { clock[0] }.also { it.attach(FilePendingStore(f), 1L, 100L) }
        lose(a, clock, "A")
        val b = RestartGuard { clock[0] }.also { it.attach(FilePendingStore(f), 2L, 100L) }
        val host = SlowHost(clock, acks = false)
        startB17(b, host, clock)
        assertEquals(1, host.names().count { it.startsWith("start") })
        assertEquals(false, b.lastCause!!["host_ended_session"])
        assertEquals(0, host.names().count { it.startsWith("stop") })                  // never a stop after a start
    }

    @Test
    fun aNormalStartAfterPrepareIsANormalStart() {
        val clock = longArrayOf(0L)
        val g = RestartGuard { clock[0] }.also { it.attach(FilePendingStore(storeFile()), 1L, 100L) }
        val host = SlowHost(clock)
        val r = startB17(g, host, clock)
        assertEquals(listOf("start?port=48100"), host.names())
        assertTrue(r.audioAtStart.startedAtMs >= 0L)                                    // started at once, as today
        assertNull(g.lastCause)
    }

    @Test
    fun theFlagAbsentIsToday() {
        val clock = longArrayOf(0L)
        val host = SlowHost(clock)
        val r = startB17(null, host, clock)
        assertEquals(listOf("start?port=48100"), host.names())
        assertEquals(surfaceMs, r.audioAtStart.startedAtMs)                             // the receiver at once
        assertFalse(RestartGuardFlag.parse("0"))                 // B19: `0` is today's off
    }
}
