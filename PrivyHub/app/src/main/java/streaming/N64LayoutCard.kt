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
}
