package com.safeiot.privyhub.vod

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B47: the movie retry on by default (`debug.privyhub.vod_retry` absent = on, `0` / `off` = today), and the mark
 * cleared at every READY with no attempt left scheduled (HOME-3 C5'' (a): "reconnecting…" stayed after a `reset`
 * resume). A fake clock, scheduler and player, as B35's test.
 */
class VodRetryDefaultOnTest {

    private class Sched : VodRetryController.Scheduler {
        var task: (() -> Unit)? = null
        var delay = -1L
        override fun schedule(delayMs: Long, task: () -> Unit) { this.task = task; delay = delayMs }
        override fun cancel() { task = null }
        fun run() { val t = task; task = null; t?.invoke() }
    }

    private class Ui : VodRetryController.Ui {
        var shown = false
        var shows = 0
        var hides = 0
        override fun showMark(attempt: Int) { shown = true; shows++ }
        override fun hideMark() { shown = false; hides++ }
        override fun offerRetry() {}
    }

    private class Rig {
        var now = 0L
        val sched = Sched()
        val ui = Ui()
        val rows = mutableListOf<Map<String, Any>>()
        val seeks = mutableListOf<Long>()
        val c = VodRetryController(VodRetryPolicy(), object : VodRetryController.Player {
            override fun retryAt(positionMs: Long) { seeks.add(positionMs) }
        }, sched, { now }, { rows.add(it) }, ui, "vod:/x")
        fun events() = rows.map { it["event"] }
    }

    @Test
    fun absentIsOnAndZeroOrOffIsTodaysNoController() {
        assertTrue(VodRetryController.wanted(VodRetryFlag.parse(null), isLive = false))
        assertTrue(VodRetryController.wanted(VodRetryFlag.parse(""), isLive = false))
        assertTrue(VodRetryController.wanted(VodRetryFlag.parse("junk"), isLive = false))
        assertFalse(VodRetryController.wanted(VodRetryFlag.parse("0"), isLive = false))
        assertFalse(VodRetryController.wanted(VodRetryFlag.parse("off"), isLive = false))
        assertFalse(VodRetryController.wanted(VodRetryFlag.parse(null), isLive = true))   // live TV never
    }

    @Test
    fun aResetEpisodeResumesWithTheMarkGoneAndNothingScheduled() {
        val r = Rig()
        r.now = 1_000
        assertTrue(r.c.onError(2001, "ERROR_CODE_IO_NETWORK_CONNECTION_FAILED", 92_369, VodRetryPolicy.REASON_RESET))
        assertTrue(r.ui.shown)
        repeat(3) {
            r.now += 4_000; r.sched.run()   // the attempt fails
            r.c.onError(2001, "ERROR_CODE_IO_NETWORK_CONNECTION_FAILED", 92_369, VodRetryPolicy.REASON_RESET)
        }
        assertEquals(listOf("vod_error", "vod_retry", "vod_retry", "vod_retry", "vod_retry"), r.events())
        // HOME-3 (a): the player's own reconnect reaches READY while attempt 4 is still scheduled
        r.now += 3_000
        r.c.onReady()
        assertFalse(r.ui.shown)
        assertNull(r.sched.task)                                       // the late attempt dropped
        assertEquals("vod_resumed", r.events().last())
        val seeks = r.seeks.size
        r.sched.run()
        assertEquals(seeks, r.seeks.size)                              // no seek back after the resume
        // a later READY (a seek, a buffer) hides again, idempotent, and writes no row
        val n = r.rows.size; val hides = r.ui.hides
        r.c.onReady()
        assertEquals(n, r.rows.size); assertEquals(hides + 1, r.ui.hides); assertFalse(r.ui.shown)
    }

    @Test
    fun aReadyWithNoEpisodeWritesNoRow() {
        val r = Rig()
        r.c.onReady()
        assertTrue(r.rows.isEmpty())
        assertEquals(1, r.ui.hides)
    }

    @Test
    fun afterACancelNothingIsShownOrHidden() {
        val r = Rig()
        r.c.cancel()
        val hides = r.ui.hides
        r.c.onReady()
        assertEquals(hides, r.ui.hides)
        assertFalse(r.c.onError(2001, "X", 0))
        assertEquals(0, r.ui.shows)
    }
}
