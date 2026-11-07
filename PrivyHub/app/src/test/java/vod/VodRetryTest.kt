package com.safeiot.privyhub.vod

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B35: the movie player's retry on a fake clock, scheduler, player and server. The fake server serves a movie at
 * a fixed byte rate and drops the connection at a byte position (TRIP-R2 §4: ~1 h 50 min in); it comes back after a
 * while, or never. The fake player plays from it, raises Media3's 2001 at the drop, and reconnects with a Range from
 * the position it is asked to seek to.
 */
class VodRetryTest {

    private class Clock { var now = 0L }

    private class FakeScheduler(private val clock: Clock) : VodRetryController.Scheduler {
        var task: Pair<Long, () -> Unit>? = null
        override fun schedule(delayMs: Long, task: () -> Unit) { this.task = (clock.now + delayMs) to task }
        override fun cancel() { task = null }

        /** Runs the pending task when due, until [until]; each run may schedule the next. */
        fun runUntil(until: Long) {
            while (true) {
                val t = task ?: break
                if (t.first > until) break
                clock.now = t.first
                task = null
                t.second()
            }
            if (clock.now < until) clock.now = until
        }
    }

    /** A movie at [bytesPerMs]; the connection drops at [dropAtByte]; the server is back at [upAtMs] (or never). */
    private class FakeServer(val bytesPerMs: Long, val dropAtByte: Long, var upAtMs: Long?) {
        val rangeStarts = mutableListOf<Long>()
        fun open(nowMs: Long, fromByte: Long): Boolean {
            rangeStarts.add(fromByte)
            val up = upAtMs
            return up != null && nowMs >= up
        }
    }

    private class FakeUi : VodRetryController.Ui {
        var markShown = false
        var marks = 0
        var retryOffered = 0
        override fun showMark(attempt: Int) { markShown = true; marks++ }
        override fun hideMark() { markShown = false }
        override fun offerRetry() { retryOffered++ }
    }

    private inner class Rig(upAtMs: Long?, private val flag: Boolean = true) {
        val clock = Clock()
        val scheduler = FakeScheduler(clock)
        val ui = FakeUi()
        val rows = mutableListOf<Map<String, Any>>()
        val server = FakeServer(bytesPerMs = 500L, dropAtByte = 6_600_000L * 500L, upAtMs = upAtMs)
        var positionMs = 0L
        var ready = false
        var todaysErrorShown = 0
        lateinit var controller: VodRetryController

        val player = object : VodRetryController.Player {
            override fun retryAt(positionMs: Long) {
                this@Rig.positionMs = positionMs
                if (server.open(clock.now, positionMs * server.bytesPerMs)) {
                    ready = true
                    controller.onReady()
                } else {
                    error()          // Media3 reports the failed open as a fresh 2001
                }
            }
        }

        /** As MainActivity: built only with the flag and not live. */
        val built: VodRetryController? =
            if (VodRetryController.wanted(flag, isLive = false)) {
                VodRetryController(VodRetryPolicy(), player, scheduler, { clock.now }, { rows.add(it) }, ui,
                    "vod:/library/A Long Feature (2026).mkv").also { controller = it }
            } else null

        /** MainActivity's onPlayerError: today's branch runs unless the controller handled the error. */
        fun error(code: Int = 2001, name: String = "ERROR_CODE_IO_NETWORK_CONNECTION_FAILED") {
            ready = false
            if (built?.onError(code, name, positionMs) == true) return
            todaysErrorShown++
            built?.afterTodaysError()
        }

        /** Plays from the start at 1x until the server drops the connection at its byte position. */
        fun playToTheDrop() {
            server.open(0L, 0L)
            ready = true
            val dropMs = server.dropAtByte / server.bytesPerMs
            clock.now = dropMs
            positionMs = dropMs
            error()
        }

        fun events() = rows.map { it["event"] }
    }

    @Test
    fun theFlag() {
        // B47 (disclosed, as B42): absent / empty / junk / 1 = on; only 0 / off = today's absent
        assertTrue(VodRetryFlag.parse("1"))
        assertTrue(VodRetryFlag.parse(" 1 "))
        for (v in listOf(null, "", "true", "yes", "2", "junk")) assertTrue(v.toString(), VodRetryFlag.parse(v))
        for (v in listOf("0", " 0 ", "off")) assertFalse(v, VodRetryFlag.parse(v))
        assertTrue(VodRetryFlag.read())           // no SystemProperties on the JVM: absent = on
        assertTrue(VodRetryController.wanted(true, isLive = false))
        assertFalse(VodRetryController.wanted(true, isLive = true))
        assertFalse(VodRetryController.wanted(false, isLive = false))
    }

    @Test
    fun theBackoffAndTheBound() {
        val p = VodRetryPolicy()
        assertEquals(listOf(1_000L, 2_000L, 4_000L, 8_000L, 15_000L, 15_000L, 15_000L), (1..7).map { p.delayBefore(it) })
        assertTrue(p.boundMs >= 120_000L)
        assertEquals(150_000L, p.boundMs)
        assertTrue(VodRetryPolicy.isRetryable(2001))
        assertFalse(VodRetryPolicy.isRetryable(2005))
        assertFalse(VodRetryPolicy.isRetryable(4001))
    }

