package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.awt.BasicStroke
import java.awt.Color
import java.awt.Font
import java.awt.Graphics2D
import java.awt.RenderingHints
import java.awt.geom.Ellipse2D
import java.awt.geom.Line2D
import java.awt.geom.Path2D
import java.awt.geom.RoundRectangle2D
import java.awt.image.BufferedImage
import java.io.File
import javax.imageio.ImageIO

/** B91: the picture beside the rows, its labels at the rows' text size, no overlap — and the whole editor rendered at
 *  1920 × 1080 off the device (the same model and placement the view uses). */
class B91MappingBesideTest {

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

    private val swap = with("a" to "a", "b" to "b")                      // B89's cases, unchanged
    private val many = with(
        "a" to "a", "b" to "b", "l" to "r", "r" to "l", "l2" to "r2", "r2" to "l2",
        "select" to "start", "start" to "select", "x" to "l3", "l3" to "y",
        "up" to "left_stick_up", "left_stick_up" to "up"
    )
    private val cases = listOf("default" to default, "swap_bottom_right" to swap, "many_button_remap" to many)

    private val tv = MappingEditorLayout.plan(1920, 1080, 2.0f)            // the onn: the 1080p TV norm (density 2.0)

    private val font: (Float) -> Font = { px -> Font("DejaVu Sans", Font.PLAIN, 1).deriveFont(px) }
    private val g0: Graphics2D = BufferedImage(1, 1, BufferedImage.TYPE_INT_RGB).createGraphics()
    private fun awtMeasure(px: Float): (String) -> Float = { t -> g0.getFontMetrics(font(px)).stringWidth(t).toFloat() }
    private fun wideMeasure(px: Float): (String) -> Float = { t -> 0.75f * px * t.length }   // a wider bound than any font

    private fun assertNoOverlap(name: String, placed: List<MappingPicture.Placed>, w: Float, h: Float) {
        for (i in placed.indices) for (j in i + 1 until placed.size)
            assertFalse("$name: ${placed[i].id} / ${placed[j].id}", placed[i].box.overlaps(placed[j].box))
        for (p in placed) assertTrue("$name: ${p.id} inside", p.box.x >= 0f && p.box.y >= 0f &&
                                     p.box.x + p.box.w <= w && p.box.y + p.box.h <= h)
    }

    @Test
    fun labelTextIsNeverSmallerThanTheRows() {
        assertTrue(MappingEditorLayout.LABEL_TEXT_SP >= MappingEditorLayout.ROW_TEXT_SP)
        assertEquals(34f, tv.rowTextPx, 0.01f)
        assertTrue(tv.labelTextPx >= tv.rowTextPx)
        val uhd = MappingEditorLayout.plan(3840, 2160, 4.0f)
        assertTrue(uhd.labelTextPx >= uhd.rowTextPx)
        // B89's largest label at 1080p (a face button's box) for the record's comparison: ≤ 11 px
        val (b89W, _) = MappingPicture.pictureSize(tv.contentW, 1080)
        val b89Face = MappingPicture.BOXES.first { it.id == "a" }.h * b89W * 0.85f
        assertTrue("$b89Face", b89Face <= 11f)
        assertTrue(tv.labelTextPx >= 3 * b89Face)
    }

    @Test
    fun noTwoLabelBoxesOverlapInTheThreeCasesAndTheWorstCase() {
        val w = tv.pictureW.toFloat(); val h = tv.pictureH.toFloat()
        // the rows' size (java.awt's widths and a wider bound), and Android's font size set 1.3x larger (sp grows, the
        // picture does not; java.awt's widths — with the wider bound too, the worst case leaves 4 of 24 labels out)
        val runs = listOf(tv.labelTextPx to awtMeasure(tv.labelTextPx), tv.labelTextPx to wideMeasure(tv.labelTextPx),
                          1.3f * tv.labelTextPx to awtMeasure(1.3f * tv.labelTextPx))
        for ((t, measure) in runs) {
            for ((name, case) in cases) {
                val placed = MappingPicture.placeLabels(w, h, t, case, default, measure)
                assertNoOverlap(name, placed, w, h)
                val drawn = MappingPicture.shortLabels(case).keys.filter {
                    !(it.contains("stick") && it !in MappingPicture.changed(case, default))
                }
                assertEquals(name, drawn.toSet(), placed.map { it.id }.toSet())      // every label placed
            }
            // the worst case: all 24 controls (the stick directions too) labelled with the longest label
            val all = MappingPicture.BOXES.map { it.id }
            val worst = MappingPicture.placeLabelTexts(w, h, t, all.associateWith { "START" }, all.toSet(), measure)
            assertNoOverlap("worst", worst, w, h)
            assertEquals(all.toSet(), worst.map { it.id }.toSet())
        }
    }

