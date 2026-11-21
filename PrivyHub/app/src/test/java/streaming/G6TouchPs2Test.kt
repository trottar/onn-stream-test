package com.safeiot.privyhub.streaming

import com.safeiot.privyhub.streaming.TouchPadState.Control
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import kotlin.math.abs
import kotlin.math.hypot
import kotlin.math.max

/**
 * G6-HM4: the PS2 touch layout (the amendment G6-HM1a; the shoulders as addendum B2, settled by the ergonomics chat)
 * on the tablet's pad region, the sticks, L3 / R3, and the main app's 2-column rule.
 * B2's numbers are `docs/memory/evidence/g6_hm1a_2026-11-19/layout_check_b.py`'s, exactly.
 * G6-SCREEN1: the region is 1200 x 1100 under the 4:3 box; every y but SELECT / START's is B2's minus 225 (the same
 * place on the screen), End at x 1080 (`G6Screen1Test` pins the on-screen places against G6-HM4b's).
 */
class G6TouchPs2Test {

    private val W = 1200
    private val H = 1100                                    // G6-SCREEN1 (G6-HM4: 1325)
    private lateinit var s: TouchPadState

    @Before
    fun setUp() {
        s = TouchPadState(TouchPadState.Kind.PS2).apply { layout(W, H) }
    }

    private fun c(control: Control) = s.centreOf(control)!!
    private val MAX = 32767.toShort()
    private val MIN = (-32767).toShort()

    // B2's centres, exactly as layout_check_b.py; G6-SCREEN1: each y but SELECT / START's 225 less
    @Test
    fun theLayoutIsAddendumB2() {
        val b2 = mapOf(
            Control.LSTICK to (300f to 805f), Control.DPAD to (300f to 295f), Control.L3 to (540f to 815f),
            // G6-SWAP1: the face diamond and the right stick trade places (G6-SCREEN1: △ 715, ○ / □ 805, ✕ 895, RS 295)
            Control.TRIANGLE to (900f to 205f), Control.CIRCLE to (990f to 295f), Control.CROSS to (900f to 385f),
            Control.SQUARE to (810f to 295f), Control.RSTICK to (900f to 805f), Control.R3 to (690f to 565f),
            Control.SELECT to (400f to 70f), Control.START to (600f to 70f),
            Control.L2 to (56f to 549f), Control.L1 to (170f to 549f), Control.R1 to (1030f to 549f), Control.R2 to (1144f to 549f),
        )
        assertEquals(15, s.drawn().size)
        for ((control, xy) in b2) assertEquals(control.name, xy, c(control))
        val e = s.endRect(W, H)
        assertEquals(listOf(1004.5f, 22.5f, 1155.5f, 117.5f), e.toList())   // G6-SCREEN1: End at (1080, 70), 151 x 95
    }

    // each stick's four directions and the sign (up and right positive; the sender stores -AXIS_Y)
    // G6-HM4b: at the new radius (0.875 x G6-HM4's 132 px = 115.5 px)
    @Test
    fun eachStickHasFourDirectionsWithTheSendersSign() {
        val r = Ps2TouchLayout.STICK_R
        val (lx, ly) = c(Control.LSTICK)
        s.down(1, lx, ly)
        assertEquals(MAX, s.move(1, lx, ly - r).ly); assertEquals(0.toShort(), s.output().lx)
        assertEquals(MIN, s.move(1, lx, ly + r).ly)
        assertEquals(MIN, s.move(1, lx - r, ly).lx); assertEquals(0.toShort(), s.output().ly)
        assertEquals(MAX, s.move(1, lx + r, ly).lx)
        s.up(1)
        val (rx, ry) = c(Control.RSTICK)
        s.down(2, rx, ry)
        assertEquals(MAX, s.move(2, rx, ry - r).ry)
        assertEquals(MIN, s.move(2, rx, ry + r).ry)
        assertEquals(MIN, s.move(2, rx - r, ry).rx)
        val right = s.move(2, rx + r, ry)
        assertEquals(MAX, right.rx); assertEquals(0.toShort(), right.lx); assertEquals(0.toShort(), right.ly)
        assertEquals(TouchPadState.Output(), s.up(2))
        // the same sign as G6-HM2's stub
        assertTrue(TouchPadState.stickY(ly - 50f, ly, r) > 0 && s.down(3, lx, ly - 50f).ly > 0)
    }

