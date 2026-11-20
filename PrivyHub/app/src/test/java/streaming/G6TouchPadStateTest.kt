package com.safeiot.privyhub.streaming

import com.safeiot.privyhub.streaming.TouchPadState.Control
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/**
 * G6-HM2: the touch pad's state, geometry and input helpers (design `g6_hm1_2026-11-19` §4 test list 1-12), on the
 * tablet's portrait pad region 1200 x 1325.
 */
class G6TouchPadStateTest {

    private val W = 1200
    private val H = 1325
    private lateinit var s: TouchPadState

    @Before
    fun setUp() {
        s = TouchPadState().apply { layout(W, H) }
    }

    private fun c(control: Control) = s.centreOf(control)!!
    private fun downOn(id: Int, control: Control) = c(control).let { (x, y) -> s.down(id, x, y) }

    private val bits = mapOf(
        Control.CROSS to TouchPadState.XUSB_A, Control.CIRCLE to TouchPadState.XUSB_B,
        Control.SQUARE to TouchPadState.XUSB_X, Control.TRIANGLE to TouchPadState.XUSB_Y,
        Control.L1 to TouchPadState.XUSB_LEFT_SHOULDER, Control.R1 to TouchPadState.XUSB_RIGHT_SHOULDER,
        Control.SELECT to TouchPadState.XUSB_BACK, Control.START to TouchPadState.XUSB_START,
    )

    // 1. each control alone
    @Test
    fun eachButtonAloneSetsItsBitAndUpClearsIt() {
        for ((control, bit) in bits) {
            assertEquals(control.name, bit, downOn(1, control).buttons)
            assertEquals(control.name, TouchPadState.Output(), s.up(1))
        }
        assertEquals(255, downOn(1, Control.L2).lt); assertEquals(0, s.output().rt); s.up(1)
        assertEquals(255, downOn(1, Control.R2).rt); assertEquals(0, s.output().lt); s.up(1)
        assertEquals(TouchPadState.Output(), s.output())
    }

    // 2. several fingers at once
    @Test
    fun severalFingersAtOnceAreIndependent() {
        val (dx, dy) = c(Control.DPAD)
        s.down(1, dx + 200f, dy)                  // right
        downOn(2, Control.CROSS)
        val all = downOn(3, Control.R2)
        assertEquals(TouchPadState.XUSB_DPAD_RIGHT or TouchPadState.XUSB_A, all.buttons)
        assertEquals(255, all.rt)
        assertEquals(3, s.heldFingers())
        assertEquals(TouchPadState.XUSB_DPAD_RIGHT or TouchPadState.XUSB_A, s.up(3).buttons.also { assertEquals(0, s.output().rt) })
        assertEquals(TouchPadState.XUSB_A, s.up(1).buttons)
        assertEquals(TouchPadState.Output(), s.up(2))
    }

    // 3. cancel
    @Test
    fun cancelWithThreeFingersReleasesEverything() {
        downOn(1, Control.CROSS); downOn(2, Control.L2); downOn(3, Control.START)
        assertEquals(TouchPadState.Output(), s.cancel())
        assertEquals(0, s.heldFingers())
    }

    // 4. sliding off keeps the button; sliding onto another presses nothing
    @Test
    fun aFingerKeepsItsControlUntilItsUp() {
        downOn(1, Control.CROSS)
        assertEquals(TouchPadState.XUSB_A, s.move(1, 5f, 5f).buttons)                   // slid far off
        val (cx, cy) = c(Control.CIRCLE)
        assertEquals(TouchPadState.XUSB_A, s.move(1, cx, cy).buttons)                   // onto Circle: still Cross
        assertEquals(0, s.up(1).buttons)
        // a finger down on nothing stays on nothing
        assertNull(s.controlAt(W / 2f, H * 0.97f))
        assertEquals(0, s.down(2, W / 2f, H * 0.97f).buttons)
        assertEquals(0, s.move(2, cx, cy).buttons)
    }

