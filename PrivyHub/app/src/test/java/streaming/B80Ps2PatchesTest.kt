package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** B80: "Patches…" only when the hub offers one; the labels; the save's query; today's Extras without patches. */
class B80Ps2PatchesTest {

    @Test
    fun entryOnlyWhenOffered() {
        assertTrue(Ps2Patches.showEntry(true, listOf("ws")))
        assertFalse(Ps2Patches.showEntry(true, emptyList()))
        assertFalse(Ps2Patches.showEntry(false, listOf("ws", "60")))          // the property off: today's Extras
        assertFalse(Ps2Patches.showEntry(true, listOf("something_new")))      // an unknown key is not shown
    }

    @Test
    fun theWordsOnTheTv() {
        assertEquals(listOf("Widescreen", "No interlacing", "60 fps"), Ps2Patches.KEYS.map { Ps2Patches.label(it) })
        assertEquals("Patches…", Ps2Patches.ENTRY_LABEL)
        assertEquals(listOf("ws", "60"), Ps2Patches.known(listOf("60", "x", "ws")))
    }

    @Test
    fun theQuery() {
        assertEquals("id=g1&ws=1&fps60=0", Ps2Patches.query("g1", listOf("ws", "60"), setOf("ws")))
        assertEquals("id=g1&ni=1", Ps2Patches.query("g1", listOf("ni"), setOf("ni", "ws")))
    }

    @Test
    fun extrasListIsTodaysWithoutPatches() {
        assertEquals(listOf("Cheats", "Mods"), Ps2Patches.extrasItems(startOnDisc = false, patches = false))
        assertEquals(listOf("Cheats", "Mods", DiscSafe.START_LABEL), Ps2Patches.extrasItems(true, false))
        assertEquals(listOf("Cheats", "Mods", "Patches…"), Ps2Patches.extrasItems(false, true))
    }

    @Test
    fun theProperty() {
        assertTrue(Ps2Patches.parse(null))
        assertTrue(Ps2Patches.parse(""))
        assertFalse(Ps2Patches.parse("0"))
        assertFalse(Ps2Patches.parse("off"))
    }
}