    @Test
    fun theClampAndTheDeadZone() {
        val r = Ps2TouchLayout.STICK_R                                           // G6-HM4b: the new radius
        val (lx, ly) = c(Control.LSTICK)
        s.down(1, lx, ly)
        assertEquals(MAX, s.move(1, lx + 3 * r, ly).lx)                         // clamped at 1
        val diag = s.move(1, lx + 3 * r, ly - 3 * r)
        // G6-STICK1: the DualShock 2 square: a full diagonal is full on both axes (G6-HM4: the unit circle, 23170 each)
        assertEquals(MAX, diag.lx); assertEquals(MAX, diag.ly)
        assertEquals(TouchPadState.Output(), s.move(1, lx + 0.09f * r, ly))     // inside 0.1 r
        assertTrue(s.move(1, lx + 0.11f * r, ly).lx > 0)                         // just outside
        assertEquals(0f to 0f, TouchPadState.stickVector(5f, 5f, r))
        assertEquals(1f, TouchPadState.stickVector(1000f, 0f, r).first, 1e-6f)
    }

    @Test
    fun aStickAndAButtonTogether() {
        val (lx, ly) = c(Control.LSTICK)
        val (cx, cy) = c(Control.CROSS)
        s.down(1, lx, ly)
        s.move(1, lx, ly - 132f)
        val both = s.down(2, cx, cy)
        assertEquals(TouchPadState.XUSB_A, both.buttons)
        assertEquals(MAX, both.ly)
        assertEquals(setOf(Control.LSTICK, Control.CROSS), s.heldControls())
        assertEquals(0, s.up(2).buttons); assertEquals(MAX, s.output().ly)
    }

    @Test
    fun aStickFingerLeavingItsBaseKeepsTheStick() {
        val (lx, ly) = c(Control.LSTICK)
        s.down(1, lx, ly)
        assertEquals(MAX, s.move(1, lx + 600f, ly).lx)                            // far outside its press area
        val (cx, cy) = c(Control.CROSS)
        val onCross = s.move(1, cx, cy)                                          // over the Cross button: still the stick
        assertEquals(0, onCross.buttons)
        assertTrue(onCross.lx > 0)
        assertEquals(TouchPadState.Output(), s.up(1))
    }

    // G6-HM4b: full deflection at 0.875 x the old radius; the press area unchanged
    @Test
    fun fullDeflectionAt0875OfTheOldRadius() {
        assertEquals(0.875f, Ps2TouchLayout.STICK_THROW, 0f)
        assertEquals(115.5f, Ps2TouchLayout.STICK_R, 1e-4f)
        assertEquals(158.4f, Ps2TouchLayout.STICK_PRESS_R, 1e-3f)
        val (lx, ly) = c(Control.LSTICK)
        s.down(1, lx, ly)
        assertEquals(MAX, s.move(1, lx + 0.875f * 132f, ly).lx)                  // full at 115.5 px
        // G6-STICK1: half of the throw is (0.5 - 0.1) / 0.65 end to end (G6-HM4b: half sent, 16384); 91 % of it is now
        // full (>= 0.75)
        val g6hm4Half = s.move(1, lx + 0.5f * 0.875f * 132f, ly).lx                // half of the new throw
        assertEquals(0.4 / 0.65, Ds2Stick.endToEnd(g6hm4Half).toDouble(), 1.0 / 128)
        assertEquals(MAX, s.move(1, lx + 0.8f * 132f, ly).lx)                     // G6-HM4's 80 % = 91 % of the throw
        s.up(1)
        // a touch 150 px from the centre (outside the new ring, inside the unchanged 158.4 px press area) lands on it
        assertEquals(Control.LSTICK, s.controlAt(lx - 150f, ly))
        assertEquals(Control.RSTICK, c(Control.RSTICK).let { (x, y) -> s.controlAt(x, y - 150f) })
    }

    @Test
    fun l3AndR3BitsArePinned() {
        assertEquals(0x0040, TouchPadState.XUSB_LEFT_THUMB)
        assertEquals(0x0080, TouchPadState.XUSB_RIGHT_THUMB)
        assertEquals(0x0040, c(Control.L3).let { (x, y) -> s.down(1, x, y) }.buttons)
        assertEquals(0x0040 or 0x0080, c(Control.R3).let { (x, y) -> s.down(2, x, y) }.buttons)
        assertEquals(0, s.cancel().buttons)
    }

