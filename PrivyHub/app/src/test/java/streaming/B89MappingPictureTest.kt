package com.safeiot.privyhub.streaming

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.awt.BasicStroke
import java.awt.Color
import java.awt.Font
import java.awt.RenderingHints
import java.awt.geom.Ellipse2D
import java.awt.geom.Path2D
import java.awt.geom.RoundRectangle2D
import java.awt.image.BufferedImage
import java.io.File
import javax.imageio.ImageIO

/** B89: the redrawn picture's one geometry — labels per case, no overlap, the size rule — and its render off the device. */
class B89MappingPictureTest {

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

    private val swap = with("a" to "a", "b" to "b")                    // your Bottom → the game's A, your Right → B
    private val many = with(                                          // a many-button remap
        "a" to "a", "b" to "b",                                       // bottom / right swapped
        "l" to "r", "r" to "l", "l2" to "r2", "r2" to "l2",           // shoulders and triggers swapped side for side
        "select" to "start", "start" to "select",                     // the centre buttons swapped
        "x" to "l3", "l3" to "y",                                     // the game's X from the left stick's press, its L3 from Top
        "up" to "left_stick_up", "left_stick_up" to "up"              // D-pad Up and the stick's Up swapped
    )

    @Test
    fun labelsPerCaseEqualTheMapping() {
        val d = MappingPicture.shortLabels(default)
        assertEquals(listOf("B", "A", "Y", "X"), listOf("a", "b", "x", "y").map { d.getValue(it) })
        assertEquals(listOf("L1", "R1", "L2", "R2", "L3", "R3", "SEL", "START"),
                     listOf("l", "r", "l2", "r2", "l3", "r3", "select", "start").map { d.getValue(it) })
        assertEquals(listOf("↑", "↓", "←", "→"), listOf("up", "down", "left", "right").map { d.getValue(it) })
        val s = MappingPicture.shortLabels(swap)
        assertEquals(listOf("A", "B"), listOf("a", "b").map { s.getValue(it) })
        assertEquals(setOf("a", "b"), MappingPicture.changed(swap, default))
        val m = MappingPicture.shortLabels(many)
        assertEquals("A", m["a"]); assertEquals("B", m["b"])
        assertEquals("R1", m["l"]); assertEquals("L1", m["r"]); assertEquals("R2", m["l2"]); assertEquals("L2", m["r2"])
        assertEquals("START", m["select"]); assertEquals("SEL", m["start"])
        assertEquals("L3", m["y"]); assertEquals("X", m["l3"]); assertEquals("Y", m["x"])
        assertEquals("L↑", m["up"]); assertEquals("↑", m["left_stick_up"])
        assertEquals("A+B", MappingPicture.shortLabels(with("a" to "a", "b" to "a"))["a"])   // two on one control
        // every control's label is what the mapping says it sends (the inverse of the stored {target: source})
        for (case in listOf(default, swap, many)) {
            val labels = MappingPicture.shortLabels(case)
            for ((target, source) in case) assertTrue("$source sends $target", labels.getValue(source).split("+")
                .contains(MappingPicture.shortLabel(target)))
        }
    }

    @Test
    fun noTwoLabelBoxesOverlapAndAllAreInside() {
        val boxes = MappingPicture.BOXES
        for (i in boxes.indices) for (j in i + 1 until boxes.size)
            assertFalse("${boxes[i].id} / ${boxes[j].id}", boxes[i].overlaps(boxes[j]))
        for (b in boxes) assertTrue(b.id, b.x >= 0f && b.y >= 0f && b.x + b.w <= 1f && b.y + b.h <= MappingPicture.ASPECT)
        assertEquals(default.values.toSet(), boxes.map { it.id }.toSet())       // every control the hub lists has a box
        val shapeIds = MappingPicture.SHAPES.mapNotNull {
            when (it) {
                is MappingPicture.Shape.RoundRect -> it.id; is MappingPicture.Shape.Circle -> it.id
                is MappingPicture.Shape.Cross -> it.id; else -> null
            }
        }.toSet()
        assertEquals(setOf("l", "r", "l2", "r2", "a", "b", "x", "y", "select", "start", "l3", "r3", "dpad"), shapeIds)
        assertEquals(1, MappingPicture.SHAPES.count { it is MappingPicture.Shape.Outline })
    }

