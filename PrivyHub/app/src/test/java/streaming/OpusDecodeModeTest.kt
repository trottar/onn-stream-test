package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * CL-B7P: the drain mode flag. Absent, empty or anything but `lean` is
 * today's drain, which polls again after every output; `lean` polls again
 * only while an output is still pending.
 */
class OpusDecodeModeTest {

    @Test
    fun parseTable() {
        assertEquals(OpusDecodeMode.TODAY, OpusDecodeMode.parse(null))
        assertEquals(OpusDecodeMode.TODAY, OpusDecodeMode.parse(""))
        assertEquals(OpusDecodeMode.TODAY, OpusDecodeMode.parse("today"))
        assertEquals(OpusDecodeMode.TODAY, OpusDecodeMode.parse("lean2"))
        assertEquals(OpusDecodeMode.TODAY, OpusDecodeMode.parse("0"))
        assertEquals(OpusDecodeMode.LEAN, OpusDecodeMode.parse("lean"))
        assertEquals(OpusDecodeMode.LEAN, OpusDecodeMode.parse(" LEAN "))
    }

    @Test
    fun noAndroidPropertyIsToday() {
        // The JVM has no android.os.SystemProperties: the read fails to today.
        assertEquals(OpusDecodeMode.TODAY, OpusDecodeMode.fromSystem())
    }

    @Test
    fun todayPollsAfterEveryOutput() {
        for (pending in -2L..3L) assertTrue(OpusDecodeMode.TODAY.pollAfterOutput(pending))
    }

    @Test
    fun leanPollsOnlyWhilePending() {
        assertFalse(OpusDecodeMode.LEAN.pollAfterOutput(0))
        assertFalse(OpusDecodeMode.LEAN.pollAfterOutput(-1))
        assertTrue(OpusDecodeMode.LEAN.pollAfterOutput(1))
        assertTrue(OpusDecodeMode.LEAN.pollAfterOutput(2))
    }

    @Test
    fun reportNameEmptyForToday() {
        assertEquals("", OpusDecodeMode.TODAY.reportName)
        assertEquals("lean", OpusDecodeMode.LEAN.reportName)
    }
}
