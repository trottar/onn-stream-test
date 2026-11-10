package com.safeiot.privyhub.streaming

/**
 * B84: the cheat picker as PrivyHub's own screen, usable from the couch. "Launch Cheat Session" and "Cancel" sit at the
 * top (Left from any row reaches Launch; the pad's Start launches; Back cancels); a filter row; the list in sections
 * (General, Player 1 … Player 4, Other, Your files — B85's groups), each collapsed to its header with a count until
 * opened; the shoulder buttons / the remote's channel keys page by a screen.
 *
 * [CheatPickerModel] is the screen's whole behaviour (rows, focus, keys, filter, sections, selection); the activity's
 * view only draws its rows and forwards the keys. `debug.privyhub.cheat_picker=0` = today's multi-choice dialog.
 * Design: docs/memory/evidence/b84_2026-11-10/design_written_before_code.md (hashed before this code).
 */
object CheatPicker {
    const val PROPERTY = "debug.privyhub.cheat_picker"
    const val LAUNCH = "Launch Cheat Session"
    const val CANCEL = "Cancel"
    const val FILTER_HINT = "Filter — type to narrow the list"
    const val SELECTED_ONLY = "Selected only"
    const val HINT = "Left: jump to Launch · Start: launch · L1 / R1: page · on the filter: Right = selected only"

    /** The sections in the order shown, and their headers. */
    val GROUPS = listOf("general", "player1", "player2", "player3", "player4", "other", "yours")
    private val GROUP_NAMES = mapOf(
        "general" to "General", "player1" to "Player 1", "player2" to "Player 2", "player3" to "Player 3",
        "player4" to "Player 4", "other" to "Other", "yours" to "Your files"
    )

    fun groupName(group: String): String = GROUP_NAMES[group] ?: "General"

    /** An unknown or missing group (a hub without B85, `raw=1`) is General. */
    fun groupOf(value: String?): String = value?.trim()?.lowercase()?.takeIf { it in GROUPS } ?: "general"

    fun selectedLine(n: Int): String = "$n selected"

    fun parse(value: String?): Boolean = value?.trim().let { it != "0" && it != "off" }

    fun fromSystem(): Boolean =
        try {
            val get = Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
            parse(get.invoke(null, PROPERTY) as String?)
        } catch (_: Throwable) {
            true
        }
}

/** One selectable cheat as the hub lists it: `index` is what the launch sends (B85 expands parts / enablers). */
data class CheatEntry(val index: Int, val label: String, val group: String = "general", val variantOf: Int? = null)

/** The screen's rows. */
sealed class PickerRow {
    object Bar : PickerRow()
    object Filter : PickerRow()
    data class Header(val group: String, val count: Int, val open: Boolean) : PickerRow()
    data class Item(val entry: CheatEntry, val checked: Boolean, val indent: Boolean) : PickerRow()
}

enum class PickerAction { NONE, LAUNCH, CANCEL, EDIT_FILTER }

enum class PickerKey { UP, DOWN, LEFT, RIGHT, OK, START, BACK, PAGE_UP, PAGE_DOWN, OTHER }

class CheatPickerModel(entries: List<CheatEntry>, var pageSize: Int = 8) {
    companion object {
        /** Android's key codes (KeyEvent.KEYCODE_*), as literals so the model runs on the JVM. */
        fun keyOf(code: Int): PickerKey = when (code) {
            19 -> PickerKey.UP                                   // DPAD_UP
            20 -> PickerKey.DOWN                                 // DPAD_DOWN
            21 -> PickerKey.LEFT                                 // DPAD_LEFT
            22 -> PickerKey.RIGHT                                // DPAD_RIGHT
            23, 66, 160, 96 -> PickerKey.OK                      // DPAD_CENTER, ENTER, NUMPAD_ENTER, BUTTON_A
            108 -> PickerKey.START                               // BUTTON_START
            4, 97 -> PickerKey.BACK                              // BACK, BUTTON_B
            102, 166, 92 -> PickerKey.PAGE_UP                    // BUTTON_L1, CHANNEL_UP, PAGE_UP
            103, 167, 93 -> PickerKey.PAGE_DOWN                  // BUTTON_R1, CHANNEL_DOWN, PAGE_DOWN
            else -> PickerKey.OTHER
        }
    }

    private val all: List<CheatEntry> = entries
    private val byGroup: Map<String, List<CheatEntry>> = run {
        val out = LinkedHashMap<String, MutableList<CheatEntry>>()
        for (g in CheatPicker.GROUPS) out[g] = mutableListOf()
        for (e in entries) out.getValue(CheatPicker.groupOf(e.group)).add(e)
        out
    }
    private val opened = mutableSetOf<String>()
    private val selected = LinkedHashSet<Int>()
    private var words: List<String> = emptyList()

    var filter: String = ""
        private set
    var selectedOnly: Boolean = false
        private set

    /** The row the focus is on; on the bar, [barButton] 0 = Launch, 1 = Cancel. */
    var focus: Int = 0
        private set
    var barButton: Int = 0
        private set
    private var returnTo: Int = 2

