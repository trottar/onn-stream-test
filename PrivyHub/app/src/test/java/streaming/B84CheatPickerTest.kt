package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** B84: the cheat picker's model, the whole behaviour the screen runs (rows, keys, filter, sections, selection). */
class B84CheatPickerTest {

    private fun catalog(n: Int): List<CheatEntry> = (0 until n).map { i ->
        val group = when (i % 7) {
            0, 1 -> "general"
            2 -> "player1"
            3 -> "player2"
            4 -> "player3"
            5 -> "player4"
            else -> "other"
        }
        CheatEntry(index = i, label = "Made Up Cheat $i ${if (i % 2 == 0) "Health" else "Speed"}", group = group)
    }

    private val small = listOf(
        CheatEntry(0, "Infinite Health", "general"),
        CheatEntry(1, "Infinite Health — variant 2", "general", variantOf = 0),
        CheatEntry(2, "Max Money", "general"),
        CheatEntry(3, "Infinite Lives — Player 1", "player1"),
        CheatEntry(4, "Infinite Lives — Player 2", "player2"),
        CheatEntry(5, "Moon Jump", "other"),
        CheatEntry(6, "mine.cht: My Own", "yours"),
    )

    private fun press(m: CheatPickerModel, vararg keys: PickerKey): PickerAction {
        var last = PickerAction.NONE
        for (k in keys) last = m.onKey(k)
        return last
    }

    private fun openAll(m: CheatPickerModel) {
        for (g in CheatPicker.GROUPS) if (m.rows.any { it is PickerRow.Header && it.group == g && !it.open }) m.toggleSection(g)
    }

    /** To the filter row with the TV's keys (Down from the bar returns to the row the focus came from; Up climbs). */
    private fun toFilterRow(m: CheatPickerModel) {
        while (m.focus != 1) m.onKey(if (m.focus == 0) PickerKey.DOWN else PickerKey.UP)
    }

    private fun focusRow(m: CheatPickerModel, row: Int) {
        toFilterRow(m)
        while (m.focus < row) m.onKey(PickerKey.DOWN)
        assertEquals(row, m.focus)
    }

    @Test
    fun launchInTwoPressesFromEveryRow() {
        val m = CheatPickerModel(catalog(300))
        openAll(m)
        m.toggle(5)
        for (row in 1 until m.rows.size) {
            focusRow(m, row)
            assertEquals("row $row", PickerAction.NONE, m.onKey(PickerKey.LEFT))       // 1: to Launch
            assertEquals(0, m.focus)
            assertEquals(0, m.barButton)
            assertEquals("row $row", PickerAction.LAUNCH, m.onKey(PickerKey.OK))       // 2: Launch
        }
        for (row in 1 until m.rows.size step 37) {
            focusRow(m, row)
            assertEquals(PickerAction.LAUNCH, m.onKey(PickerKey.START))               // the pad's Start: one press
        }
    }

    @Test
    fun upFromTheFilterRowReachesTheBarAndDownComesBack() {
        val m = CheatPickerModel(small)
        assertEquals(2, m.focus)                            // the list's first row on opening
        press(m, PickerKey.UP)
        assertEquals(1, m.focus)                            // the filter row
        press(m, PickerKey.UP)
        assertEquals(0, m.focus)                            // the bar, on Launch
        press(m, PickerKey.DOWN)
        assertEquals(1, m.focus)
        press(m, PickerKey.DOWN, PickerKey.DOWN, PickerKey.LEFT, PickerKey.DOWN)
        assertEquals(3, m.focus)                            // Left from a list row, then Down: back to that row
    }

    @Test
    fun cancelFromTheBarAndBack() {
        val m = CheatPickerModel(small)
        assertEquals(PickerAction.CANCEL, press(m, PickerKey.LEFT, PickerKey.RIGHT, PickerKey.OK))
        assertEquals(PickerAction.CANCEL, CheatPickerModel(small).onKey(PickerKey.BACK))
        assertEquals(PickerKey.BACK, CheatPickerModel.keyOf(4))       // KEYCODE_BACK
        assertEquals(PickerKey.START, CheatPickerModel.keyOf(108))    // KEYCODE_BUTTON_START
        assertEquals(PickerKey.PAGE_DOWN, CheatPickerModel.keyOf(103)) // KEYCODE_BUTTON_R1
        assertEquals(PickerKey.PAGE_UP, CheatPickerModel.keyOf(166))   // KEYCODE_CHANNEL_UP
    }

    @Test
    fun sectionsCollapsedWithTheirCounts() {
        val m = CheatPickerModel(small)
        val headers = m.rows.filterIsInstance<PickerRow.Header>()
        assertEquals(listOf("general", "player1", "player2", "other", "yours"), headers.map { it.group })
        assertEquals(listOf(3, 1, 1, 1, 1), headers.map { it.count })
        assertTrue(headers.none { it.open })
        assertEquals(2 + 5, m.rows.size)                     // the bar, the filter, five headers: nothing else
        assertEquals("▸ Player 1 (1)", m.text(headers[1]))
        assertEquals("▸ Your files (1)", m.text(headers[4]))
        assertEquals(PickerAction.NONE, m.onKey(PickerKey.OK))   // OK on the first header opens it
        assertEquals(listOf(0, 1, 2), m.rows.filterIsInstance<PickerRow.Item>().map { it.entry.index })
        assertTrue(m.rows.filterIsInstance<PickerRow.Item>()[1].indent)   // the variant sits under its first
    }