    @Test
    fun aDropAtABytePositionResumesThereWithinTheBound() {
        val r = Rig(upAtMs = null)
        r.playToTheDrop()
        val dropMs = 6_600_000L
        val dropByte = r.server.dropAtByte
        assertTrue(r.ui.markShown)
        assertEquals(0, r.todaysErrorShown)
        r.server.upAtMs = dropMs + 10_000L                    // the link heals 10 s after the drop
        r.scheduler.runUntil(dropMs + VodRetryPolicy.BOUND_MS)
        assertTrue(r.ready)
        assertEquals(dropMs, r.positionMs)
        assertEquals(dropByte, r.server.rangeStarts.last())   // the reconnect's Range starts at the drop's byte
        assertEquals(listOf(0L, dropByte, dropByte, dropByte, dropByte), r.server.rangeStarts)
        assertEquals(listOf("vod_error", "vod_retry", "vod_retry", "vod_retry", "vod_retry", "vod_resumed"), r.events())
        val resumed = r.rows.last()
        assertEquals(4, resumed["attempts"])
        assertEquals(15_000L, resumed["elapsed_ms"])          // attempts at +1, +3, +7, +15 s
        assertTrue((resumed["elapsed_ms"] as Long) <= VodRetryPolicy.BOUND_MS)
        assertEquals(dropMs, resumed["position_ms"])
        assertFalse(r.ui.markShown)
        assertEquals(0, r.todaysErrorShown)
        assertEquals(0, r.ui.retryOffered)
        assertNull(r.scheduler.task)
    }

    @Test
    fun theServerDownGivesTodaysErrorAfterTheBoundThenRetry() {
        val r = Rig(upAtMs = null)
        r.playToTheDrop()
        val dropMs = r.clock.now
        r.scheduler.runUntil(dropMs + 10 * 60_000L)
        assertFalse(r.ready)
        assertEquals(1, r.todaysErrorShown)                   // today's "Playback error", once
        assertEquals(1, r.ui.retryOffered)
        assertFalse(r.ui.markShown)
        val gaveUp = r.rows.last()
        assertEquals("vod_gave_up", gaveUp["event"])
        val elapsed = gaveUp["elapsed_ms"] as Long
        assertTrue("elapsed $elapsed", elapsed in 120_000L..VodRetryPolicy.BOUND_MS)
        assertEquals(13, gaveUp["attempts"])                  // +1 +3 +7 +15 +30 … +150 s (the bound inclusive)
        assertEquals(dropMs, gaveUp["position_ms"])
        assertTrue(r.server.rangeStarts.drop(1).all { it == r.server.dropAtByte })
        // the Retry button: the server is back now
        r.server.upAtMs = r.clock.now
        r.controller.manualRetry()
        assertTrue(r.ready)
        assertEquals(dropMs, r.positionMs)
        assertEquals("vod_resumed", r.rows.last()["event"])
    }

    @Test
    fun aNonRetryableErrorIsTodaysAtOnce() {
        val r = Rig(upAtMs = null)
        r.error(code = 2005, name = "ERROR_CODE_IO_FILE_NOT_FOUND")
        assertEquals(1, r.todaysErrorShown)
        assertTrue(r.rows.isEmpty())
        assertEquals(0, r.ui.retryOffered)
        assertNull(r.scheduler.task)
    }

    @Test
    fun cancelDropsThePendingAttempt() {
        val r = Rig(upAtMs = 0L)
        r.playToTheDrop()
        r.controller.cancel()
        r.scheduler.runUntil(r.clock.now + 60_000L)
        assertFalse(r.ready)
        assertEquals(listOf("vod_error", "vod_retry"), r.events())
        assertFalse(r.ui.markShown)
    }

    @Test
    fun noTitleOrPathInAnyRow() {
        val r = Rig(upAtMs = null)
        r.playToTheDrop()
        r.scheduler.runUntil(r.clock.now + 10 * 60_000L)
        val text = r.rows.joinToString { it.toString() }
        for (bad in listOf("Long", "Feature", "mkv", "library", "/")) assertFalse(bad, text.contains(bad))
        assertTrue(r.rows.all { (it["media"] as String).matches(Regex("^[0-9a-f]{12}$")) })
    }

    @Test
    fun absentIsToday() {
        val r = Rig(upAtMs = 0L, flag = false)
        assertNull(r.built)
        r.positionMs = 6_600_000L
        r.error()
        assertEquals(1, r.todaysErrorShown)                   // "Playback error" at once, no retry
        assertTrue(r.rows.isEmpty())
        assertNull(r.scheduler.task)
        assertEquals(0, r.ui.marks)
        assertTrue(r.server.rangeStarts.isEmpty())
    }
}