    // 5. the D-pad's angle edges, the dead zone, the roll
    @Test
    fun dpadSectorEdgesAreHalfOpen() {
        fun at(deg: Double): Int? {
            val r = Math.toRadians(deg)
            return TouchPadState.dpadSector((100 * Math.cos(r)).toFloat(), (100 * Math.sin(r)).toFloat(), 100f)
        }
        val edges = listOf(22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5)
        for ((k, e) in edges.withIndex()) {
            assertEquals("just below $e", k % 8, at(e - 0.01))
            assertEquals("at/above $e", (k + 1) % 8, at(e + 0.01))
        }
        assertEquals(0, at(0.0)); assertEquals(2, at(90.0)); assertEquals(4, at(180.0)); assertEquals(6, at(270.0))
        assertNull(TouchPadState.dpadSector(10f, 10f, 100f))                // inside 0.25 r
        assertEquals(0, TouchPadState.dpadSector(26f, 0f, 100f))
    }

    @Test
    fun dpadRollsWithoutLifting() {
        val (dx, dy) = c(Control.DPAD)
        assertEquals(TouchPadState.XUSB_DPAD_RIGHT, s.down(1, dx + 150f, dy).buttons)
        assertEquals(TouchPadState.XUSB_DPAD_RIGHT or TouchPadState.XUSB_DPAD_DOWN, s.move(1, dx + 150f, dy + 150f).buttons)
        assertEquals(TouchPadState.XUSB_DPAD_DOWN, s.move(1, dx, dy + 150f).buttons)          // screen y down = down
        assertEquals(TouchPadState.XUSB_DPAD_UP or TouchPadState.XUSB_DPAD_LEFT, s.move(1, dx - 150f, dy - 150f).buttons)
        assertEquals(0, s.move(1, dx + 5f, dy).buttons)                                       // the dead centre
        assertEquals(TouchPadState.XUSB_DPAD_RIGHT, s.move(1, dx + 400f, dy).buttons)         // beyond its hit area: kept
    }

    // 6. reset mid-press; an old pointer id is ignored
    @Test
    fun resetReleasesAndOldPointersAreIgnored() {
        downOn(7, Control.TRIANGLE)
        assertEquals(TouchPadState.Output(), s.reset())
        val (x, y) = c(Control.TRIANGLE)
        assertEquals(0, s.move(7, x, y).buttons)
        assertEquals(0, s.up(7).buttons)
    }

    // 7. the hit-area margin
    @Test
    fun hitAreasAreLargerThanTheDrawing() {
        val (x, y) = c(Control.CROSS)
        val r = 0.07f * W
        assertEquals(Control.CROSS, s.controlAt(x, y + r * 1.25f))        // outside the drawing, inside x1.3
        assertNull(s.controlAt(x, y + r * 1.35f))                         // outside x1.3
        val (dx, dy) = c(Control.DPAD)
        assertEquals(Control.DPAD, s.controlAt(dx, dy - 0.17f * W * 1.45f))
        assertNull(s.controlAt(dx, dy - 0.17f * W * 1.55f))
    }

    // 8. overlapping hit areas: the nearest centre
    @Test
    fun overlappingHitAreasGoToTheNearestCentre() {
        val (tx, ty) = c(Control.TRIANGLE)
        val (rx, ry) = c(Control.CIRCLE)
        val mx = (tx + rx) / 2f
        val my = (ty + ry) / 2f
        assertEquals(Control.TRIANGLE, s.controlAt(mx - 2f, my - 2f))
        assertEquals(Control.CIRCLE, s.controlAt(mx + 2f, my + 2f))
        assertEquals(TouchPadState.XUSB_Y, s.down(1, mx - 2f, my - 2f).buttons)     // one finger, one button
    }

    @Test
    fun theBottomTenthIsEmpty() {
        for (x in 0 until W step 10) assertNull("x=$x", s.controlAt(x.toFloat(), H * 0.905f))
    }

