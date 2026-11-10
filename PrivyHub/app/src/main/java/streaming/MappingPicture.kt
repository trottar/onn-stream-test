package com.safeiot.privyhub.streaming

/**
 * B86: the Input Profile editor in one set of letters, with a small controller picture.
 *
 * A mapping is stored as `{target: source}`: the target is the button the game receives (RetroArch's RetroPad names,
 * Nintendo layout: b bottom, a right, y left, x top), the source is your pad's button (Xbox names: a bottom, b right,
 * x left, y top). The editor used to print both as bare letters, so the hub's default (a ← b, b ← a, …: the identity by
 * position) read as a swap. Here your pad's buttons are named by position and glyph and the game's by its letter:
 * "Bottom (✕) → B". The picture shows, on each of your pad's controls, what it sends now; changed ones highlighted.
 * A display change only: the stored mapping is never touched. `debug.privyhub.mapping_picture=0` = today's editor.
 * Design: docs/memory/evidence/b86_2026-11-10/design_written_before_code.md (hashed before this code).
 */
object MappingPicture {
    const val PROPERTY = "debug.privyhub.mapping_picture"
    const val LEGEND = "The picture shows what each of your pad's buttons sends to the game. " +
        "A, B, X, Y are the game's buttons: B bottom, A right, Y left, X top."
    const val NOTHING = "—"

    private val PAD = mapOf(
        "a" to "Bottom (✕)", "b" to "Right (○)", "x" to "Left (□)", "y" to "Top (△)",
        "l" to "L1", "r" to "R1", "l2" to "L2", "r2" to "R2", "l3" to "L3", "r3" to "R3",
        "select" to "Select", "start" to "Start",
        "up" to "D-pad Up", "down" to "D-pad Down", "left" to "D-pad Left", "right" to "D-pad Right",
        "left_stick_up" to "Left stick Up", "left_stick_down" to "Left stick Down",
        "left_stick_left" to "Left stick Left", "left_stick_right" to "Left stick Right",
        "right_stick_up" to "Right stick Up", "right_stick_down" to "Right stick Down",
        "right_stick_left" to "Right stick Left", "right_stick_right" to "Right stick Right"
    )
    private val GAME = mapOf(
        "a" to "A", "b" to "B", "x" to "X", "y" to "Y",
        "l" to "L1", "r" to "R1", "l2" to "L2", "r2" to "R2", "l3" to "L3", "r3" to "R3",
        "select" to "Select", "start" to "Start",
        "up" to "Up", "down" to "Down", "left" to "Left", "right" to "Right",
        "left_stick_up" to "L-stick Up", "left_stick_down" to "L-stick Down",
        "left_stick_left" to "L-stick Left", "left_stick_right" to "L-stick Right",
        "right_stick_up" to "R-stick Up", "right_stick_down" to "R-stick Down",
        "right_stick_left" to "R-stick Left", "right_stick_right" to "R-stick Right"
    )

    /** Your pad's button, by position and glyph (the source of a mapping). */
    fun padLabel(source: String): String = PAD[source.trim().lowercase()] ?: source

    /** What the game receives (the target of a mapping). */
    fun gameLabel(target: String): String = GAME[target.trim().lowercase()] ?: target

    /** One editor row: "<your pad's button> → <what the game receives>". */
    fun rowText(target: String, source: String?): String =
        "${if (source.isNullOrBlank()) "nothing" else padLabel(source)} → ${gameLabel(target)}"

    /** On each of your pad's controls: what it sends to the game now (the mapping inverted; never changes the map). */
    fun pictureLabels(mapping: Map<String, String>): Map<String, String> {
        val out = LinkedHashMap<String, String>()
        for (source in LAYOUT.keys) out[source] = NOTHING
        val sends = LinkedHashMap<String, MutableList<String>>()
        for ((target, source) in mapping) {
            val s = source.trim().lowercase()
            if (s.isEmpty()) continue
            sends.getOrPut(s) { mutableListOf() }.add(gameLabel(target))
        }
        for ((s, labels) in sends) out[s] = labels.joinToString("+")
        return out
    }

    /** The controls whose label differs from the default mapping's (highlighted on the picture). */
    fun changed(mapping: Map<String, String>, default: Map<String, String>): Set<String> {
        val now = pictureLabels(mapping)
        val before = pictureLabels(default)
        return now.keys.filter { now[it] != before[it] }.toSet()
    }

    // --- B89: the picture's geometry, in one place (the view, the SVG and the off-device render all draw this) -----

    /** The picture's height / width. Every shape below is in "width units": x in 0..1, y in 0..ASPECT. */
    const val ASPECT = 0.62f
    /** One stroke width for every line, in width units. */
    const val STROKE = 0.006f
    /** The picture is at most this share of the screen's height (B89: the editor's rows stay in view). */
    const val MAX_SCREEN_SHARE = 0.2f

    sealed class Shape {
        data class Outline(val points: List<Pair<Float, Float>>) : Shape()
        data class RoundRect(val id: String, val x: Float, val y: Float, val w: Float, val h: Float, val r: Float) : Shape()
        data class Circle(val id: String, val cx: Float, val cy: Float, val r: Float) : Shape()
        data class Cross(val id: String, val cx: Float, val cy: Float, val arm: Float, val half: Float) : Shape()
    }

