package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** B71: the "Change disc" entry only on a multi-disc session; the chooser's labels; "Disc 2 of 4"; the property. */
class B71DiscChangeTest {

    @Test
    fun entryOnlyWithMoreThanOneDisc() {
        assertFalse(DiscChange.showEntry(true, DiscChange.fromValues(null, null)))   // an old host / a one-disc game
        assertFalse(DiscChange.showEntry(true, DiscChange.fromValues(0, null)))
        assertFalse(DiscChange.showEntry(true, DiscChange.fromValues(1, 1)))
        assertTrue(DiscChange.showEntry(true, DiscChange.fromValues(2, 1)))
        assertTrue(DiscChange.showEntry(true, DiscChange.fromValues(4, null)))
        assertFalse(DiscChange.showEntry(false, DiscChange.fromValues(4, 2)))      // the property off: today
    }

    @Test
    fun choicesMarkTheCurrentDisc() {
        assertEquals(listOf("Disc 1", "Disc 2 (in the tray)", "Disc 3", "Disc 4"),
            DiscChange.choices(DiscChange.State(4, 2)))
        assertEquals(listOf("Disc 1", "Disc 2"), DiscChange.choices(DiscChange.State(2, null)))   // unknown: none
        assertEquals(2, DiscChange.discForChoice(1))
        assertEquals("disc=2", DiscChange.query(2))
    }

    @Test
    fun theStatusLine() {
        assertEquals("Disc 2 of 4", DiscChange.statusLine(DiscChange.State(4, 2)))
        assertEquals("4 discs", DiscChange.statusLine(DiscChange.State(4, null)))
        assertEquals("Changing to disc 3…", DiscChange.progressLine(3))
    }

    @Test
    fun theReplyParse() {
        // the host's reply after a swap: discs 4, disc 3
        assertEquals(DiscChange.State(4, 3), DiscChange.fromValues(4, 3))
        // a disc out of range is treated as unknown, never shown as current
        assertNull(DiscChange.fromValues(4, 7)?.disc)
        assertNull(DiscChange.fromValues(2, 0)?.disc)
    }

    @Test
    fun theProperty() {
        assertTrue(DiscChange.parse(null))
        assertTrue(DiscChange.parse(""))
        assertFalse(DiscChange.parse("0"))
        assertFalse(DiscChange.parse("off"))
        assertEquals("debug.privyhub.disc_change", DiscChange.PROPERTY)
    }
}
