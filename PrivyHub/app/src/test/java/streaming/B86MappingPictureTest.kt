package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** B86: the editor's one set of letters and the controller picture's labels (the code the editor runs). */
class B86MappingPictureTest {

    /** The hub's default (emulator_manager.INPUT_PROFILE_EDITOR_DEFAULT_MAPPING): {target (game): source (your pad)}. */
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

    private fun face(labels: Map<String, String>) = listOf("a", "b", "x", "y").associateWith { labels.getValue(it) }

    @Test
    fun theDefaultReadsByPositionNeverAsASwap() {
        val labels = MappingPicture.pictureLabels(default)
        // your pad's Bottom sends the game's B (bottom), Right → A (right), Left → Y (left), Top → X (top)
        assertEquals(mapOf("a" to "B", "b" to "A", "x" to "Y", "y" to "X"), face(labels))
        assertEquals(emptySet<String>(), MappingPicture.changed(default, default))
        assertEquals("Bottom (✕) → B", MappingPicture.rowText("b", default.getValue("b")))
        assertEquals("Right (○) → A", MappingPicture.rowText("a", default.getValue("a")))
        assertEquals("Left (□) → Y", MappingPicture.rowText("y", default.getValue("y")))
        assertEquals("Top (△) → X", MappingPicture.rowText("x", default.getValue("x")))
        assertEquals("L1", labels["l"])
        assertEquals("Start", labels["start"])
    }

    @Test
    fun aBottomRightSwap() {
        val swap = with("a" to "a", "b" to "b")                // the game's A from your Bottom, its B from your Right
        val labels = MappingPicture.pictureLabels(swap)
        assertEquals(mapOf("a" to "A", "b" to "B", "x" to "Y", "y" to "X"), face(labels))
        assertEquals(setOf("a", "b"), MappingPicture.changed(swap, default))
        assertEquals("Bottom (✕) → A", MappingPicture.rowText("a", swap.getValue("a")))
    }

    @Test
    fun aSquareTriangleSwap() {
        val swap = with("x" to "x", "y" to "y")                // the game's X from your Left (□), its Y from your Top (△)
        val labels = MappingPicture.pictureLabels(swap)
        assertEquals(mapOf("a" to "B", "b" to "A", "x" to "X", "y" to "Y"), face(labels))
        assertEquals(setOf("x", "y"), MappingPicture.changed(swap, default))
        assertEquals("Left (□) → X", MappingPicture.rowText("x", swap.getValue("x")))
    }

    @Test
    fun aRowChangeUpdatesTheLabel() {
        val working = LinkedHashMap(default)
        assertEquals("L1", MappingPicture.pictureLabels(working)["l"])
        working["r2"] = "l"                                    // the game's R2 now from your L1 as well
        working["l"] = ""                                       // and the game's L1 from nothing
        val labels = MappingPicture.pictureLabels(working)
        assertEquals("R2", labels["l"])
        assertEquals(MappingPicture.NOTHING, labels["r2"])
        assertEquals(setOf("l", "r2"), MappingPicture.changed(working, default))
        assertEquals("nothing → L1", MappingPicture.rowText("l", working["l"]))
        working["a"] = "a"
        working["b"] = "a"                                      // two targets on one control are both shown
        assertEquals("A+B", MappingPicture.pictureLabels(working)["a"])
    }

    @Test
    fun theStoredMappingIsNeverTouched() {
        val stored = with("a" to "a", "b" to "b")
        val before = stored.toString()
        val copy = LinkedHashMap(stored)
        repeat(3) {                                             // open, redraw, close: the editor's calls
            MappingPicture.pictureLabels(stored)
            MappingPicture.changed(stored, default)
            stored.forEach { (t, s) -> MappingPicture.rowText(t, s) }
        }
        assertEquals(copy, stored)
        assertEquals(before, stored.toString())                // the same bytes, the same order
        assertEquals(before, LinkedHashMap(stored).toString())
    }

    @Test
    fun everyControlHasAPlaceOnThePicture() {
        val layout = MappingPicture.LAYOUT
        assertEquals(default.values.toSet(), layout.keys)        // every source the hub lists
        assertTrue(layout.values.all { (x, y) -> x in 0f..1f && y in 0f..1f })
        assertEquals(layout.size, layout.values.toSet().size)    // no two controls on one spot
        val (bx, by) = layout.getValue("a")
        val (tx, ty) = layout.getValue("y")
        assertTrue(by > ty && bx == tx)                          // Bottom below Top
        assertNotEquals(layout.getValue("x"), layout.getValue("b"))
    }

    @Test
    fun theProperty() {
        assertTrue(MappingPicture.parse(null))
        assertTrue(MappingPicture.parse(""))
        assertFalse(MappingPicture.parse("0"))
        assertFalse(MappingPicture.parse("off"))
        assertEquals("debug.privyhub.mapping_picture", MappingPicture.PROPERTY)
        assertTrue(MappingPicture.LEGEND.contains("B bottom, A right, Y left, X top"))
    }
}
