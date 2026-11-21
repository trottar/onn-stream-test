package com.safeiot.privyhub.streaming

import com.safeiot.privyhub.streaming.TouchPadState.Control
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * G6-SWAP1 (the user, 2026-11-21: "swap the right face and analogs everything else remains unchanged"): the face
 * diamond centres on (900, 295), the right stick on (900, 805); every other control where G6-JOIN1 had it.
 * The figures: `docs/memory/evidence/g6_swap1_2026-11-21/layout_check_swap1.py`.
 */
class G6Swap1Test {

    private val s = TouchPadState(TouchPadState.Kind.PS2).apply { layout(1200, 1100) }
    private fun c(control: Control) = s.centreOf(control)!!

    @Test
    fun theFiveMovedControls() {
        assertEquals(900f to 205f, c(Control.TRIANGLE))
        assertEquals(990f to 295f, c(Control.CIRCLE))
        assertEquals(900f to 385f, c(Control.CROSS))
        assertEquals(810f to 295f, c(Control.SQUARE))
        assertEquals(900f to 805f, c(Control.RSTICK))
        // the diamond unchanged: 90 px from its centre, the right stick's old place
        for (f in listOf(Control.TRIANGLE, Control.CIRCLE, Control.CROSS, Control.SQUARE)) {
            val (x, y) = c(f)
            assertEquals(f.name, 90.0, Math.hypot((x - 900f).toDouble(), (y - 295f).toDouble()), 1e-6)
        }
        // sizes, press areas and hit scales unchanged
        val d = s.drawn().associateBy { it.control }
        assertEquals(52f, d.getValue(Control.CROSS).halfW, 0f)
        assertEquals(52f * 1.2f, d.getValue(Control.TRIANGLE).hitHalfW, 1e-4f)
        assertEquals(115.5f, d.getValue(Control.RSTICK).halfW, 1e-3f)
        assertEquals(158.4f, d.getValue(Control.RSTICK).hitHalfW, 1e-3f)
    }

    // every other control exactly as G6-JOIN1 (G6-SCREEN1's places)
    @Test
    fun everyOtherControlStaysPut() {
        val join1 = mapOf(
            Control.LSTICK to (300f to 805f), Control.DPAD to (300f to 295f), Control.L3 to (540f to 815f),
            Control.R3 to (690f to 565f), Control.SELECT to (400f to 70f), Control.START to (600f to 70f),
            Control.L2 to (56f to 549f), Control.L1 to (170f to 549f), Control.R1 to (1030f to 549f), Control.R2 to (1144f to 549f),
        )
        for ((control, xy) in join1) assertEquals(control.name, xy, c(control))
        assertEquals(listOf(1004.5f, 22.5f, 1155.5f, 117.5f), s.endRect(1200, 1100).toList())   // End at (1080, 70)
        assertEquals(15, s.drawn().size)
    }

    // the face buttons and the right stick behave as before, in their new places
    @Test
    fun theyWorkInTheirNewPlaces() {
        for ((f, bit) in listOf(Control.TRIANGLE to TouchPadState.XUSB_Y, Control.CIRCLE to TouchPadState.XUSB_B,
                                Control.CROSS to TouchPadState.XUSB_A, Control.SQUARE to TouchPadState.XUSB_X)) {
            val (x, y) = c(f)
            assertEquals(f, s.controlAt(x, y))
            assertEquals(f.name, bit, s.down(1, x, y).buttons)
            s.up(1)
        }
        val (rx, ry) = c(Control.RSTICK)
        assertEquals(Control.RSTICK, s.controlAt(rx, ry - 150f))                 // the unchanged press area
        s.down(2, rx, ry)
        assertEquals(32767.toShort(), s.move(2, rx, ry - 115.5f).ry)              // up, full (the DS2 mapping)
        assertEquals((-32767).toShort(), s.move(2, rx - 115.5f, ry).rx)            // left, full
        val corner = s.move(2, rx + 100f, ry - 100f)                              // a corner: full on both axes
        assertEquals(32767.toShort(), corner.rx); assertEquals(32767.toShort(), corner.ry)
        assertEquals(0.toShort(), corner.lx)
        s.up(2)
        // L3 / R3 unchanged
        assertEquals(TouchPadState.XUSB_RIGHT_THUMB, c(Control.R3).let { (x, y) -> s.down(3, x, y) }.buttons)
        assertTrue(s.cancel().buttons == 0)
    }

    // End (1080, 70) keeps >= 0.5 cm to every press area; the nearest is now △ (73.9 px = 0.78 cm)
    @Test
    fun endKeepsItsClearance() {
        val pxCm = 240.0 / 2.54
        val e = s.endRect(1200, 1100)
        fun gapTo(d: TouchPadState.Drawn): Double {
            val dx = maxOf(maxOf(e[0] - d.cx, d.cx - e[2]).toDouble(), 0.0)
            val dy = maxOf(maxOf(e[1] - d.cy, d.cy - e[3]).toDouble(), 0.0)
            return if (d.halfH == 0f) Math.hypot(dx, dy) - d.hitHalfW
            else Math.hypot(maxOf(dx - d.hitHalfW, 0.0), maxOf(dy - d.hitHalfH, 0.0))
        }
        val gaps = s.drawn().associate { it.control to gapTo(it) }
        for ((control, g) in gaps) assertTrue("${control.name} $g", g >= 0.5 * pxCm)
        assertEquals(Control.TRIANGLE, gaps.minByOrNull { it.value }!!.key)
        assertEquals(73.9, gaps.getValue(Control.TRIANGLE), 0.05)
    }

    @Test
    fun theLayoutVersion() {
        assertEquals("ps2-swap1", Ps2TouchLayout.LAYOUT_VERSION)
    }
}
