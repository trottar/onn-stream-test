package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B39: the report's `surface_hold` counters count what the `surface_lost` rows counted (HOME-1 C1: the row `held`, the
 * report 0). The activity's report cache modelled as the activity has it (`cacheSessionReport`: first one wins, cleared
 * at a start; the snapshot's `surface_hold` from [SurfaceHold.reportFields]), with B39's three hooks exactly as written
 * in `NativeStreamActivity.kt` (the clear at a held re-attach, the count before the snapshot, the refresh when the
 * outcome is decided). The report is the text `JSONObject.toString()` gives: compact, keys in insertion order.
 */
class HoldReportTest {

    private class Model(val hold: SurfaceHold?, val clock: LongArray) {
        var sessionStarted = false
        var startedAtMs = 0L
        var cachedSessionReport: String? = null
        val posted = mutableListOf<String>()         // reports as they reach the host
        var pendingForNextStart: String? = null      // RestartGuard's cached report, posted at the next start

        fun buildSessionReport(): String {
            val sb = StringBuilder("{\"duration_ms\":${clock[0] - startedAtMs}")
            hold?.let { h -> sb.append(",\"surface_hold\":").append(h.reportFields().entries.joinToString(",", "{", "}") { (k, v) -> "\"$k\":$v" }) }
            sb.append(",\"restart_cause\":null}")
            return sb.toString()
        }

        fun cacheSessionReport(): String? {
            cachedSessionReport?.let { if (it.isNotBlank()) return it }
            return buildSessionReport().also { cachedSessionReport = it }
        }

        fun startSession() {
            if (sessionStarted) return
            pendingForNextStart?.let { posted.add(it) }; pendingForNextStart = null
            sessionStarted = true
            startedAtMs = clock[0]
            cachedSessionReport = null
        }

        fun surfaceDestroyed() {
            val h = hold
            if (sessionStarted && h != null) {           // beginSurfaceHold, B39's order
                h.onSurfaceLost(16L, true)
                cacheSessionReport()
                return
            }
            if (sessionStarted) {
                cacheSessionReport()
                pendingForNextStart = cachedSessionReport  // restartGuard.onSurfaceLost(cachedSessionReport, …)
            }
            sessionStarted = false
        }

        fun surfaceCreated() {
            val h = hold
            if (h != null && sessionStarted && h.onSurfaceBack()) {   // endSurfaceHold
                cachedSessionReport = null
                h.stallAgeMs(clock[0] + 500L, 1L)
                return
            }
            startSession()
        }

        fun expiry() {
            val h = hold ?: return
            if (!h.holding || !h.expired()) return
            h.onExpired()
            cachedSessionReport = h.refreshReport(cachedSessionReport)
            pendingForNextStart = cachedSessionReport
            sessionStarted = false
        }

        fun stop() {                                       // stopSession: the cached (or a fresh) report, posted
            if (!sessionStarted) return
            posted.add(cacheSessionReport()!!)
            sessionStarted = false
        }

        fun destroyInHold() {                              // onDestroy inside a hold, then stopSession
            hold?.let { h -> h.onEndedInHold(); cachedSessionReport = h.refreshReport(cachedSessionReport) }
            stop()
        }
    }

    private fun num(report: String, key: String): Long =
        Regex("\"$key\":(-?\\d+)").find(report)!!.groupValues[1].toLong()

    private fun hold(r: String): String = Regex("\"surface_hold\":\\{[^{}]*\\}").find(r)!!.value

    @Test
    fun aHeldLossThenAStopReportsHeldOne() {
        val clock = longArrayOf(1_000L)
        val m = Model(SurfaceHold(12_000L) { clock[0] }, clock)
        m.startSession()
        clock[0] += 16_000L
        m.surfaceDestroyed()                               // C1 (1): the remote's Home
        clock[0] += 4_400L
        m.surfaceCreated()                                 // back within the bound: the same session
        clock[0] += 30_000L
        m.stop()
        assertEquals(1, m.posted.size)
        val r = m.posted[0]
        assertEquals(1L, num(hold(r), "held"))
        assertEquals(1L, num(hold(r), "losses"))
        assertEquals(0L, num(hold(r), "restarted"))
        assertEquals(50_400L, num(r, "duration_ms"))       // the whole session, not cut at the loss
    }

