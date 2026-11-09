package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.awt.Font
import java.awt.font.FontRenderContext
import java.io.File

/**
 * B73: the paused bar at the onn's density (a 1080p UI: 1920 px at density 2.0 = 960 dp). HOME-10's reading: END
 * "~95 % off" → the TV's visible right edge ≈ 899 dp; Android TV's overscan guideline: 48 dp a side (912 dp).
 */
class B73PausedBarTest {

    private val onnDensity = 2.0f
    private val onnWidthDp = (1920 / onnDensity).toInt()   // 960
    private val home10VisibleEdgeDp = 899
    private val guidelineSafeRightDp = 960 - 48
    private val guidelineSafeLeftDp = 48

    private fun span(spans: List<PausedBar.Span>, name: String) = spans.first { it.name == name }

    @Test
    fun fourButtonsFitTheOnnsScreen() {
        val plan = PausedBar.plan(true, true, onnWidthDp)
        val spans = PausedBar.layout(plan, onnWidthDp)
        for (b in listOf("SAVE", "LOAD", "DISC", "END")) {
            val s = span(spans, b)
            assertTrue("$b left ${s.left}", s.left >= guidelineSafeLeftDp)
            assertTrue("$b right ${s.right}", s.right <= 880)
        }
        val end = span(spans, "END").right
        assertEquals(880, end)
        assertTrue(end < home10VisibleEdgeDp)
        assertTrue(end <= guidelineSafeRightDp)
        val title = span(spans, "title")
        assertTrue("title ${title.right - title.left}", title.right - title.left >= PausedBar.TITLE_MIN_DP)
        assertEquals(232, plan.statusDp)
        assertEquals("DISC", plan.discLabel)
    }

    @Test
    fun b71sBarReproducesHome10() {
        val plan = PausedBar.plan(false, true, onnWidthDp)          // the property off: B71's bar
        assertEquals(150, plan.discDp)
        assertEquals("CHANGE DISC", plan.discLabel)
        val end = span(PausedBar.layout(plan, onnWidthDp), "END")
        assertEquals(998, end.right)                                   // past the 960-dp screen
        assertTrue(end.left < home10VisibleEdgeDp && end.right > onnWidthDp)
        // the visible part of END on the TV: (899 - 894) / 104 ≈ 5 % (the user's "~95 % off")
        val visible = (home10VisibleEdgeDp - end.left).toDouble() / (end.right - end.left)
        assertTrue("visible $visible", visible in 0.0..0.10)
    }

    @Test
    fun oneDiscBarIsTodays() {
        for (fit in listOf(true, false)) {
            val plan = PausedBar.plan(fit, false, onnWidthDp)
            assertEquals(PausedBar.TODAY, plan)
            assertEquals(104, plan.buttonDp)
            assertEquals(8, plan.marginDp)
            assertEquals(280, plan.statusDp)
            assertEquals(20, plan.padEndDp)
            val spans = PausedBar.layout(plan, onnWidthDp)
            assertFalse(spans.any { it.name == "DISC" })
            assertEquals(940, span(spans, "END").right)                // today's three-button bar
        }
    }

    @Test
    fun narrowScreensClampTheStatusText() {
        assertEquals(PausedBar.STATUS_MIN_DP, PausedBar.plan(true, true, 700).statusDp)
        assertEquals(PausedBar.TODAY_STATUS_DP, PausedBar.plan(true, true, 2000).statusDp)
        for (w in 880..960) {
            val end = span(PausedBar.layout(PausedBar.plan(true, true, w), w), "END")
            assertTrue("w $w end ${end.right}", end.right <= w)
        }
    }

    private fun boldFont(px: Float): Font {
        val f = File("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
        val base = if (f.isFile) Font.createFont(Font.TRUETYPE_FONT, f) else Font(Font.SANS_SERIF, Font.BOLD, 1)
        return base.deriveFont(Font.BOLD, px)
    }

    /** A label's width in dp at 13 sp × the onn's density, plus a button's 16-dp padding each side. */
    private fun neededDp(label: String): Double {
        val px = 13f * onnDensity
        val w = boldFont(px).getStringBounds(label, FontRenderContext(null, true, true)).width
        return w / onnDensity + 2 * 16
    }

    @Test
    fun labelsMeasuredAtTheOnnsDensity() {
        for (label in listOf("SAVE", "LOAD", "DISC", "END", "CHANGE DISC")) {
            println("B73 measured: \"$label\" needs %.1f dp (DejaVu Sans Bold 26 px + 2 x 16 dp)".format(neededDp(label)))
        }
        for (label in listOf("SAVE", "LOAD", "DISC", "END")) {
            assertTrue("$label ${neededDp(label)}", neededDp(label) <= PausedBar.FIT_BUTTON_DP)
        }
        assertTrue(neededDp("CHANGE DISC") > PausedBar.FIT_BUTTON_DP)  // why the label is shortened
        assertTrue(neededDp("CHANGE DISC") <= PausedBar.B71_DISC_DP)
    }

    @Test
    fun theProperty() {
        assertTrue(PausedBar.parse(null))
        assertTrue(PausedBar.parse(""))
        assertTrue(PausedBar.parse("1"))
        assertFalse(PausedBar.parse("0"))
        assertFalse(PausedBar.parse(" off "))
    }
}
