package com.safeiot.privyhub.streaming

/**
 * B67: the N64 layout, shown once per onn at the first N64 start (the host's `game_session.game.system` = `n64`),
 * while the player prompt is on. The glyphs only if the font draws all four; else the button names. Dismissed by
 * the first key-down (not consumed). Remembered in a private preference, written when shown. No prompt = no card.
 */
object N64LayoutCard {
    const val PREFS = "privyhub_n64_layout"
    const val KEY_SHOWN = "shown"
    val GLYPHS = listOf("✕", "□", "△", "○")     // ✕ □ △ ○
    const val TEXT_GLYPHS =
        "A = ✕, B = □, C-buttons = right stick (also △ = C-up, ○ = C-right), Z = L2"
    const val TEXT_LETTERS =
        "A = Cross, B = Square, C-buttons = right stick (also Triangle = C-up, Circle = C-right), Z = L2"

    fun shouldShow(system: String?, promptOn: Boolean, alreadyShown: Boolean): Boolean =
        promptOn && !alreadyShown && system?.trim()?.lowercase() == "n64"

    fun text(hasGlyph: (String) -> Boolean): String = if (GLYPHS.all(hasGlyph)) TEXT_GLYPHS else TEXT_LETTERS

    // B72 (a): the card above the "Stabilizing game..." text, not over its details line.
    // `debug.privyhub.n64_card_top=0` = B67's centred card (the overlay untouched).
    const val PROPERTY_TOP = "debug.privyhub.n64_card_top"
    const val GAP_PX = 24
    const val OVERLAY_BASE_TOP_PX = 32

    /** The overlay's top padding while the card shows: its text centred in the space under the card. */
    fun overlayTopPadding(cardBottomPx: Int, basePx: Int = OVERLAY_BASE_TOP_PX): Int =
        maxOf(basePx, cardBottomPx + GAP_PX)

    /** The card's gravity: top and centred across (on), or B67's centre (off). */
    fun gravity(top: Boolean): Int =
        if (top) android.view.Gravity.TOP or android.view.Gravity.CENTER_HORIZONTAL else android.view.Gravity.CENTER

    /** The card's own "shown" key: the top layout is shown once more on an onn that saw B67's centred card
     *  (`shown_top`); with the property off, B67's key. */
    const val KEY_SHOWN_TOP = "shown_top"

    fun shownKey(top: Boolean): String = if (top) KEY_SHOWN_TOP else KEY_SHOWN

    fun parseTop(value: String?): Boolean = value?.trim().let { it != "0" && it != "off" }

    fun topFromSystem(): Boolean =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parseTop(get.invoke(null, PROPERTY_TOP) as? String)
        } catch (_: Throwable) {
            parseTop(null)
        }
}