    // 9. the XUSB values (NativeControllerSender's private constants)
    @Test
    fun xusbValuesArePinned() {
        assertEquals(0x0001, TouchPadState.XUSB_DPAD_UP); assertEquals(0x0002, TouchPadState.XUSB_DPAD_DOWN)
        assertEquals(0x0004, TouchPadState.XUSB_DPAD_LEFT); assertEquals(0x0008, TouchPadState.XUSB_DPAD_RIGHT)
        assertEquals(0x0010, TouchPadState.XUSB_START); assertEquals(0x0020, TouchPadState.XUSB_BACK)
        assertEquals(0x0100, TouchPadState.XUSB_LEFT_SHOULDER); assertEquals(0x0200, TouchPadState.XUSB_RIGHT_SHOULDER)
        assertEquals(0x1000, TouchPadState.XUSB_A); assertEquals(0x2000, TouchPadState.XUSB_B)
        assertEquals(0x4000, TouchPadState.XUSB_X); assertEquals(0x8000, TouchPadState.XUSB_Y)
    }

    // 10. the stick sign (HM5's stub): above the centre is positive, as the sender stores -AXIS_Y
    @Test
    fun stickSignIsPositiveUp() {
        assertTrue(TouchPadState.stickY(fingerY = 400f, centreY = 500f, radius = 100f) > 0)
        assertEquals(32767.toShort(), TouchPadState.stickY(300f, 500f, 100f))
        assertEquals((-32767).toShort(), TouchPadState.stickY(700f, 500f, 100f))
        assertEquals(0.toShort(), TouchPadState.stickY(500f, 500f, 100f))
    }

    // 11. the video box (G6-SCREEN1: 4:3, was 16:9; G6-HM3's 16:9 stays as videoBoxHeight16x9 and the fallback)
    @Test
    fun videoBoxIsWidthTimesNineSixteenths() {
        assertEquals(675, HandheldGeometry.videoBoxHeight16x9(1200))
        assertEquals(900, HandheldGeometry.videoBoxHeight(1200))
        assertEquals(1100, HandheldGeometry.padRegionHeight(1200, 2000))
        assertEquals(720, HandheldGeometry.videoBoxHeight16x9(1280))
        assertEquals(450, HandheldGeometry.videoBoxHeight16x9(800))
        assertEquals(0, HandheldGeometry.videoBoxHeight(0))
        assertEquals(0, HandheldGeometry.padRegionHeight(1200, 600))
    }

    // 12. the touchscreen-only exemption
    @Test
    fun onlyTheTouchscreenIsExempt() {
        assertTrue(HandheldInput.isTouchscreen(0x00001002))           // touchscreen
        assertTrue(HandheldInput.isTouchscreen(0x00005002))           // stylus with the screen (the S Pen, disclosed)
        assertFalse(HandheldInput.isTouchscreen(0x00002002))          // mouse
        assertFalse(HandheldInput.isTouchscreen(0x00100008))          // touchpad
        assertFalse(HandheldInput.isTouchscreen(0x00020004))          // mouse relative
        assertFalse(HandheldInput.isTouchscreen(0x00200000))          // touch navigation
        assertFalse(HandheldInput.isTouchscreen(0x00000401))          // gamepad
        assertFalse(HandheldInput.isTouchscreen(0x01000010))          // joystick
        assertFalse(HandheldInput.isTouchscreen(0x00004002))          // stylus alone
        // B70's guard still takes every one of the consumed kinds
        for (src in intArrayOf(0x2002, 0x100008, 0x20004, 0x200000)) assertTrue(PointerGuard.isPointerSource(src))
    }

    @Test
    fun beforeLayoutNothingIsHeld() {
        val fresh = TouchPadState()
        assertEquals(TouchPadState.Output(), fresh.down(1, 100f, 100f))
        assertEquals(0, fresh.heldFingers())
    }
}