    /** A label's box (width units): the control's text is fitted inside it. */
    data class Box(val id: String, val x: Float, val y: Float, val w: Float, val h: Float) {
        fun overlaps(o: Box): Boolean = x < o.x + o.w && o.x < x + w && y < o.y + o.h && o.y < y + h
        val cx: Float get() = x + w / 2
        val cy: Float get() = y + h / 2
    }

    private fun arc(cx: Float, cy: Float, r: Float, from: Double, to: Double, steps: Int): List<Pair<Float, Float>> =
        (0..steps).map { i ->
            val a = Math.toRadians(from + (to - from) * i / steps)
            (cx + r * Math.cos(a).toFloat()) to (cy + r * Math.sin(a).toFloat())
        }

    /** The body: a flat top with rounded corners, two rounded grips, a raised middle between them (right half drawn,
     *  then mirrored: the outline is symmetric by construction). */
    val OUTLINE: List<Pair<Float, Float>> = run {
        val right = mutableListOf(0.5f to 0.14f, 0.80f to 0.14f)
        right += arc(0.80f, 0.24f, 0.10f, -90.0, 0.0, 8)                     // the top-right corner
        right += 0.94f to 0.44f                                                // the grip's outer side
        right += arc(0.83f, 0.46f, 0.11f, 0.0, 150.0, 14)                     // the grip's rounded end
        right += listOf(0.66f to 0.50f, 0.5f to 0.50f)                         // up to the raised middle
        val left = right.reversed().map { (x, y) -> (1f - x) to y }
        (right + left.drop(1)).distinct()
    }

    val SHAPES: List<Shape> = listOf(
        Shape.Outline(OUTLINE),
        Shape.RoundRect("l2", 0.15f, 0.015f, 0.16f, 0.05f, 0.015f), Shape.RoundRect("r2", 0.69f, 0.015f, 0.16f, 0.05f, 0.015f),
        Shape.RoundRect("l", 0.13f, 0.075f, 0.20f, 0.05f, 0.015f), Shape.RoundRect("r", 0.67f, 0.075f, 0.20f, 0.05f, 0.015f),
        Shape.Cross("dpad", 0.24f, 0.30f, 0.06f, 0.022f),
        Shape.Circle("y", 0.76f, 0.235f, 0.028f), Shape.Circle("a", 0.76f, 0.365f, 0.028f),
        Shape.Circle("x", 0.695f, 0.30f, 0.028f), Shape.Circle("b", 0.825f, 0.30f, 0.028f),
        Shape.RoundRect("select", 0.405f, 0.24f, 0.05f, 0.022f, 0.011f),
        Shape.RoundRect("start", 0.545f, 0.24f, 0.05f, 0.022f, 0.011f),
        Shape.Circle("l3", 0.37f, 0.41f, 0.05f), Shape.Circle("r3", 0.63f, 0.41f, 0.05f)
    )

    /** Each control's label box: inside the control, or beside it (Select / Start under theirs, stick directions around
     *  their stick). */
    val BOXES: List<Box> = run {
        val b = mutableListOf<Box>()
        fun at(id: String, cx: Float, cy: Float, w: Float, h: Float) { b += Box(id, cx - w / 2, cy - h / 2, w, h) }
        at("l2", 0.23f, 0.04f, 0.12f, 0.036f); at("r2", 0.77f, 0.04f, 0.12f, 0.036f)
        at("l", 0.23f, 0.10f, 0.14f, 0.036f); at("r", 0.77f, 0.10f, 0.14f, 0.036f)
        at("up", 0.24f, 0.26f, 0.034f, 0.03f); at("down", 0.24f, 0.34f, 0.034f, 0.03f)
        at("left", 0.20f, 0.30f, 0.034f, 0.03f); at("right", 0.28f, 0.30f, 0.034f, 0.03f)
        for (id in listOf("y", "a", "x", "b")) {
            val c = SHAPES.filterIsInstance<Shape.Circle>().first { it.id == id }
            at(id, c.cx, c.cy, 0.036f, 0.036f)
        }
        at("select", 0.43f, 0.283f, 0.07f, 0.026f); at("start", 0.57f, 0.283f, 0.07f, 0.026f)
        for ((stick, cx) in listOf("left" to 0.37f, "right" to 0.63f)) {
            val press = if (stick == "left") "l3" else "r3"
            at(press, cx, 0.41f, 0.044f, 0.03f)
            at("${stick}_stick_up", cx, 0.343f, 0.05f, 0.022f)
            at("${stick}_stick_down", cx, 0.477f, 0.05f, 0.022f)
            at("${stick}_stick_left", cx - 0.073f, 0.41f, 0.04f, 0.022f)
            at("${stick}_stick_right", cx + 0.073f, 0.41f, 0.04f, 0.022f)
        }
        b
    }