    @Test
    fun theFilterNarrowsAndCounts() {
        val m = CheatPickerModel(small)
        m.setFilter("lives")
        val headers = m.rows.filterIsInstance<PickerRow.Header>()
        assertEquals(listOf("player1", "player2"), headers.map { it.group })
        assertTrue(headers.all { it.open && it.count == 1 })
        m.setFilter("player   2 LIVES")                     // every word, any order, any case
        assertEquals(listOf(4), m.rows.filterIsInstance<PickerRow.Item>().map { it.entry.index })
        m.setFilter("nothing like this")
        assertEquals(2, m.rows.size)
        m.setFilter("")
        assertEquals(2 + 5, m.rows.size)
    }

    @Test
    fun startLaunchesTheTickedIndexes() {
        val m = CheatPickerModel(small)
        press(m, PickerKey.OK, PickerKey.DOWN, PickerKey.OK, PickerKey.DOWN, PickerKey.DOWN, PickerKey.OK)
        assertEquals(listOf(0, 2), m.selection().map { it.index })
        assertEquals("☑ Max Money", m.text(m.rows[m.focus]))
        assertEquals("Launch Cheat Session   Cancel   2 selected", m.text(PickerRow.Bar))
        assertEquals(PickerAction.LAUNCH, m.onKey(PickerKey.START))
    }

    @Test
    fun theSelectionSurvivesFilterSelectedOnlyAndClosing() {
        val m = CheatPickerModel(small)
        m.toggle(3)
        m.toggle(6)
        m.setFilter("health")
        m.toggle(1)
        assertEquals(setOf(1, 3, 6), m.selection().map { it.index }.toSet())
        m.setFilter("")
        m.toggleSection("player1")
        m.toggleSection("player1")
        assertEquals(listOf(1, 3, 6), m.selection().map { it.index })
        toFilterRow(m)
        press(m, PickerKey.RIGHT)                                      // the filter row: Right = "Selected only"
        assertTrue(m.selectedOnly)
        assertEquals(listOf(1, 3, 6), m.rows.filterIsInstance<PickerRow.Item>().map { it.entry.index })
        assertEquals(listOf(1, 1, 1), m.rows.filterIsInstance<PickerRow.Header>().map { it.count })
        m.toggleSelectedOnly()
        assertFalse(m.selectedOnly)
        assertEquals(3, m.selectedCount)
    }

    @Test
    fun twoThousandNinetyTwoEntriesOpenAsHeadersOnly() {
        val start = System.nanoTime()
        val m = CheatPickerModel(catalog(2092))
        val ms = (System.nanoTime() - start) / 1_000_000
        assertTrue("built in $ms ms", ms < 1000)
        assertEquals(2 + 6, m.rows.size)                     // the bar, the filter and six headers, no entry row
        assertEquals(2092, m.rows.filterIsInstance<PickerRow.Header>().sumOf { it.count })
        m.toggleSection("player1")
        assertEquals(2 + 6 + 299, m.rows.size)              // only the opened section's own rows
        val t2 = System.nanoTime()
        m.setFilter("health")
        assertTrue((System.nanoTime() - t2) / 1_000_000 < 1000)
        assertEquals(1046, m.rows.count { it is PickerRow.Item })
    }

    @Test
    fun pagingByAScreen() {
        val m = CheatPickerModel(catalog(200), pageSize = 10)
        m.toggleSection("general")
        assertEquals(2, m.focus)
        press(m, PickerKey.PAGE_DOWN)
        assertEquals(12, m.focus)
        press(m, PickerKey.PAGE_DOWN, PickerKey.PAGE_DOWN)
        assertEquals(32, m.focus)
        press(m, PickerKey.PAGE_UP)
        assertEquals(22, m.focus)
        press(m, PickerKey.PAGE_UP, PickerKey.PAGE_UP, PickerKey.PAGE_UP)
        assertEquals(2, m.focus)                             // never into the bar or the filter row by paging
    }

    @Test
    fun aHubWithoutGroupsIsOneGeneralSection() {
        assertEquals("general", CheatPicker.groupOf(null))
        assertEquals("general", CheatPicker.groupOf(""))
        assertEquals("general", CheatPicker.groupOf("something_new"))
        assertEquals("player3", CheatPicker.groupOf("Player3"))
        val m = CheatPickerModel(listOf(CheatEntry(0, "a"), CheatEntry(1, "b")))
        assertEquals(listOf("general"), m.rows.filterIsInstance<PickerRow.Header>().map { it.group })
    }

    @Test
    fun theProperty() {
        assertTrue(CheatPicker.parse(null))
        assertTrue(CheatPicker.parse(""))
        assertTrue(CheatPicker.parse("1"))
        assertFalse(CheatPicker.parse("0"))
        assertFalse(CheatPicker.parse("off"))
        assertEquals("debug.privyhub.cheat_picker", CheatPicker.PROPERTY)
    }
}
