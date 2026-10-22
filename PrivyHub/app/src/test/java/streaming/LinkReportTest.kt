package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B3: the Wi-Fi link report. The flag (absent = off), the validity rules, the
 * heartbeat's query keys, and the sampler's once-a-second read (fake clock).
 */
class LinkReportTest {

    @Test
    fun flagTable() {
        assertFalse(LinkReportFlag.parse(null))
        assertFalse(LinkReportFlag.parse(""))
        assertFalse(LinkReportFlag.parse("0"))
        assertFalse(LinkReportFlag.parse("true"))
        assertTrue(LinkReportFlag.parse("1"))
        assertTrue(LinkReportFlag.parse(" 1 "))
    }

    @Test
    fun noAndroidPropertyIsOff() {
        assertFalse(LinkReportFlag.fromSystem())
    }

    @Test
    fun validity() {
        val s = LinkSample.of(rssi = -55, txMbps = 866, rxMbps = 780, frequencyMhz = 5180, wifiStandard = 5)
        assertEquals(LinkSample(-55, 866, 780, 5180, 5), s)
        val bad = LinkSample.of(rssi = -127, txMbps = -1, rxMbps = 0, frequencyMhz = -1, wifiStandard = 0)
        assertEquals(LinkSample(null, null, null, null, null), bad)
        assertNull(LinkSample.of(0, 1, 1, 1, 1).rssiDbm)
    }

    @Test
    fun queryKeysValidOnly() {
        assertEquals(
            "&link_rssi_dbm=-61&link_tx_mbps=433&link_frequency_mhz=5745",
            LinkSample(-61, 433, null, 5745, null).query()
        )
        assertEquals("", LinkSample(null, null, null, null, null).query())
        assertEquals(
            listOf("rssi_dbm" to -61, "rx_mbps" to 390, "wifi_standard" to 6),
            LinkSample(-61, null, 390, null, 6).fields()
        )
    }

    @Test
    fun samplerReadsAtMostOncePerSecond() {
        var now = 0L
        var n = 0
        val sampler = LinkSampler({ n += 1; LinkSample(-50 - n, null, null, null, null) }, { now })
        assertEquals(-51, sampler.current()?.rssiDbm)
        now = 400_000_000L
        assertEquals(-51, sampler.current()?.rssiDbm)
        now = 999_999_999L
        assertEquals(-51, sampler.current()?.rssiDbm)
        now = 1_000_000_000L
        assertEquals(-52, sampler.current()?.rssiDbm)
        assertEquals(2L, sampler.reads)
    }

    @Test
    fun aFailingReadIsNoSample() {
        val sampler = LinkSampler({ throw IllegalStateException("no wifi") }, { 0L })
        assertNull(sampler.current())
    }
}