    // B2's checks, as layout_check_b.py: no overlap (End included), the bottom tenth, the sizes
    @Test
    fun b2HasNoOverlapAndTheMinimumSizes() {
        val pxCm = 240.0 / 2.54
        data class Hit(val name: String, val circle: Boolean, val x: Double, val y: Double, val a: Double, val b: Double)
        val hits = s.drawn().map { Hit(it.control.name, it.halfH == 0f, it.cx.toDouble(), it.cy.toDouble(), it.hitHalfW.toDouble(),
            if (it.halfH == 0f) it.hitHalfW.toDouble() else it.hitHalfH.toDouble()) } +
            Hit("END", false, 1080.0, 70.0, 75.5 * 1.2, 47.5 * 1.2)
        fun overlap(p: Hit, q: Hit): Boolean = when {
            p.circle && q.circle -> hypot(p.x - q.x, p.y - q.y) < p.a + q.a
            !p.circle && !q.circle -> abs(p.x - q.x) < p.a + q.a && abs(p.y - q.y) < p.b + q.b
            else -> {
                val (ci, re) = if (p.circle) p to q else q to p
                hypot(max(abs(ci.x - re.x) - re.a, 0.0), max(abs(ci.y - re.y) - re.b, 0.0)) < ci.a
            }
        }
        for (i in hits.indices) for (j in i + 1 until hits.size)
            assertFalse("${hits[i].name} / ${hits[j].name}", overlap(hits[i], hits[j]))
        val bottom = 0.9 * H
        for (h in hits) {
            assertTrue(h.name, h.x - h.a >= 0 && h.x + h.a <= W && h.y - h.b >= 0 && h.y + h.b <= bottom)
            if (h.name in setOf("L1", "L2", "R1", "R2")) assertTrue(h.name, h.y + h.b <= bottom - pxCm)
        }
        for (d in s.drawn()) {
            val wCm = 2 * d.halfW / pxCm
            val hCm = (if (d.halfH == 0f) 2 * d.halfW else 2 * d.halfH) / pxCm
            assertTrue(d.control.name, minOf(wCm, hCm) >= 1.0)
            if (d.control in setOf(Control.L1, Control.L2, Control.R1, Control.R2)) assertTrue(d.control.name, hCm >= 2.0)
            if (d.control == Control.DPAD) assertTrue(d.control.name, wCm >= 2.5)
            // G6-HM4b: the sticks' drawn ring is 0.875 x G6-HM4's (2.44 cm at 240 dpi, under the amendment's 2.5 cm,
            // kept at the user's request); their press area is unchanged and exceeds 2.5 cm
            if (d.control == Control.LSTICK || d.control == Control.RSTICK) {
                assertEquals(115.5f, d.halfW, 1e-3f)
                assertTrue(d.control.name, 2 * d.hitHalfW / pxCm >= 2.5)
            }
        }
    }

    // all 16 controls reachable by a press at their centre (End is its own view: no pad control claims its centre)
    @Test
    fun all16ControlsAreReachableAtTheirCentres() {
        val pad = Control.values().toList()
        assertEquals(15, pad.size)
        for (control in pad) {
            val (x, y) = c(control)
            assertEquals(control.name, control, s.controlAt(x, y))
        }
        val e = s.endRect(W, H)
        assertNull(s.controlAt((e[0] + e[2]) / 2, (e[1] + e[3]) / 2))
        assertNull(s.controlAt(e[0] + 2f, e[1] + 2f))
        assertNull(s.controlAt(e[2] - 2f, e[3] - 2f))
    }

    @Test
    fun theLayoutScalesWithTheMeasuredSize() {
        val t = TouchPadState(TouchPadState.Kind.PS2).apply { layout(600, 550) }
        val (x, y) = t.centreOf(Control.L1)!!
        assertEquals(85f, x, 0.01f); assertEquals(549f * 550 / 1100, y, 0.01f)
    }

    @Test
    fun ps1RemainsTheDefaultAndHasNoSticks() {
        val t = TouchPadState().apply { layout(W, H) }
        assertNull(t.centreOf(Control.LSTICK)); assertNull(t.centreOf(Control.L3))
        assertEquals(11, t.drawn().size)
    }

    // the main app's 2-column rule (Q-B4 (a))
    @Test
    fun theCatalogUsesTwoColumnsOnlyUprightInHandheldMode() {
        assertEquals(2, HandheldGeometry.catalogColumns(handheld = true, touchscreen = true, widthDp = 800, tvGuideList = false))
        assertEquals(3, HandheldGeometry.catalogColumns(handheld = true, touchscreen = true, widthDp = 960, tvGuideList = false))
        assertEquals(3, HandheldGeometry.catalogColumns(handheld = true, touchscreen = true, widthDp = 1333, tvGuideList = false))
        assertEquals(3, HandheldGeometry.catalogColumns(handheld = false, touchscreen = true, widthDp = 800, tvGuideList = false))
        assertEquals(3, HandheldGeometry.catalogColumns(handheld = true, touchscreen = false, widthDp = 800, tvGuideList = false))
        // the onn: no handheld choice, no touchscreen, 960 dp
        assertEquals(3, HandheldGeometry.catalogColumns(handheld = false, touchscreen = false, widthDp = 960, tvGuideList = false))
        assertEquals(1, HandheldGeometry.catalogColumns(handheld = true, touchscreen = true, widthDp = 800, tvGuideList = true))
        assertEquals(1, HandheldGeometry.catalogColumns(handheld = false, touchscreen = false, widthDp = 960, tvGuideList = true))
        assertEquals(960, HandheldGeometry.CATALOG_FULL_WIDTH_DP)
    }
}
