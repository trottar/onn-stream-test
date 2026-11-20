package com.safeiot.privyhub.streaming

import com.safeiot.privyhub.streaming.TouchPadState.Control
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * G6-JOIN1: holding any touch control for a real pad's join hold (500 ms) during the countdown makes the touch pad P1
 * at once ("hold"); shorter does nothing; no hold -> the countdown at 5 s ("timer"); the joining press is not sent;
 * P1 taken -> nothing new; End is never a pad control.
 */
class G6Join1Test {

    private fun armed(at: Long = 1_000L) = TouchP1Rule().apply { onStart(false); onGameplayReleased(at) }

    @Test
    fun theHoldTimeIsTheRealPadsHold() {
        assertEquals(500L, PlayerPrompt.HOLD_MS)
    }

    @Test
    fun aHoldOfTheRealPadsTimeOnAnyControlJoinsAtOnce() {
        for (c in Control.values()) {
            val rule = armed()
            val j = TouchHoldJoin()
            j.observe(setOf(c), 1_200L)
            assertNull(c.name, j.step(1_699L, rule, p1Free = true, p1HeldByRealPad = false))
            assertEquals(c.name, TouchHoldJoin.Via.HOLD, j.step(1_700L, rule, p1Free = true, p1HeldByRealPad = false))
            assertEquals("hold", TouchHoldJoin.Via.HOLD.report)
            // the countdown stopped: no timer join later, no countdown text
            assertFalse(rule.armed()); assertNull(rule.secondsLeft(2_000L))
            assertNull(j.step(6_100L, rule, p1Free = true, p1HeldByRealPad = false))
        }
    }

    @Test
    fun aShorterHoldDoesNothingAndTheCountdownGoesOn() {
        val rule = armed()
        val j = TouchHoldJoin()
        j.observe(setOf(Control.CROSS), 1_200L)
        j.observe(emptySet(), 1_650L)                                   // lifted after 450 ms
        assertNull(j.step(1_700L, rule, true, false))
        assertNull(j.step(3_000L, rule, true, false))
        assertTrue(rule.armed())
        assertEquals(4, rule.secondsLeft(2_100L))
        // a new hold starts again from its own down
        j.observe(setOf(Control.CROSS), 3_000L)
        assertNull(j.step(3_499L, rule, true, false))
        assertEquals(TouchHoldJoin.Via.HOLD, j.step(3_500L, rule, true, false))
    }

    @Test
    fun noHoldTheTimerJoinsAtFiveSecondsAsToday() {
        val rule = armed()
        val j = TouchHoldJoin()
        assertNull(j.step(5_999L, rule, true, false))
        assertEquals(TouchHoldJoin.Via.TIMER, j.step(6_000L, rule, true, false))
        assertEquals("timer", TouchHoldJoin.Via.TIMER.report)
        assertNull(j.step(7_000L, rule, true, false))                   // once
    }

    @Test
    fun withP1TakenOrNoCountdownAHoldChangesNothing() {
        // a real pad holds P1: the rule gives up as today, the hold joins nothing
        val rule = armed()
        val j = TouchHoldJoin()
        j.observe(setOf(Control.START), 1_100L)
        assertNull(j.step(2_000L, rule, p1Free = false, p1HeldByRealPad = true))
        assertFalse(rule.armed())
        // P1 already the touch pad's (the countdown finished): nothing new
        val done = armed(); val j2 = TouchHoldJoin()
        assertEquals(TouchHoldJoin.Via.TIMER, j2.step(6_000L, done, true, false))
        j2.observe(setOf(Control.CROSS), 6_100L)
        assertNull(j2.step(7_000L, done, p1Free = false, p1HeldByRealPad = false))
        // before the gameplay release (no countdown yet): nothing
        val waiting = TouchP1Rule().apply { onStart(false) }
        val j3 = TouchHoldJoin()
        j3.observe(setOf(Control.CROSS), 0L)
        assertNull(j3.step(2_000L, waiting, true, false))
    }

    // the joining press is not sent until it is lifted; other controls are
    @Test
    fun theJoiningPressIsNotSent() {
        val s = TouchPadState(TouchPadState.Kind.PS2).apply { layout(1200, 1100) }
        val (cx, cy) = s.centreOf(Control.CROSS)!!
        val (lx, ly) = s.centreOf(Control.LSTICK)!!
        assertEquals(TouchPadState.XUSB_A, s.down(1, cx, cy).buttons)
        assertEquals(0, s.output(setOf(Control.CROSS)).buttons)
        s.down(2, lx, ly); s.move(2, lx + 200f, ly)
        val skipStick = s.output(setOf(Control.CROSS, Control.LSTICK))
        assertEquals(0.toShort(), skipStick.lx)
        assertEquals(32767.toShort(), s.output(setOf(Control.CROSS)).lx)   // the stick not skipped: sent
        assertEquals(s.output(), s.output(emptySet()))
    }

    // End is its own view: never a pad control, so never a joining hold, and nothing of the pad claims its place
    @Test
    fun endIsNeverAPadControl() {
        assertFalse(Control.values().any { it.name == "END" })
        val s = TouchPadState(TouchPadState.Kind.PS2).apply { layout(1200, 1100) }
        val e = s.endRect(1200, 1100)
        assertNull(s.controlAt((e[0] + e[2]) / 2, (e[1] + e[3]) / 2))
        assertEquals(0, s.down(9, (e[0] + e[2]) / 2, (e[1] + e[3]) / 2).buttons)
        assertTrue(s.heldControls().isEmpty())
    }
}