    /** The short words a box holds: the game's letter, L1 … R3, SEL / START, arrows for directions. */
    fun shortLabel(target: String): String = when (val t = target.trim().lowercase()) {
        "a", "b", "x", "y" -> t.uppercase()
        "l" -> "L1"; "r" -> "R1"; "l2" -> "L2"; "r2" -> "R2"; "l3" -> "L3"; "r3" -> "R3"
        "select" -> "SEL"; "start" -> "START"
        "up" -> "↑"; "down" -> "↓"; "left" -> "←"; "right" -> "→"
        else -> when {
            t.startsWith("left_stick_") -> "L" + shortLabel(t.removePrefix("left_stick_"))
            t.startsWith("right_stick_") -> "R" + shortLabel(t.removePrefix("right_stick_"))
            else -> t
        }
    }

    /** On each control's box: what it sends now, in short words (never changes the map). */
    fun shortLabels(mapping: Map<String, String>): Map<String, String> {
        val out = LinkedHashMap<String, String>()
        for (box in BOXES) out[box.id] = NOTHING
        val sends = LinkedHashMap<String, MutableList<String>>()
        for ((target, source) in mapping) {
            val s = source.trim().lowercase()
            if (s.isNotEmpty()) sends.getOrPut(s) { mutableListOf() }.add(shortLabel(target))
        }
        for ((s, labels) in sends) if (s in out) out[s] = labels.joinToString("+")
        return out
    }

    /** The picture's size in pixels: at most a fifth of the screen's height, never wider than the space. */
    fun pictureSize(availableWidth: Int, screenHeight: Int): Pair<Int, Int> {
        val byHeight = (screenHeight * MAX_SCREEN_SHARE).toInt()
        val h = minOf(byHeight, (availableWidth * ASPECT).toInt()).coerceAtLeast(1)
        return (h / ASPECT).toInt() to h
    }

    /** The same picture as an SVG document (`px` wide), for looking at off the device. */
    fun svg(mapping: Map<String, String>, default: Map<String, String>, px: Int = 800): String {
        val k = px.toFloat()
        val labels = shortLabels(mapping)
        val changed = changed(mapping, default)
        val sw = STROKE * k
        val sb = StringBuilder()
        sb.append("<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"$px\" height=\"${(ASPECT * k).toInt()}\" ")
            .append("viewBox=\"0 0 $px ${(ASPECT * k).toInt()}\"><rect width=\"100%\" height=\"100%\" fill=\"#1c1c1c\"/>")
            .append("<g fill=\"none\" stroke=\"#cfcfcf\" stroke-width=\"$sw\" stroke-linejoin=\"round\">")
        for (s in SHAPES) when (s) {
            is Shape.Outline -> sb.append("<polygon points=\"")
                .append(s.points.joinToString(" ") { (x, y) -> "${x * k},${y * k}" }).append("\"/>")
            is Shape.RoundRect -> sb.append("<rect x=\"${s.x * k}\" y=\"${s.y * k}\" width=\"${s.w * k}\" height=\"${s.h * k}\" rx=\"${s.r * k}\"/>")
            is Shape.Circle -> sb.append("<circle cx=\"${s.cx * k}\" cy=\"${s.cy * k}\" r=\"${s.r * k}\"/>")
            is Shape.Cross -> sb.append("<path d=\"").append(crossPath(s).joinToString(" ", postfix = " Z") { (x, y) -> "L${x * k},${y * k}" }.replaceFirst("L", "M")).append("\"/>")
        }
        sb.append("</g><g font-family=\"sans-serif\" text-anchor=\"middle\" dominant-baseline=\"central\">")
        for (box in BOXES) {
            val text = labels[box.id] ?: continue
            if (box.id.contains("stick") && box.id !in changed) continue
            val size = minOf(box.h * k * 0.85f, box.w * k / (0.62f * maxOf(1, text.length)))
            sb.append("<text x=\"${box.cx * k}\" y=\"${box.cy * k}\" font-size=\"$size\" fill=\"")
                .append(if (box.id in changed) "#ffc107" else "#ffffff").append("\">")
                .append(text.replace("&", "&amp;").replace("<", "&lt;")).append("</text>")
        }
        return sb.append("</g></svg>").toString()
    }

    /** The cross's outline (12 points). */
    fun crossPath(c: Shape.Cross): List<Pair<Float, Float>> {
        val (x, y, a, h) = listOf(c.cx, c.cy, c.arm, c.half)
        return listOf(x - h to y - a, x + h to y - a, x + h to y - h, x + a to y - h, x + a to y + h, x + h to y + h,
                      x + h to y + a, x - h to y + a, x - h to y + h, x - a to y + h, x - a to y - h, x - h to y - h)
    }

    /** B86's map of each control's place (x, y as fractions of the picture), now the centres of B89's boxes. */
    val LAYOUT: Map<String, Pair<Float, Float>> = BOXES.associate { it.id to (it.cx to it.cy / ASPECT) }

    fun parse(value: String?): Boolean = value?.trim().let { it != "0" && it != "off" }

    fun fromSystem(): Boolean =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as String?)
        } catch (_: Throwable) {
            true
        }
}