    var rows: List<PickerRow> = emptyList()
        private set

    init {
        rebuild()
        focus = if (rows.size > 2) 2 else 0
    }

    val selectedCount: Int get() = selected.size

    fun isSelected(index: Int): Boolean = index in selected

    private fun matches(e: CheatEntry): Boolean {
        if (selectedOnly && e.index !in selected) return false
        if (words.isEmpty()) return true
        val label = e.label.lowercase()
        return words.all { it in label }
    }

    private fun narrowing(): Boolean = words.isNotEmpty() || selectedOnly

    private fun rebuild() {
        val out = ArrayList<PickerRow>()
        out.add(PickerRow.Bar)
        out.add(PickerRow.Filter)
        for ((group, list) in byGroup) {
            if (list.isEmpty()) continue
            if (narrowing()) {
                val shown = list.filter(::matches)
                if (shown.isEmpty()) continue
                out.add(PickerRow.Header(group, shown.size, true))
                for (e in shown) out.add(PickerRow.Item(e, e.index in selected, e.variantOf != null))
            } else {
                val open = group in opened
                out.add(PickerRow.Header(group, list.size, open))
                if (open) for (e in list) out.add(PickerRow.Item(e, e.index in selected, e.variantOf != null))
            }
        }
        rows = out
        if (focus >= rows.size) focus = rows.size - 1
    }

    fun setFilter(text: String) {
        filter = text
        words = text.lowercase().split(Regex("\\s+")).filter { it.isNotEmpty() }
        rebuild()
    }

    fun toggleSelectedOnly() {
        selectedOnly = !selectedOnly
        rebuild()
    }

    fun toggle(index: Int) {
        if (!selected.remove(index)) selected.add(index)
        rebuild()
    }

    fun toggleSection(group: String) {
        if (!opened.remove(group)) opened.add(group)
        rebuild()
    }

    private fun moveTo(row: Int) {
        focus = row.coerceIn(0, rows.size - 1)
    }

    /** The selected entries in the source's order: what the launch sends. */
    fun selection(): List<CheatEntry> = all.filter { it.index in selected }

    /** One key; returns what the activity must do. */
    fun onKey(key: PickerKey): PickerAction {
        when (key) {
            PickerKey.START -> return PickerAction.LAUNCH
            PickerKey.BACK -> return PickerAction.CANCEL
            PickerKey.LEFT -> {
                if (focus == 0) {
                    barButton = 0
                } else {
                    returnTo = focus
                    focus = 0
                    barButton = 0
                }
                return PickerAction.NONE
            }
            PickerKey.RIGHT -> {
                if (focus == 0) barButton = 1
                if (focus == 1) toggleSelectedOnly()          // the filter row: Right = "Selected only" on / off
                return PickerAction.NONE
            }
            PickerKey.UP -> {
                if (focus == 1) {
                    returnTo = 1
                    focus = 0
                    barButton = 0
                } else if (focus > 1) {
                    moveTo(focus - 1)
                }
                return PickerAction.NONE
            }
            PickerKey.DOWN -> {
                if (focus == 0) moveTo(returnTo.coerceAtLeast(1)) else moveTo(focus + 1)
                return PickerAction.NONE
            }
            PickerKey.PAGE_UP -> {
                if (focus > 1) moveTo((focus - pageSize).coerceAtLeast(2))
                return PickerAction.NONE
            }
            PickerKey.PAGE_DOWN -> {
                moveTo(if (focus < 2) 2 + pageSize - 1 else focus + pageSize)
                return PickerAction.NONE
            }
            PickerKey.OK -> {
                return when (val row = rows[focus]) {
                    PickerRow.Bar -> if (barButton == 0) PickerAction.LAUNCH else PickerAction.CANCEL
                    PickerRow.Filter -> PickerAction.EDIT_FILTER
                    is PickerRow.Header -> {
                        if (!narrowing()) toggleSection(row.group)
                        PickerAction.NONE
                    }
                    is PickerRow.Item -> {
                        toggle(row.entry.index)
                        PickerAction.NONE
                    }
                }
            }
            PickerKey.OTHER -> return PickerAction.NONE
        }
    }

    /** The text a row shows on the TV. */
    fun text(row: PickerRow): String = when (row) {
        PickerRow.Bar -> "${CheatPicker.LAUNCH}   ${CheatPicker.CANCEL}   ${CheatPicker.selectedLine(selected.size)}"
        PickerRow.Filter -> (if (filter.isBlank()) CheatPicker.FILTER_HINT else "Filter: $filter") +
            "   ${if (selectedOnly) "☑" else "☐"} ${CheatPicker.SELECTED_ONLY}"
        is PickerRow.Header -> "${if (row.open) "▾" else "▸"} ${CheatPicker.groupName(row.group)} (${row.count})"
        is PickerRow.Item -> "${if (row.checked) "☑" else "☐"} ${if (row.indent) "    " else ""}${row.entry.label}"
    }
}