    @Test
    fun aLeaderExactlyWhenALabelMoved() {
        val w = tv.pictureW.toFloat(); val h = tv.pictureH.toFloat(); val t = tv.labelTextPx
        val k = MappingPicture.besideScale(w)
        for ((name, case) in cases) for (p in MappingPicture.placeLabels(w, h, t, case, default, awtMeasure(t))) {
            val atAnchor = Math.abs(p.box.cx - p.ax) < 0.01f && Math.abs(p.box.cy - p.ay) < 0.01f
            assertEquals("$name ${p.id}", !atAnchor, p.leader)
            val (u, v) = MappingPicture.ANCHORS.getValue(p.id)
            assertEquals(MappingPicture.besideLeft(w) + u * k, p.ax, 0.01f)
            assertEquals(MappingPicture.besideTop(w) + v * k, p.ay, 0.01f)
        }
        val d = MappingPicture.placeLabels(w, h, t, default, default, awtMeasure(t)).associateBy { it.id }
        for (id in listOf("a", "b", "x", "y", "l", "r", "l2", "r2")) assertFalse(id, d.getValue(id).leader)
    }

    @Test
    fun theRowsStayInViewAndThePictureNeverScrollsAway() {
        assertTrue(tv.beside)
        assertTrue(tv.pictureOutsideScroll)
        assertTrue("${tv.rowsVisibleBeside} vs ${tv.rowsVisibleToday}", tv.rowsVisibleBeside >= tv.rowsVisibleToday)
        assertTrue(tv.rowsVisibleBeside >= 1)
        assertTrue(tv.pictureW <= tv.leftW && tv.pictureH + MappingEditorLayout.legendPx(2f) <= tv.contentH)
        assertTrue(tv.leftW + MappingEditorLayout.GAP_PX + tv.rightW <= tv.contentW)
        val tall = MappingEditorLayout.plan(1080, 1920, 2.0f)                  // not the onn: the picture stays above
        assertFalse(tall.beside)
    }

    @Test
    fun theSwitch() {
        assertFalse(MappingPicture.parse("0"))
        assertFalse(MappingPicture.parse("off"))
        assertTrue(MappingPicture.parse(null))
        assertTrue(MappingPicture.parse(""))
    }

    /** With B91_RENDER_DIR set: the whole editor at 1920 × 1080 for the three cases (PNG), and the numbers. */
    @Test
    fun renderTheWholeEditorOffTheDevice() {
        val dir = System.getenv("B91_RENDER_DIR") ?: return
        System.setProperty("java.awt.headless", "true")
        File(dir).mkdirs()
        for ((name, case) in cases) ImageIO.write(screen(case), "png", File(dir, "$name.png"))
        val placed = cases.associate { (n, c) ->
            n to MappingPicture.placeLabels(tv.pictureW.toFloat(), tv.pictureH.toFloat(), tv.labelTextPx, c, default,
                                            awtMeasure(tv.labelTextPx)) }
        val fm = g0.getFontMetrics(font(tv.labelTextPx))
        File(dir, "numbers.txt").writeText(buildString {
            appendLine("plan at 1920x1080, density 2.0: $tv")
            appendLine("label text size px: ${tv.labelTextPx}; rows' text size px: ${tv.rowTextPx}")
            appendLine("label text height px (DejaVu Sans ascent+descent at that size): ${fm.ascent + fm.descent}; " +
                       "a capital's height ~ ${(0.73f * tv.labelTextPx)}")
            for ((n, p) in placed) appendLine("$n: ${p.size} labels, moved with a leader: ${p.filter { it.leader }.map { it.id }}")
        })
    }

