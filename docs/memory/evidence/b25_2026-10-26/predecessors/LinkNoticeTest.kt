package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B14: the link notice on a fake WifiInfo feed (LinkSample readings every
 * 500 ms on a fake clock, as the activity's UI tick): 2.4 GHz shown at once
 * and once; 5 GHz good for 30 s cleared; RSSI <= -72 or tx <= 54 for 10 s
 * shown; once per session unless the band changes; the flag absent = off.
 */
class LinkNoticeTest {

    private fun s(mhz: Int?, rssi: Int?, tx: Int?) = LinkSample(rssi, tx, 100, mhz, 4)

    private val g24 = s(2412, -68, 121)      // BENCH-R3: the onn all month
    private val g5 = s(5180, -68, 195)       // LINK-R1: 5 GHz, good

    /** Feed one reading every 500 ms from t0 for `seconds`; the events with their times. */
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
    fun flagTable() {
        assertTrue(LinkNoticeFlag.parse("1"))
        for (bad in listOf(null, "", "0", "on", "true")) assertFalse(bad, LinkNoticeFlag.parse(bad))
        assertFalse(LinkNoticeFlag.fromSystem())                  // off-device: off (absent = today)
    }

    @Test
    fun twoPointFourIsShownAtOnceAndOnce() {
        val n = LinkNotice()
        val ev = feed(n, g24, 0, 60.0)
        assertEquals(1, ev.size)
        assertEquals(0L, ev[0].first)
        val shown = ev[0].second as LinkNotice.Event.Shown
        assertEquals(LinkNotice.BAND_24, shown.reasons)
        assertEquals("Wi-Fi: 2.4 GHz\nUse your router's 5 GHz Wi-Fi for this box.", shown.text)
        assertEquals("&link_notice=1", n.query())
    }

    @Test
    fun fiveGhzGoodForThirtySecondsClears() {
        val n = LinkNotice()
        feed(n, g24, 0, 5.0)
        assertTrue(n.shown)
        val ev = feed(n, g5, 5_000, 40.0)
        assertEquals(1, ev.size)
        assertEquals(LinkNotice.Event.Cleared, ev[0].second)
        assertEquals(35_000L, ev[0].first)                        // 30 s after the first good reading, not before
        assertEquals("&link_notice=0", n.query())
    }

    @Test
    fun onceASessionUnlessTheBandChanges() {
        val n = LinkNotice()
        feed(n, g24, 0, 5.0)
        feed(n, g5, 5_000, 31.0)                                  // cleared on 5 GHz
        assertFalse(n.shown)
        val back = feed(n, g24, 36_000, 5.0)                      // the band changed: shown again
        assertEquals(1, back.size)
        val m = LinkNotice()
        feed(m, s(5180, -75, 195), 0, 12.0)                       // weak on 5 GHz: shown
        assertTrue(m.shown)
        feed(m, g5, 12_000, 31.0)                                 // cleared
        val again = feed(m, s(5180, -75, 195), 43_000, 20.0)      // weak again, the same band: not shown
        assertTrue(again.isEmpty())
        m.onSessionStart()                                        // a new session re-arms it
        assertEquals(1, feed(m, s(5180, -75, 195), 70_000, 12.0).size)
        assertEquals(2L, m.shownCount)
    }

    @Test
    fun weakForTenSecondsIsShownNotBefore() {
        val n = LinkNotice()
        val ev = feed(n, s(5180, -72, 195), 0, 15.0)
        assertEquals(1, ev.size)
        assertEquals(10_000L, ev[0].first)
        val shown = ev[0].second as LinkNotice.Event.Shown
        assertEquals(LinkNotice.WEAK, shown.reasons)
        assertEquals("Wi-Fi: weak signal (-72 dBm)\nMove this box or the router closer, or use a wired connection.",
            shown.text)
        assertTrue(feed(LinkNotice(), s(5180, -71, 195), 0, 60.0).isEmpty())   // -71 never
    }

    @Test
    fun slowForTenSecondsIsShownAndADipResets() {
        val n = LinkNotice()
        assertTrue(feed(n, s(5180, -68, 54), 0, 9.5).isEmpty())
        n.update(g5, 9_500)                                       // one good reading resets the 10 s
        val ev = feed(n, s(5180, -68, 48), 10_000, 12.0)
        assertEquals(20_000L, ev[0].first)
        assertEquals("Wi-Fi: slow link (48 Mbps)\nUse the 5 GHz network or move closer to the router.",
            (ev[0].second as LinkNotice.Event.Shown).text)
    }

    @Test
    fun badLinkKeepsItUpAndNullReadingsChangeNothing() {
        val n = LinkNotice()
        feed(n, g24, 0, 1.0)
        assertNull(n.update(null, 100_000))
        assertTrue(n.shown)
        assertTrue(feed(n, s(5180, -68, 40), 1_000, 60.0).isEmpty())   // 5 GHz but slow: never good, stays
        assertTrue(n.shown)
        assertEquals(24, LinkNotice.band(2462))
        assertEquals(5, LinkNotice.band(5745))
        assertNull(LinkNotice.band(null))
    }
}
