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

    /**
     * Where each of your pad's controls sits on the picture, in a 0..1 box (x, y): a plain outline drawn by the app —
     * a body with two grips, a D-pad (left), four face buttons (right), two sticks (lower middle), shoulders and
     * triggers (top), Select / Start (centre).
     */
    val LAYOUT: Map<String, Pair<Float, Float>> = linkedMapOf(
        "l2" to (0.18f to 0.05f), "r2" to (0.82f to 0.05f),
        "l" to (0.18f to 0.15f), "r" to (0.82f to 0.15f),
        "up" to (0.22f to 0.33f), "down" to (0.22f to 0.53f), "left" to (0.13f to 0.43f), "right" to (0.31f to 0.43f),
        "y" to (0.78f to 0.31f), "a" to (0.78f to 0.55f), "x" to (0.69f to 0.43f), "b" to (0.87f to 0.43f),
        "select" to (0.42f to 0.36f), "start" to (0.58f to 0.36f),
        "l3" to (0.36f to 0.66f), "r3" to (0.64f to 0.66f),
        "left_stick_up" to (0.36f to 0.58f), "left_stick_down" to (0.36f to 0.74f),
        "left_stick_left" to (0.29f to 0.66f), "left_stick_right" to (0.43f to 0.66f),
        "right_stick_up" to (0.64f to 0.58f), "right_stick_down" to (0.64f to 0.74f),
        "right_stick_left" to (0.57f to 0.66f), "right_stick_right" to (0.71f to 0.66f)
    )

    fun parse(value: String?): Boolean = value?.trim().let { it != "0" && it != "off" }

    fun fromSystem(): Boolean =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as String?)
        } catch (_: Throwable) {
            true
        }
}