    @Test
    fun theHeightRule() {
        val (w, h) = MappingPicture.pictureSize(1700, 1080)         // the TV: the dialog's width, the screen's height
        assertTrue("$h", h <= 216)
        assertEquals((h / MappingPicture.ASPECT).toInt(), w)
        val (w2, h2) = MappingPicture.pictureSize(300, 1080)         // a narrow space: never wider than it
        assertTrue(w2 <= 300 && h2 <= 216)
        val (_, h3) = MappingPicture.pictureSize(1000, 600)          // a small screen
        assertTrue(h3 <= 120)
    }

    @Test
    fun theOutlineIsClosedAndSymmetric() {
        val pts = MappingPicture.OUTLINE
        assertTrue(pts.size > 20)
        for ((x, y) in pts) assertTrue("($x, $y)", pts.any { (u, v) -> Math.abs(u - (1f - x)) < 1e-4 && Math.abs(v - y) < 1e-4 })
        assertTrue(pts.all { (x, y) -> x in 0f..1f && y in 0f..MappingPicture.ASPECT })
    }

    @Test
    fun theSvgHoldsEveryLabel() {
        val svg = MappingPicture.svg(many, default)
        for (label in listOf(">A<", ">B<", ">R1<", ">L1<", ">START<", ">SEL<", ">L3<", ">X<")) assertTrue(label, label in svg)
        assertTrue("<polygon" in svg)
        assertEquals(1, Regex("stroke-width=").findAll(svg).count())         // one stroke width for every line
    }

    @Test
    fun theSwitch() {
        assertFalse(MappingPicture.parse("0"))
        assertFalse(MappingPicture.parse("off"))
        assertTrue(MappingPicture.parse(null))
    }

    /** With B89_RENDER_DIR set: the three cases as SVG and PNG (java.awt, headless), the same geometry as the view. */
    @Test
    fun renderOffTheDevice() {
        val dir = System.getenv("B89_RENDER_DIR") ?: return
        System.setProperty("java.awt.headless", "true")
        File(dir).mkdirs()
        for ((name, case) in listOf("default" to default, "swap_bottom_right" to swap, "many_button_remap" to many)) {
            File(dir, "$name.svg").writeText(MappingPicture.svg(case, default))
            File(dir, "$name.png").let { ImageIO.write(png(case, 800), "png", it) }
        }
    }

    private fun png(mapping: Map<String, String>, px: Int): BufferedImage {
        val k = px.toFloat()
        val img = BufferedImage(px, (MappingPicture.ASPECT * k).toInt(), BufferedImage.TYPE_INT_RGB)
        val g = img.createGraphics()
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON)
        g.color = Color(0x1c, 0x1c, 0x1c); g.fillRect(0, 0, img.width, img.height)
        g.color = Color(0xcf, 0xcf, 0xcf)
        g.stroke = BasicStroke(MappingPicture.STROKE * k, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND)
        fun poly(points: List<Pair<Float, Float>>) = Path2D.Float().apply {
            points.forEachIndexed { i, (x, y) -> if (i == 0) moveTo(x * k, y * k) else lineTo(x * k, y * k) }; closePath()
        }
        for (s in MappingPicture.SHAPES) when (s) {
            is MappingPicture.Shape.Outline -> g.draw(poly(s.points))
            is MappingPicture.Shape.RoundRect -> g.draw(RoundRectangle2D.Float(s.x * k, s.y * k, s.w * k, s.h * k, 2 * s.r * k, 2 * s.r * k))
            is MappingPicture.Shape.Circle -> g.draw(Ellipse2D.Float((s.cx - s.r) * k, (s.cy - s.r) * k, 2 * s.r * k, 2 * s.r * k))
            is MappingPicture.Shape.Cross -> g.draw(poly(MappingPicture.crossPath(s)))
        }
        val labels = MappingPicture.shortLabels(mapping)
        val changed = MappingPicture.changed(mapping, default)
        for (b in MappingPicture.BOXES) {
            val text = labels[b.id] ?: continue
            if (b.id.contains("stick") && b.id !in changed) continue
            var size = b.h * k * 0.85f
            var fm = g.getFontMetrics(Font(Font.SANS_SERIF, Font.BOLD, size.toInt().coerceAtLeast(1)))
            while (size > 6f && fm.stringWidth(text) > b.w * k) {
                size *= 0.9f; fm = g.getFontMetrics(Font(Font.SANS_SERIF, Font.BOLD, size.toInt().coerceAtLeast(1)))
            }
            g.font = fm.font
            g.color = if (b.id in changed) Color(0xff, 0xc1, 0x07) else Color.WHITE
            g.drawString(text, b.cx * k - fm.stringWidth(text) / 2f, b.cy * k + (fm.ascent - fm.descent) / 2f)
        }
        g.dispose()
        return img
    }
}
