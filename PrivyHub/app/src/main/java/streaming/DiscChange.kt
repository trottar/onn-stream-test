package com.safeiot.privyhub.streaming

/**
 * B71: "Change disc" in the paused game's bar, only on a multi-disc session (the host's `discs` > 1, from the launch
 * response and the `status` poll). The chooser lists the discs with the current one marked; the pick goes to the
 * host's `disc-swap` action and the bar says "Disc 2 of 4". `debug.privyhub.disc_change=0` = today (no entry).
 */
object DiscChange {
    const val PROPERTY = "debug.privyhub.disc_change"
    const val LABEL = "CHANGE DISC"
    const val ENDPOINT = "disc-swap"

    /** A session's discs: `disc` null = not known (after a LOAD the host cannot tell). */
    data class State(val discs: Int, val disc: Int?)

    /** Null unless the host said `discs` > 1 (absent, 0 or 1 = a one-disc game: today). */
    fun fromValues(discs: Int?, disc: Int?): State? {
        if (discs == null || discs <= 1) return null
        return State(discs, disc?.takeIf { it in 1..discs })
    }

    fun showEntry(enabled: Boolean, state: State?): Boolean = enabled && state != null

    /** "Disc 1" … "Disc n", " (in the tray)" beside the known current one. */
    fun choices(state: State): List<String> =
        (1..state.discs).map { i -> "Disc $i" + if (i == state.disc) " (in the tray)" else "" }

    /** The chooser's row -> the disc asked for. */
    fun discForChoice(index: Int): Int = index + 1

    fun statusLine(state: State): String =
        state.disc?.let { "Disc $it of ${state.discs}" } ?: "${state.discs} discs"

    fun query(disc: Int): String = "disc=$disc"

    fun progressLine(disc: Int): String = "Changing to disc $disc…"

    fun parse(value: String?): Boolean = value?.trim().let { it != "0" && it != "off" }

    fun fromSystem(): Boolean =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as? String)
        } catch (_: Throwable) {
            parse(null)
        }
}
