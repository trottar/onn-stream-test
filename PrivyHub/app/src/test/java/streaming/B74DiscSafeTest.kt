package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** B74: the warning once per onn, the chooser, the line after a change, "Start on disc…" for sets only. */
class B74DiscSafeTest {

    @Test
    fun warningOnceThenNever() {
        assertTrue(DiscSafe.needsWarning(safeOn = true, understood = false))     // the first time on this onn
        assertFalse(DiscSafe.needsWarning(safeOn = true, understood = true))     // after "I understand"
        assertFalse(DiscSafe.needsWarning(safeOn = false, understood = false))   // the property off: B71's flow
        assertEquals(
            "Change discs only when the game asks for the next one — changing at any other time can freeze the game",
            DiscSafe.WARNING
        )
        assertEquals("I understand", DiscSafe.UNDERSTAND)
    }

    @Test
    fun theChooserIsB71s() {
        val state = DiscChange.fromValues(4, 1)!!
        assertEquals(listOf("Disc 1 (in the tray)", "Disc 2", "Disc 3", "Disc 4"), DiscChange.choices(state))
        assertEquals(2, DiscChange.discForChoice(1))
    }

    @Test
    fun theLineAfterAChange() {
        assertEquals(
            "Disc 2 of 4 — if the game freezes, use LOAD or END",
            DiscSafe.afterChangeLine(DiscChange.State(4, 2))
        )
        assertEquals(
            "4 discs — if the game freezes, use LOAD or END",
            DiscSafe.afterChangeLine(DiscChange.State(4, null))
        )
    }

    @Test
    fun startOnDiscOnlyForSets() {
        assertTrue(DiscSafe.showStartOnDisc(true, 2))
        assertTrue(DiscSafe.showStartOnDisc(true, 4))
        assertFalse(DiscSafe.showStartOnDisc(true, 1))
        assertFalse(DiscSafe.showStartOnDisc(true, 0))                           // a one-disc game / an old host
        assertFalse(DiscSafe.showStartOnDisc(false, 4))                          // the property off
        assertEquals(listOf("Disc 1", "Disc 2", "Disc 3", "Disc 4"), DiscSafe.startChoices(4))
        assertEquals("Start on disc…", DiscSafe.START_LABEL)
    }

    @Test
    fun theLaunchQuery() {
        assertEquals("", DiscSafe.launchSuffix(null))                            // today's URL
        assertEquals("&disc=3", DiscSafe.launchSuffix(3))
        assertEquals("", DiscSafe.launchSuffix(0))
    }

    @Test
    fun theProperty() {
        assertTrue(DiscSafe.parse(null))
        assertTrue(DiscSafe.parse("1"))
        assertFalse(DiscSafe.parse("0"))
        assertFalse(DiscSafe.parse("off"))
    }
}
