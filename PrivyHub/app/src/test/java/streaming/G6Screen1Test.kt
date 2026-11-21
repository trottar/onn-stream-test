package com.safeiot.privyhub.streaming

import com.safeiot.privyhub.streaming.TouchPadState.Control
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.abs
import kotlin.math.hypot
import kotlin.math.max

/**
 * G6-SCREEN1: the 4:3 video box (1200 x 900 on the tablet's 1200 x 2000), the crop of the systems proven 4:3, and the
 * pad region 1200 x 1100 with the cluster unchanged on the screen, SELECT / START moved down 225 px and End at x 1080.
 * The figures: `docs/memory/evidence/g6_screen1_2026-11-20/layout_check_screen1.py`.
 */
class G6Screen1Test {

    private val screenW = 1200
    private val screenH = 2000
    private val pxCm = 240.0 / 2.54

    private fun ps2(w: Int, h: Int) = TouchPadState(TouchPadState.Kind.PS2).apply { layout(w, h) }

    // the 4:3 box, the region under it, and the 16:9 fallback where the region would be shorter than its reference
    @Test
    fun theBoxIs4x3OnTheTablet() {
        assertEquals(900, HandheldGeometry.videoBoxHeight(1200))
        assertEquals(900, HandheldGeometry.videoBoxHeight(screenW, screenH))
        assertEquals(1100, HandheldGeometry.padRegionHeight(screenW, screenH))
        assertEquals(1100f, Ps2TouchLayout.REF_H, 0f)
        assertEquals(225f, Ps2TouchLayout.BOX_GROWTH, 0f)
        // a shorter screen of the same width: 4:3 would leave 1020 < 1100, so G6-HM3's 16:9 stays
        assertEquals(675, HandheldGeometry.videoBoxHeight(1200, 1920))
        assertEquals(1245, HandheldGeometry.padRegionHeight(1200, 1920))
        assertEquals(0, HandheldGeometry.videoBoxHeight(0, 2000))
    }

    // every control but SELECT / START at G6-HM4b's on-screen centre (box 675 + region 1325 then; 900 + 1100 now).
    // G6-SWAP1 moved the face diamond and the right stick on purpose (G6Swap1Test pins them); the rest stay here
    @Test
    fun theClusterDoesNotMoveOnTheScreen() {
        val hm4b = mapOf(
            Control.LSTICK to (300f to 1030f), Control.DPAD to (300f to 520f), Control.L3 to (540f to 1040f),
            Control.R3 to (690f to 790f),
            Control.L2 to (56f to 774f), Control.L1 to (170f to 774f), Control.R1 to (1030f to 774f), Control.R2 to (1144f to 774f),
        )
        val now = ps2(screenW, HandheldGeometry.padRegionHeight(screenW, screenH))
        val nowTop = HandheldGeometry.videoBoxHeight(screenW, screenH)
        for ((control, xy) in hm4b) {
            val (x, y) = now.centreOf(control)!!
            assertEquals(control.name, xy.first, x, 0.5f)
            assertEquals(control.name, 675f + xy.second, nowTop + y, 0.5f)              // within 1 px on the screen
        }
        // sizes, radii, throw and hit scales unchanged (sx = sy = 1 on the tablet)
        val d = now.drawn().associateBy { it.control }
        assertEquals(115.5f, d.getValue(Control.LSTICK).halfW, 1e-3f)
        assertEquals(158.4f, d.getValue(Control.RSTICK).hitHalfW, 1e-3f)
        assertEquals(125f * 1.25f, d.getValue(Control.DPAD).hitHalfW, 1e-3f)
        assertEquals(50f, d.getValue(Control.R1).halfW, 0f); assertEquals(100f, d.getValue(Control.R1).halfH, 0f)
        assertEquals(52f, d.getValue(Control.CROSS).halfW, 0f)
    }

    // SELECT and START at y 70 of the region: 225 px lower on the screen, same x and size
    @Test
    fun selectAndStartMoveDownWithTheBox() {
        val now = ps2(screenW, 1100)
        assertEquals(400f to 70f, now.centreOf(Control.SELECT))
        assertEquals(600f to 70f, now.centreOf(Control.START))
        val top = HandheldGeometry.videoBoxHeight(screenW, screenH)
        assertEquals(970f, top + now.centreOf(Control.SELECT)!!.second, 0f)            // on screen: 970 (G6-HM4b: 745)
        assertEquals(970f, top + now.centreOf(Control.START)!!.second, 0f)
        val sel = now.drawn().first { it.control == Control.SELECT }
        assertEquals(75.5f, sel.halfW, 0f); assertEquals(47.5f, sel.halfH, 0f)
    }

