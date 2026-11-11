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

    // --- B91: the picture beside the rows, its labels at the rows' text size, boxes never overlapping -----------------

    /** The controller's share of the beside view's width, its top margin, and the view's height / width (B91). */
    const val CONTROLLER_SHARE = 0.86f
    const val BESIDE_TOP = 0.05f
    const val BESIDE_ASPECT = 0.74f

    /** Where each control's label sits when it fits there (controller width units): B89's box centres, the triggers'
     *  and shoulders' spread apart in their shapes, the D-pad arrows at the arms' ends, Select's under it and Start's
     *  above it, the stick directions further out. */
    val ANCHORS: Map<String, Pair<Float, Float>> = run {
        val a = LinkedHashMap<String, Pair<Float, Float>>()
        for (b in BOXES) a[b.id] = b.cx to b.cy
        a["up"] = 0.24f to 0.225f; a["down"] = 0.24f to 0.375f; a["left"] = 0.165f to 0.30f; a["right"] = 0.315f to 0.30f
        a["l2"] = 0.23f to 0.035f; a["r2"] = 0.77f to 0.035f; a["l"] = 0.23f to 0.105f; a["r"] = 0.77f to 0.105f
        a["select"] = 0.41f to 0.283f; a["start"] = 0.575f to 0.205f                       // Select under, Start above
        for ((stick, cx) in listOf("left" to 0.37f, "right" to 0.63f)) {
            a["${stick}_stick_up"] = cx to 0.325f; a["${stick}_stick_down"] = cx to 0.495f
            a["${stick}_stick_left"] = (cx - 0.095f) to 0.41f; a["${stick}_stick_right"] = (cx + 0.095f) to 0.41f
        }
        a
    }

    /** The shape a label belongs to (its own shape may lie under it; any other control's may not). */
    fun shapeOf(id: String): String = when {
        id in setOf("up", "down", "left", "right") -> "dpad"
        id.startsWith("left_stick_") -> "l3"
        id.startsWith("right_stick_") -> "r3"
        else -> id
    }

    /** Each control shape's bounds (controller width units). */
    val SHAPE_BOUNDS: Map<String, Box> = SHAPES.mapNotNull {
        when (it) {
            is Shape.RoundRect -> Box(it.id, it.x, it.y, it.w, it.h)
            is Shape.Circle -> Box(it.id, it.cx - it.r, it.cy - it.r, 2 * it.r, 2 * it.r)
            is Shape.Cross -> Box(it.id, it.cx - it.arm, it.cy - it.arm, 2 * it.arm, 2 * it.arm)
            else -> null
        }
    }.associateBy { it.id }

    /** A label as drawn: its box in the view's pixels, its control's point, and whether a leader line joins them. */
    data class Placed(val id: String, val text: String, val box: Box, val ax: Float, val ay: Float,
                      val leader: Boolean, val changed: Boolean)

    /** The beside view's height for a view `w` px wide. */
    fun besideHeight(w: Int): Int = (w * BESIDE_ASPECT).toInt()

    /** The controller's scale and offset (px) in a beside view `w` px wide. */
    fun besideScale(w: Float): Float = CONTROLLER_SHARE * w
    fun besideLeft(w: Float): Float = (1f - CONTROLLER_SHARE) / 2f * w
    fun besideTop(w: Float): Float = BESIDE_TOP * w

    /** B91's placement: every label at `textPx`, boxes = text width + ½ text height, 1.3 text heights tall. Pass 1 puts
     *  each at its control when it overlaps no placed box and no other control's shape; pass 2 moves the rest outward
     *  (rings of ¼ text height, 16 directions, the outward one first) to the first free place inside the view, with a
     *  leader. `measure` is the drawing font's width of a text at `textPx`. Never returns overlapping boxes: a label
     *  with no free place is left out (the tests require none is). */
    fun placeLabels(viewW: Float, viewH: Float, textPx: Float, mapping: Map<String, String>, default: Map<String, String>,
                    measure: (String) -> Float): List<Placed> =
        placeLabelTexts(viewW, viewH, textPx, shortLabels(mapping), changed(mapping, default), measure)

    /** [placeLabels] for given texts per control and the changed set (stick directions drawn only when changed). */
    fun placeLabelTexts(viewW: Float, viewH: Float, textPx: Float, labels: Map<String, String>, changed: Set<String>,
                        measure: (String) -> Float): List<Placed> {
        val k = besideScale(viewW); val ox = besideLeft(viewW); val oy = besideTop(viewW)
        val shapes = SHAPE_BOUNDS.mapValues { (_, b) -> Box(b.id, ox + b.x * k, oy + b.y * k, b.w * k, b.h * k) }
        val h = 1.3f * textPx
        val order = listOf("a", "b", "x", "y", "l", "r", "l2", "r2", "up", "down", "left", "right", "select", "start",
                           "l3", "r3") + ANCHORS.keys.filter { it.contains("stick") }
        val todo = order.filter { id -> labels[id] != null && !(id.contains("stick") && id !in changed) }
        val placed = mutableListOf<Placed>()
        val later = mutableListOf<String>()
        fun boxAt(id: String, cx: Float, cy: Float, w: Float) = Box(id, cx - w / 2, cy - h / 2, w, h)
        fun free(b: Box, id: String): Boolean =
            b.x >= 0f && b.y >= 0f && b.x + b.w <= viewW && b.y + b.h <= viewH &&
                placed.none { it.box.overlaps(b) } &&
                shapes.none { (sid, sb) -> sid != shapeOf(id) && sb.overlaps(b) }
        for (id in todo) {
            val text = labels.getValue(id)
            val (u, v) = ANCHORS.getValue(id)
            val ax = ox + u * k; val ay = oy + v * k
            val b = boxAt(id, ax, ay, measure(text) + 0.5f * textPx)
            if (free(b, id)) placed += Placed(id, text, b, ax, ay, false, id in changed) else later += id
        }
        val cx0 = ox + 0.5f * k; val cy0 = oy + 0.33f * k
        for (id in later) {
            val text = labels.getValue(id)
            val (u, v) = ANCHORS.getValue(id)
            val ax = ox + u * k; val ay = oy + v * k
            val w = measure(text) + 0.5f * textPx
            val out = Math.atan2((ay - cy0).toDouble(), (ax - cx0).toDouble())
            val dirs = (0 until 16).map { it * Math.PI / 8 }
                .sortedBy { d -> Math.abs(Math.IEEEremainder(d - out, 2 * Math.PI)) }
            var found: Box? = null
            var r = 0.25f * textPx
            val maxR = viewW + viewH
            while (found == null && r <= maxR) {
                for (d in dirs) {
                    val b = boxAt(id, ax + r * Math.cos(d).toFloat(), ay + r * Math.sin(d).toFloat(), w)
                    if (free(b, id)) { found = b; break }
                }
                r += 0.25f * textPx
            }
            if (found != null) placed += Placed(id, text, found, ax, ay, true, id in changed)
        }
        return placed
    }

    /** The point of `b` nearest (x, y): where a leader line meets its box. */
    fun nearest(b: Box, x: Float, y: Float): Pair<Float, Float> =
        x.coerceIn(b.x, b.x + b.w) to y.coerceIn(b.y, b.y + b.h)

    fun parse(value: String?): Boolean = value?.trim().let { it != "0" && it != "off" }

    fun fromSystem(): Boolean =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as String?)
        } catch (_: Throwable) {
            true
        }
}