    private fun screen(mapping: Map<String, String>): BufferedImage {
        val d = 2.0f
        val img = BufferedImage(1920, 1080, BufferedImage.TYPE_INT_RGB)
        val g = img.createGraphics()
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON)
        g.color = Color(0x0b, 0x0d, 0x10); g.fillRect(0, 0, 1920, 1080)                 // the app behind, dimmed
        val dx = (1920 - tv.dialogW) / 2; val dy = (1080 - tv.dialogH) / 2
        g.color = Color(0x2d, 0x2d, 0x30); g.fillRoundRect(dx, dy, tv.dialogW, tv.dialogH, 16, 16)
        fun text(s: String, x: Float, y: Float, sp: Float, c: Color = Color(0xee, 0xee, 0xee), bold: Boolean = false) {
            g.font = Font("DejaVu Sans", if (bold) Font.BOLD else Font.PLAIN, 1).deriveFont(sp * d)
            g.color = c; g.drawString(s, x, y + g.fontMetrics.ascent)
        }
        text("Made Up Profile - Player 1", dx + 24f * d, dy + 18f * d, 20f)              // the dialog's title
        val cx = dx + MappingEditorLayout.PAD_H.toFloat()
        val cy = dy + MappingEditorLayout.TITLE_DP * d + MappingEditorLayout.PAD_V
        // the left pane: the picture and its legend
        drawPicture(g, mapping, cx, cy)
        var ly = cy + tv.pictureH + 4
        for (line in wrap(MappingPicture.LEGEND, tv.leftW.toFloat(), MappingEditorLayout.LEGEND_SP * d)) {
            text(line, cx + 8, ly, MappingEditorLayout.LEGEND_SP, Color(0xbb, 0xbb, 0xbb)); ly += 1.17f * MappingEditorLayout.LEGEND_SP * d
        }
        // the right pane: the heading, the status, the copy button, the rows — clipped where the scroll's view ends
        val rx = cx + tv.leftW + MappingEditorLayout.GAP_PX
        val bottom = cy + tv.contentH
        val clip = g.clip
        g.clipRect(rx.toInt(), cy.toInt(), tv.rightW, tv.contentH)
        var y = cy
        text("Current mapping", rx + 8, y + 8, MappingEditorLayout.HEADING_SP); y += 1.17f * 18f * d + 16
        text("Tap Change for the control you want to update.", rx + 8, y, MappingEditorLayout.STATUS_SP); y += 1.17f * 14f * d + 20
        button(g, "Copy Mapping From Another Player", rx, y, tv.rightW.toFloat(), d); y += 48f * d
        val changed = MappingPicture.changed(mapping, default)
        for ((target, source) in mapping) {
            if (y > bottom) break
            val c = if (source in changed) Color(0xff, 0xc1, 0x07) else Color(0xee, 0xee, 0xee)
            text(MappingPicture.rowText(target, source), rx + 8, y + 8, MappingEditorLayout.ROW_TEXT_SP, c)
            y += 8 + 1.17f * MappingEditorLayout.ROW_TEXT_SP * d
            button(g, "Change", rx + 8, y, tv.rightW - 16f, d); y += 48f * d + 20
        }
        g.clip = clip
        // the button bar
        val by = dy + tv.dialogH - MappingEditorLayout.BUTTON_BAR_DP * d + 16
        text("CANCEL", dx + tv.dialogW - 300f, by, 15f, Color(0x80, 0xcb, 0xc4), true)
        text("SAVE", dx + tv.dialogW - 130f, by, 15f, Color(0x80, 0xcb, 0xc4), true)
        g.dispose()
        return img
    }

    private fun button(g: Graphics2D, label: String, x: Float, y: Float, w: Float, d: Float) {
        g.color = Color(0x45, 0x45, 0x4a); g.fill(RoundRectangle2D.Float(x, y + 4, w, 48f * d - 8, 8f, 8f))
        g.font = Font("DejaVu Sans", Font.PLAIN, 1).deriveFont(14f * d); g.color = Color(0xee, 0xee, 0xee)
        val fm = g.fontMetrics
        g.drawString(label, x + (w - fm.stringWidth(label)) / 2, y + 24f * d + (fm.ascent - fm.descent) / 2f)
    }

    private fun wrap(s: String, width: Float, px: Float): List<String> {
        val fm = g0.getFontMetrics(font(px)); val out = mutableListOf<String>(); var line = ""
        for (word in s.split(" ")) {
            val next = if (line.isEmpty()) word else "$line $word"
            if (fm.stringWidth(next) > width - 16 && line.isNotEmpty()) { out += line; line = word } else line = next
        }
        if (line.isNotEmpty()) out += line
        return out
    }

    private fun drawPicture(g: Graphics2D, mapping: Map<String, String>, x0: Float, y0: Float) {
        val w = tv.pictureW.toFloat(); val h = tv.pictureH.toFloat(); val t = tv.labelTextPx
        val k = MappingPicture.besideScale(w); val ox = x0 + MappingPicture.besideLeft(w); val oy = y0 + MappingPicture.besideTop(w)
        g.color = Color(0xcf, 0xcf, 0xcf)
        g.stroke = BasicStroke(MappingPicture.STROKE * k, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND)
        fun poly(points: List<Pair<Float, Float>>) = Path2D.Float().apply {
            points.forEachIndexed { i, (x, y) -> if (i == 0) moveTo(ox + x * k, oy + y * k) else lineTo(ox + x * k, oy + y * k) }
            closePath()
        }
        for (s in MappingPicture.SHAPES) when (s) {
            is MappingPicture.Shape.Outline -> g.draw(poly(s.points))
            is MappingPicture.Shape.RoundRect -> g.draw(RoundRectangle2D.Float(ox + s.x * k, oy + s.y * k, s.w * k, s.h * k, 2 * s.r * k, 2 * s.r * k))
            is MappingPicture.Shape.Circle -> g.draw(Ellipse2D.Float(ox + (s.cx - s.r) * k, oy + (s.cy - s.r) * k, 2 * s.r * k, 2 * s.r * k))
            is MappingPicture.Shape.Cross -> g.draw(poly(MappingPicture.crossPath(s)))
        }
        g.font = font(t)
        val fm = g.fontMetrics
        g.stroke = BasicStroke(MappingPicture.STROKE * k * 0.6f)
        for (p in MappingPicture.placeLabels(w, h, t, mapping, default, awtMeasure(t))) {
            g.color = if (p.changed) Color(0xff, 0xc1, 0x07) else Color.WHITE
            if (p.leader) {
                val (ex, ey) = MappingPicture.nearest(p.box, p.ax, p.ay)
                g.draw(Line2D.Float(x0 + p.ax, y0 + p.ay, x0 + ex, y0 + ey))
            }
            g.drawString(p.text, x0 + p.box.cx - fm.stringWidth(p.text) / 2f, y0 + p.box.cy + (fm.ascent - fm.descent) / 2f)
        }
    }
}