    // End at x 1080: the smallest whole x with >= 0.5 cm to the right stick's press area; inside, clear of R1 / R2
    @Test
    fun endMovesRightTo1080() {
        val now = ps2(screenW, 1100)
        assertEquals(1080f, Ps2TouchLayout.END_X, 0f)
        val e = now.endRect(screenW, 1100)
        assertEquals(listOf(1004.5f, 22.5f, 1155.5f, 117.5f), e.toList())
        // End's x was chosen against the right stick at its G6-SCREEN1 place (900, 295); G6-SWAP1 moved the stick away
        // (G6Swap1Test checks End's clearance in the new layout)
        val (rx, ry) = 900f to 295f
        fun gap(left: Double, bottom: Double) = hypot(max(left - rx, 0.0), max(ry - bottom, 0.0)) - Ps2TouchLayout.STICK_PRESS_R
        assertTrue(gap(e[0].toDouble(), e[3].toDouble()) >= 0.5 * pxCm)                 // 47.6 px at 1080
        assertFalse(gap(1079.0 - 75.5, 117.5) >= 0.5 * pxCm)                            // 1079 is too near
        assertTrue(e[2] <= screenW)
        val r1 = now.drawn().first { it.control == Control.R1 }
        assertTrue(e[3] < r1.cy - r1.hitHalfH)
        // nothing of the pad claims End's rectangle
        assertEquals(null, now.controlAt((e[0] + e[2]) / 2, (e[1] + e[3]) / 2))
        assertEquals(null, now.controlAt(e[0] + 2f, e[3] - 2f))
    }

    // the crop: only the systems proven 4:3, by the catalog entry's system id; any other or none is not cropped
    @Test
    fun theCropDecisionPerSystem() {
        assertEquals(setOf("snes", "n64"), HandheldGeometry.CROP_4X3_SYSTEMS)
        for (sys in listOf("snes", "n64", "SNES", " n64 ")) assertTrue(sys, HandheldGeometry.crop43(sys, 1200, 900))
        for (sys in listOf("ps2", "ps1", "gamecube", "party", "nes", "genesis", "", "unknown", null))
            assertFalse("$sys", HandheldGeometry.crop43(sys, 1200, 900))
        // the 16:9 fallback box never crops
        assertFalse(HandheldGeometry.crop43("snes", 1200, 675))
        assertFalse(HandheldGeometry.crop43("snes", 0, 0))
        assertEquals("4:3", HandheldGeometry.videoCrop(true))
        assertEquals("none", HandheldGeometry.videoCrop(false))
    }

    // the shown rectangle of the stream and the surface's place in the box
    @Test
    fun theSourceRectangleAndTheSurface() {
        assertEquals("160,0,960x720", HandheldGeometry.videoSourceRect(true))
        assertEquals("0,0,1280x720", HandheldGeometry.videoSourceRect(false))
        assertEquals("240,0,1440x1080", HandheldGeometry.videoSourceRect(true, 1920, 1080))
        assertArrayEquals(intArrayOf(-200, 0, 1600, 900), HandheldGeometry.surfaceRect(1200, 900, true))
        assertArrayEquals(intArrayOf(0, 0, 1200, 675), HandheldGeometry.surfaceRect(1200, 900, false))
        // cropped: the box shows exactly the stream's centre 4:3 (1200 of 1600 = 960 of 1280)
        val r = HandheldGeometry.surfaceRect(1200, 900, true)
        assertEquals(960.0, 1200.0 / r[2] * 1280, 1e-9)
        assertEquals(160.0, -r[0].toDouble() / r[2] * 1280, 1e-9)
    }

    // no press area overlaps another, End included, in the new region
    @Test
    fun noPressAreaOverlapsInTheNewRegion() {
        val now = ps2(screenW, 1100)
        data class Hit(val n: String, val circle: Boolean, val x: Double, val y: Double, val a: Double, val b: Double)
        val hits = now.drawn().map { Hit(it.control.name, it.halfH == 0f, it.cx.toDouble(), it.cy.toDouble(), it.hitHalfW.toDouble(),
            if (it.halfH == 0f) it.hitHalfW.toDouble() else it.hitHalfH.toDouble()) } +
            Hit("END", false, 1080.0, 70.0, 75.5, 47.5)
        fun overlap(p: Hit, q: Hit): Boolean = when {
            p.circle && q.circle -> hypot(p.x - q.x, p.y - q.y) < p.a + q.a
            !p.circle && !q.circle -> abs(p.x - q.x) < p.a + q.a && abs(p.y - q.y) < p.b + q.b
            else -> {
                val (ci, re) = if (p.circle) p to q else q to p
                hypot(max(abs(ci.x - re.x) - re.a, 0.0), max(abs(ci.y - re.y) - re.b, 0.0)) < ci.a
            }
        }
        for (i in hits.indices) for (j in i + 1 until hits.size)
            assertFalse("${hits[i].n} / ${hits[j].n}", overlap(hits[i], hits[j]))
    }
}