    @Test
    fun cOnesSequenceHeldThenAnOverBoundLossReportsBoth() {
        val clock = longArrayOf(1_000L)
        val m = Model(SurfaceHold(12_000L) { clock[0] }, clock)
        m.startSession()
        clock[0] += 16_270L
        m.surfaceDestroyed()                               // (1) the Home press, held
        clock[0] += 4_429L
        m.surfaceCreated()
        clock[0] += 34_000L
        m.surfaceDestroyed()                               // (2) the guide press, run as Home by the system
        clock[0] += 12_000L
        m.expiry()                                         // the bound: today's restart path
        clock[0] += 10_400L
        m.surfaceCreated()                                 // the return: a new start posts the cached report
        assertEquals(1, m.posted.size)
        val r = m.posted[0]
        assertEquals(2L, num(hold(r), "losses"))
        assertEquals(1L, num(hold(r), "held"))
        assertEquals(1L, num(hold(r), "restarted"))
        assertEquals(54_699L, num(r, "duration_ms"))       // to the second loss
    }

    @Test
    fun anActivityEndingInsideAHoldReportsEndedInHold() {
        val clock = longArrayOf(1_000L)
        val m = Model(SurfaceHold(12_000L) { clock[0] }, clock)
        m.startSession()
        clock[0] += 5_000L
        m.surfaceDestroyed()
        clock[0] += 2_000L
        m.destroyInHold()
        val r = m.posted.single()
        assertEquals(1L, num(hold(r), "losses"))
        assertEquals(1L, num(hold(r), "ended_in_hold"))
        assertEquals(0L, num(hold(r), "held"))
    }

    @Test
    fun absentTheLossCachesOnceAndTheNextStartPostsItUnchanged() {
        val clock = longArrayOf(1_000L)
        val m = Model(null, clock)
        m.startSession()
        clock[0] += 16_000L
        m.surfaceDestroyed()                               // today: the report cached at the loss
        val cached = m.cachedSessionReport
        clock[0] += 3_000L
        m.surfaceCreated()                                 // today's restart: the cached report posted at the start
        assertEquals(listOf(cached), m.posted)
        assertEquals("{\"duration_ms\":16000,\"restart_cause\":null}", m.posted[0])
        assertTrue(!m.posted[0].contains("surface_hold"))
    }

    @Test
    fun theRefreshReplacesOnlyTheSurfaceHoldObject() {
        val h = SurfaceHold(12_000L) { 0L }
        h.onSurfaceLost(10L, true)
        val before = "{\"duration_ms\":5,\"surface_hold\":{\"bound_ms\":12000,\"losses\":0,\"held\":0},\"pad_slots_mode\":\"stable\",\"pad_slots\":[{\"slot\":0}]}"
        val after = h.refreshReport(before)!!
        assertTrue(after, after.startsWith("{\"duration_ms\":5,\"surface_hold\":{\"bound_ms\":12000,\"losses\":1,\"held\":0,\"restarted\":0,"))
        assertTrue(after, after.endsWith("},\"pad_slots_mode\":\"stable\",\"pad_slots\":[{\"slot\":0}]}"))
        assertEquals("{\"duration_ms\":5}", h.refreshReport("{\"duration_ms\":5}"))
        assertNull(h.refreshReport(null))
    }

    @Test
    fun aPadGuideKeyIsNotConsumedButNoted() {
        val clock = longArrayOf(1_000L)
        val h = SurfaceHold(12_000L) { clock[0] }
        val pad = SurfaceHold.SOURCE_GAMEPAD or SurfaceHold.SOURCE_JOYSTICK
        assertEquals(false, h.onKey(SurfaceHold.KEYCODE_BUTTON_MODE, true, pad))
        assertEquals(0L, h.reportFields()["pad_system_keys_consumed"])
        assertEquals(1L, h.reportFields()["system_keys_passed"])
        clock[0] += 300L
        h.onSurfaceLost(16L, true)
        clock[0] += 1_000L
        h.onSurfaceBack()
        h.stallAgeMs(clock[0], 1L)
        val q = java.net.URLDecoder.decode(h.query().removePrefix("&surface_lost="), "UTF-8")
        assertTrue(q, q.contains("\"reason\":\"pad_system_key\""))
        assertTrue(q, q.contains("\"keys\":[\"110:pad:p\"]"))
    }
}
