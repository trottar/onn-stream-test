package com.safeiot.privyhub.streaming

/**
 * B91: the mapping editor's layout on a wide screen, in one place — the picture **beside** the rows (left pane, outside
 * the rows' scroll), its labels at the rows' own text size. The editor (`MainActivity`) builds its panes from [plan];
 * the off-device render and the JVM tests read the same numbers. `debug.privyhub.mapping_picture=0` = today's editor.
 * Design: docs/memory/evidence/b91_2026-11-11/design_written_before_code.md (hashed before this code).
 */
object MappingEditorLayout {
    /** The rows' text (each row's "Bottom (✕) → B"): today's literal 17 sp, now one constant. */
    const val ROW_TEXT_SP = 17f
    /** The picture's label text: never smaller than the rows'. */
    const val LABEL_TEXT_SP = ROW_TEXT_SP
    /** The dialog's window: this share of the screen's width and height. */
    const val DIALOG_SHARE = 0.92f
    /** The AlertDialog's title and button bar (estimates of the theme's, in dp). */
    const val TITLE_DP = 64f
    const val BUTTON_BAR_DP = 64f
    /** Today's container padding (px, as `setPadding` gives it). */
    const val PAD_H = 24
    const val PAD_V = 16
    /** The left pane's share of the content width, and the gap between the panes (px). */
    const val LEFT_SHARE = 0.45f
    const val GAP_PX = 24
    /** The legend under the picture: its text size and the lines it takes in the left pane (an estimate). */
    const val LEGEND_SP = 14f
    const val LEGEND_LINES = 3
    /** The row-height model: today's row padding (8 top, 20 bottom, px), the 17-sp line, the 48-dp "Change" button. */
    const val ROW_PAD_PX = 28
    const val BUTTON_DP = 48f
    const val LINE = 1.17f
    /** Above the rows in the right pane: the heading (18 sp, 16 px padding), the status line (14 sp, 20 px), the copy
     *  button (48 dp). */
    const val HEADING_SP = 18f
    const val STATUS_SP = 14f

    data class Plan(
        val beside: Boolean,
        val dialogW: Int, val dialogH: Int,
        val contentW: Int, val contentH: Int,
        val leftW: Int, val rightW: Int,
        val pictureW: Int, val pictureH: Int,
        val labelTextPx: Float, val rowTextPx: Float,
        val rowHeightPx: Int,
        val rowsVisibleBeside: Int, val rowsVisibleToday: Int,
        /** The picture sits in the left pane, outside the rows' scroll: it never scrolls away. */
        val pictureOutsideScroll: Boolean
    )

    fun rowHeightPx(density: Float): Int = (ROW_PAD_PX + LINE * ROW_TEXT_SP * density + BUTTON_DP * density).toInt()

    fun headerPx(density: Float): Int =
        (LINE * HEADING_SP * density + 16 + LINE * STATUS_SP * density + 20 + BUTTON_DP * density).toInt()

    fun legendPx(density: Float): Int = (LEGEND_LINES * LINE * LEGEND_SP * density + 20).toInt()

    /** The editor's layout on a `screenW` × `screenH` px screen at `density` (px per dp; sp taken at font scale 1). */
    fun plan(screenW: Int, screenH: Int, density: Float): Plan {
        val dialogW = (screenW * DIALOG_SHARE).toInt()
        val dialogH = (screenH * DIALOG_SHARE).toInt()
        val contentW = dialogW - 2 * PAD_H
        val contentH = dialogH - ((TITLE_DP + BUTTON_BAR_DP) * density).toInt() - 2 * PAD_V
        val beside = screenW > screenH
        val leftW = if (beside) (contentW * LEFT_SHARE).toInt() else contentW
        val rightW = if (beside) contentW - leftW - GAP_PX else contentW
        var pictureW = leftW
        val room = contentH - legendPx(density)
        if (MappingPicture.besideHeight(pictureW) > room) pictureW = (room / MappingPicture.BESIDE_ASPECT).toInt()
        val pictureH = MappingPicture.besideHeight(pictureW)
        val row = rowHeightPx(density)
        val header = headerPx(density)
        val besideRows = ((contentH - header) / row).coerceAtLeast(0)
        // today: B89's picture (≤ a fifth of the screen) and the legend above the same header and rows, in one scroll
        val (_, b89H) = MappingPicture.pictureSize(contentW, screenH)
        val todayRows = ((contentH - header - b89H - legendPx(density)) / row).coerceAtLeast(0)
        return Plan(beside, dialogW, dialogH, contentW, contentH, leftW, rightW, pictureW, pictureH,
                    LABEL_TEXT_SP * density, ROW_TEXT_SP * density, row,
                    if (beside) besideRows else todayRows, todayRows, beside)
    }
}
