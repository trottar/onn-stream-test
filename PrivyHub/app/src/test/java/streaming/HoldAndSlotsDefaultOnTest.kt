package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * B42: the screen-loss hold (G-A11) and stable slots (G-A12) on by default; `0` / `off` = `0132b944…`'s absent.
 * Design: `docs/memory/evidence/b42_2026-11-06/design_written_before_code.md` (hashed before this code).
 */
class HoldAndSlotsDefaultOnTest {

    private val junk = listOf("yes", "true", "ON", "OFF", "Off", "Stable", "2", "-5", "9999", "30001", "1.5", "junk")

    // `0132b944…`'s parses, verbatim (B32 / B34), for the off-path comparison
    private fun holdToday(value: String?): Long? {
        val v = value?.trim() ?: return null
        if (v == "1") return SurfaceHoldFlag.DEFAULT_BOUND_MS
        val n = v.toLongOrNull() ?: return null
        return if (n in SurfaceHoldFlag.MIN_BOUND_MS..SurfaceHoldFlag.MAX_BOUND_MS) n else null
    }

    private fun slotsToday(value: String?): Boolean = value?.trim() == "stable"

    @Test
    fun theHoldIsOnWhenAbsentEmptyOrJunk() {
        assertEquals(12_000L, SurfaceHoldFlag.parse(null))
        assertEquals(12_000L, SurfaceHoldFlag.parse(""))
        assertEquals(12_000L, SurfaceHoldFlag.parse("   "))
        for (v in junk) assertEquals(v, 12_000L, SurfaceHoldFlag.parse(v))
        assertEquals(12_000L, SurfaceHoldFlag.fromSystem())  // the JVM has no SystemProperties: a failed read = absent
    }

    @Test
    fun theHoldKeepsItsValues() {
        assertEquals(12_000L, SurfaceHoldFlag.parse("1"))
        assertEquals(10_000L, SurfaceHoldFlag.parse("10000"))
        assertEquals(20_000L, SurfaceHoldFlag.parse(" 20000 "))
        assertEquals(30_000L, SurfaceHoldFlag.parse("30000"))
    }

    @Test
    fun theHoldIsOffOnlyForZeroOrOff() {
        assertNull(SurfaceHoldFlag.parse("0"))
        assertNull(SurfaceHoldFlag.parse(" 0 "))
        assertNull(SurfaceHoldFlag.parse("off"))
        assertNull(SurfaceHoldFlag.parse(" off "))
    }

    @Test
    fun theSlotsAreStableWhenAbsentEmptyOrJunk() {
        assertTrue(PadSlotsFlag.parse(null))
        assertTrue(PadSlotsFlag.parse(""))
        assertTrue(PadSlotsFlag.parse("stable"))
        for (v in junk) assertTrue(v, PadSlotsFlag.parse(v))
        assertTrue(PadSlotsFlag.fromSystem())
    }

    @Test
    fun theSlotsAreOffOnlyForOffOrZero() {
        assertFalse(PadSlotsFlag.parse("off"))
        assertFalse(PadSlotsFlag.parse(" off "))
        assertFalse(PadSlotsFlag.parse("0"))
    }

    @Test
    fun theOffWordsGiveTodaysAbsent() {
        // the consumers build an object only from a non-null bound / true: `0` / `off` now give exactly what the
        // CONFIRMED build gave with no property, so no SurfaceHold and no PadSlots -- today's path
        for (off in listOf("0", "off")) {
            assertEquals(holdToday(null), SurfaceHoldFlag.parse(off))
            assertEquals(slotsToday(null), PadSlotsFlag.parse(off))
        }
        // and every value the old parse turned on still gives the same value
        for (v in listOf("1", "10000", "20000", "30000")) assertEquals(v, holdToday(v), SurfaceHoldFlag.parse(v))
        assertEquals(slotsToday("stable"), PadSlotsFlag.parse("stable"))
    }
}
