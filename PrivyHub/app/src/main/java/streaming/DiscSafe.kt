package com.safeiot.privyhub.streaming

/**
 * B74: the disc change made safe. HOME-10's changes outside the game's own "insert disc" prompt left the picture
 * black (the game's reaction to a lid cycle, as on a console; the host's sequence is right), so:
 *  - CHANGE DISC first warns, once per onn ("I understand" remembered in the app's preferences), then the chooser;
 *  - after a change the status line says what to do if the game freezes;
 *  - a set offers "Start on disc…" in the launch's Extras (the host starts a set on disc 1 otherwise).
 * `debug.privyhub.disc_safe=0` = B71's flow (no warning, B71's line, no "Start on disc…", no `disc=` on a launch).
 */
object DiscSafe {
    const val PROPERTY = "debug.privyhub.disc_safe"
    const val TITLE = "Change disc"
    const val WARNING =
        "Change discs only when the game asks for the next one — changing at any other time can freeze the game"
    const val UNDERSTAND = "I understand"
    const val PREF_UNDERSTOOD = "disc_change_warning_understood"
    const val START_LABEL = "Start on disc…"
    const val START_TITLE = "Start on disc"

    /** The warning shows until the user has said "I understand" on this onn (and never with the property off). */
    fun needsWarning(safeOn: Boolean, understood: Boolean): Boolean = safeOn && !understood

    /** The line after a change: "Disc 2 of 4 — if the game freezes, use LOAD or END". */
    fun afterChangeLine(state: DiscChange.State): String =
        DiscChange.statusLine(state) + " — if the game freezes, use LOAD or END"

    /** "Start on disc…" only for a set (the host's details `discs` > 1). */
    fun showStartOnDisc(safeOn: Boolean, discs: Int): Boolean = safeOn && discs > 1

    fun startChoices(discs: Int): List<String> = (1..discs).map { "Disc $it" }

    /** The launch's query suffix: none (today's URL) unless a disc was chosen. */
    fun launchSuffix(disc: Int?): String = disc?.takeIf { it >= 1 }?.let { "&disc=$it" } ?: ""

    fun parse(value: String?): Boolean = value?.trim().let { it != "0" && it != "off" }

    fun fromSystem(): Boolean =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as? String)
        } catch (_: Throwable) {
            parse(null)
        }
}
