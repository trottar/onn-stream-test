package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** B92: the mapping list's changed rows (yellow, as the picture's changed controls). */
class B92ChangedRowsTest {

    private val default: Map<String, String> = linkedMapOf(
        "up" to "up", "down" to "down", "left" to "left", "right" to "right",
        "a" to "b", "b" to "a", "x" to "y", "y" to "x",
        "l" to "l", "r" to "r", "l2" to "l2", "r2" to "r2", "l3" to "l3", "r3" to "r3",
        "select" to "select", "start" to "start",
        "left_stick_left" to "left_stick_left", "left_stick_right" to "left_stick_right",
        "left_stick_up" to "left_stick_up", "left_stick_down" to "left_stick_down",
        "right_stick_left" to "right_stick_left", "right_stick_right" to "right_stick_right",
        "right_stick_up" to "right_stick_up", "right_stick_down" to "right_stick_down"
    )

    private fun with(vararg pairs: Pair<String, String>): Map<String, String> =
        LinkedHashMap(default).apply { pairs.forEach { (k, v) -> put(k, v) } }

    private val swap = with("a" to "a", "b" to "b")
    private val many = with(
        "a" to "a", "b" to "b", "l" to "r", "r" to "l", "l2" to "r2", "r2" to "l2",
        "select" to "start", "start" to "select", "x" to "l3", "l3" to "y",
        "up" to "left_stick_up", "left_stick_up" to "up"
    )

    @Test
    fun theDefaultHasNoChangedRow() {
        assertEquals(emptySet<String>(), MappingPicture.changedRows(default, default))
    }

    @Test
    fun theSwapAndTheManyButtonRemap() {
        assertEquals(setOf("a", "b"), MappingPicture.changedRows(swap, default))
        assertEquals(setOf("a", "b", "l", "r", "l2", "r2", "select", "start", "x", "l3", "up", "left_stick_up"),
                     MappingPicture.changedRows(many, default))
    }

    @Test
    fun aBlankControlIsChangedAndCaseOrSpacesAreNot() {
        assertEquals(setOf("a"), MappingPicture.changedRows(with("a" to ""), default))
        assertEquals(emptySet<String>(), MappingPicture.changedRows(with("a" to " B ", "start" to "START"), default))
        assertEquals(setOf("start"), MappingPicture.changedRows(default - "start", default))
    }

    @Test
    fun theListAndThePictureAgree() {
        for (case in listOf(swap, many)) {
            val rows = MappingPicture.changedRows(case, default)
            val controls = MappingPicture.changed(case, default)
            for (t in rows) assertTrue("$t", case[t] in controls || default[t] in controls)
            assertFalse(rows.isEmpty() != controls.isEmpty())
        }
        assertEquals(0xFFFFC107.toInt(), MappingPicture.CHANGED_COLOR)
    }

    @Test
    fun theSwitch() {
        assertFalse(MappingPicture.parse("0"))
        assertTrue(MappingPicture.parse(null))
    }
}
