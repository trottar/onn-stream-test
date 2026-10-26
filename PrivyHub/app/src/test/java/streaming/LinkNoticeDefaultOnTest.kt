package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B25: debug.privyhub.link_notice absent / empty / junk = ON, `0` = off (B14's
 * absent: no object, no key). The notice object is built as the activity's lazy
 * builds it; readings every 500 ms on a fake clock, as LinkNoticeTest.
 */
class LinkNoticeDefaultOnTest {

    private fun s(mhz: Int?, rssi: Int?, tx: Int?) = LinkSample(rssi, tx, 100, mhz, 4)

    private val g24 = s(2412, -68, 121)      // G-A5's precondition read: the onn back on 2.4 GHz
    private val g5 = s(5180, -68, 195)       // 5 GHz, good

    /** As NativeStreamActivity's `linkNotice` lazy, from a property value. */
    private fun built(property: String?): LinkNotice? = if (LinkNoticeFlag.parse(property)) LinkNotice() else null

    /** B14's parse, kept here only for the comparison. */
    private fun b14Parse(value: String?): Boolean = value?.trim() == "1"

    /** As the heartbeat's fragment: `linkNotice?.query() ?: ""`. */
    private fun fragment(n: LinkNotice?): String = n?.query() ?: ""

    private fun feed(n: LinkNotice, r: LinkSample, t0: Long, seconds: Double): List<Pair<Long, LinkNotice.Event>> {
        val out = mutableListOf<Pair<Long, LinkNotice.Event>>()
        var t = t0
        while (t < t0 + (seconds * 1000).toLong()) {
            n.update(r, t)?.let { out.add(t to it) }
            t += 500
        }
        return out
    }

    @Test
    fun theTable() {
        for (on in listOf(null, "", " ", "1", " 1 ", "on", "true", "2", "yes")) assertTrue("[$on]", LinkNoticeFlag.parse(on))
        for (off in listOf("0", " 0 ", "0\n")) assertFalse("[$off]", LinkNoticeFlag.parse(off))
        assertTrue(LinkNoticeFlag.fromSystem())                   // off-device the read fails: a failed read = on
    }

    @Test
    fun absentIsOnTwoPointFourShownOnce() {
        val n = built(null)!!
        n.onSessionStart()
        val ev = feed(n, g24, 0, 60.0)
        assertEquals(1, ev.size)
        assertEquals(0L, ev[0].first)
        val shown = ev[0].second as LinkNotice.Event.Shown
        assertEquals(LinkNotice.BAND_24, shown.reasons)
        assertEquals("Wi-Fi: 2.4 GHz\nUse your router's 5 GHz Wi-Fi for this box.", shown.text)   // B14's wording
        assertEquals("&link_notice=1", fragment(n))
        assertEquals(1L, n.shownCount)
    }

    @Test
    fun absentIsOnFiveGhzGoodIsQuietWithTheKeyPresent() {
        for (p in listOf(null, "", "junk")) {
            val n = built(p)!!
            n.onSessionStart()
            assertTrue(feed(n, g5, 0, 60.0).isEmpty())
            assertFalse(n.shown)
            assertEquals("&link_notice=0", fragment(n))            // armed, not shown: CL-B14's heartbeat key
        }
        // the home 5-GHz reads (-66..-70 dBm; G-A5's -70 for minutes) stay quiet; -72 held 10 s still shows (B14)
        val n = built(null)!!
        assertTrue(feed(n, s(5180, -70, 195), 0, 120.0).isEmpty())
        assertEquals(1, feed(n, s(5180, -72, 195), 120_000, 12.0).size)
    }

    @Test
    fun zeroIsTodaysAbsent() {
        assertNull(built("0"))
        assertEquals("", fragment(built("0")))                     // no key, as B14's absent
        assertEquals(b14Parse(null), LinkNoticeFlag.parse("0"))   // `0` now = B14's absent
        assertEquals(b14Parse("1"), LinkNoticeFlag.parse("1"))    // `1` unchanged
    }
}
