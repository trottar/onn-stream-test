package com.safeiot.privyhub.streaming

/**
 * B73: the paused bar (SAVE · LOAD · CHANGE DISC · END) fits the TV. B71's four buttons needed 1018 dp on the onn's
 * 960-dp screen and HOME-10 saw END "~95 % off" (the TV's visible edge ≈ 899 dp). On a multi-disc session the four
 * buttons are 80 dp with 6-dp gaps, the disc button reads "DISC" (the bar's status text already carries
 * "Disc 2 of 4" under PAUSED) and the bar's end padding is 80 dp, so END ends at 880 dp. A one-disc bar (three
 * buttons) is today's, untouched. `debug.privyhub.paused_bar_fit=0` = B71's bar.
 */
object PausedBar {
    const val PROPERTY = "debug.privyhub.paused_bar_fit"

    // today's bar (activity_main.xml / createGameSessionActionButton / B71)
    const val TODAY_BUTTON_DP = 104
    const val TODAY_MARGIN_DP = 8
    const val B71_DISC_DP = 150
    const val B71_DISC_LABEL = "CHANGE DISC"
    const val TODAY_STATUS_DP = 280
    const val TODAY_PAD_START_DP = 24
    const val TODAY_PAD_END_DP = 20
    const val PREVIEW_DP = 184 + 8 + 8

    // B73's four-button bar
    const val FIT_BUTTON_DP = 80
    const val FIT_MARGIN_DP = 6
    const val FIT_DISC_LABEL = "DISC"
    const val FIT_PAD_END_DP = 80
    const val TITLE_MIN_DP = 80
    const val STATUS_MIN_DP = 160

    data class Plan(
        val buttonDp: Int,
        val marginDp: Int,
        val discDp: Int,
        val discLabel: String,
        val statusDp: Int,
        val padEndDp: Int,
        val fourButtons: Boolean,
    )

    val TODAY = Plan(TODAY_BUTTON_DP, TODAY_MARGIN_DP, B71_DISC_DP, B71_DISC_LABEL, TODAY_STATUS_DP, TODAY_PAD_END_DP, false)

    /** Today's numbers unless `fit` and four buttons; then the status text takes what the title's minimum leaves. */
    fun plan(fit: Boolean, fourButtons: Boolean, screenWidthDp: Int): Plan {
        if (!fourButtons) return TODAY
        if (!fit) return TODAY.copy(fourButtons = true)
        val buttons = 4 * (FIT_BUTTON_DP + FIT_MARGIN_DP)
        val status = (screenWidthDp - TODAY_PAD_START_DP - TITLE_MIN_DP - PREVIEW_DP - buttons - FIT_PAD_END_DP)
            .coerceIn(STATUS_MIN_DP, TODAY_STATUS_DP)
        return Plan(FIT_BUTTON_DP, FIT_MARGIN_DP, FIT_BUTTON_DP, FIT_DISC_LABEL, status, FIT_PAD_END_DP, true)
    }

    /** One child's place in the row, in dp from the screen's left edge. */
    data class Span(val name: String, val left: Int, val right: Int)

    /**
     * The row as LinearLayout places it: the start padding, the title column (weight 1: what is left, never below 0),
     * the status text, the preview, then the buttons each after its margin. A right edge past the screen is off it.
     */
    fun layout(plan: Plan, screenWidthDp: Int): List<Span> {
        val buttons = if (plan.fourButtons) {
            listOf("SAVE" to plan.buttonDp, "LOAD" to plan.buttonDp, "DISC" to plan.discDp, "END" to plan.buttonDp)
        } else {
            listOf("SAVE" to plan.buttonDp, "LOAD" to plan.buttonDp, "END" to plan.buttonDp)
        }
        val fixed = plan.statusDp + PREVIEW_DP + buttons.sumOf { it.second + plan.marginDp }
        val title = (screenWidthDp - TODAY_PAD_START_DP - plan.padEndDp - fixed).coerceAtLeast(0)
        val out = mutableListOf<Span>()
        var x = TODAY_PAD_START_DP
        out += Span("title", x, x + title); x += title
        out += Span("status", x, x + plan.statusDp); x += plan.statusDp
        out += Span("preview", x + 8, x + PREVIEW_DP - 8); x += PREVIEW_DP
        for ((name, w) in buttons) {
            x += plan.marginDp
            out += Span(name, x, x + w); x += w
        }
        return out
    }

    fun parse(value: String?): Boolean = value?.trim().let { it != "0" && it != "off" }

    fun fromSystem(): Boolean =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as? String)
        } catch (_: Throwable) {
            parse(null)
        }
}
