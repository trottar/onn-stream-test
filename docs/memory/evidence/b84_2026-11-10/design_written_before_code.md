# B84 — the cheat picker, usable from the couch (client; design, written and hashed before code)

**Baseline:** HEAD `c514c543` (HOME-12 committed). **Switch:** default on; `debug.privyhub.cheat_picker=0` (or `off`) =
today's dialog, byte for byte the same code path (`showGameCheatEntryDialog` unchanged and called as today).

## What exists (read at HEAD)

- Extras → Cheats → `showGameCheatProfilesDialog` (saved profiles from the hub, then "New Cheat Session") →
  `showGameCheatSourceDialog` (one source: straight on; several: a single-choice source list) →
  **`showGameCheatEntryDialog`**: Android's `AlertDialog.setMultiChoiceItems` over every entry of the source, the
  buttons "Launch Cheat Session" / "Cancel" after the whole list in D-pad order (HOME-12 C46: 677 entries, the user
  held Down a minute and never reached them). Launch sends `cheat_source` + the ticked entries' `index` values
  (`launchGameOnCompanion(…, cheatSourceIndex, cheatEnabledIndexes, cheatProfileLabel)`); the hub then keeps the
  selection as the game's saved cheat profile (listed next time at the top of the Cheats list) — **"kept per game as
  today" = this flow, unchanged.**
- Tests: plain JUnit on the JVM (no Robolectric in the project; nothing may be fetched to add it). The project's
  client tests drive pure Kotlin objects (`Ps2Patches`, `DiscSafe`, …) that the activity uses.

## The design

1. **`streaming/CheatPicker.kt`** (new):
   - `object CheatPicker`: `PROPERTY = "debug.privyhub.cheat_picker"`, `parse()` / `fromSystem()` as `Ps2Patches`
     (absent / anything but `0` / `off` = on); the words on the TV.
   - `class CheatPickerModel(entries, pageSize)` — **the screen's whole behaviour, pure Kotlin**: the rows, the focus,
     the keys, the filter, the sections, the selection. The Android view only draws `rows` and forwards keys.
     - **Entries** from the source's `entries` (B85's fields when present: `description` = the cleaned label, `group`
       = `general | player1..4 | other | yours`, `variant_of`; a hub without B85 or `raw=1` → every entry `general`).
     - **Rows:** `Bar` (row 0: "Launch Cheat Session" · "Cancel" · "n selected"), `Filter` (row 1: the filter text and
       "Selected only"), then per non-empty section in the order General, Player 1 … Player 4, Other, Your files: a
       `Header` ("Player 1 (461)") and, **only when that section is open**, its `Entry` rows (a variant right after its
       first, indented). Sections start **collapsed** (headers only) — a 2,092-entry list opens as ≤ 9 rows.
     - **Keys** (Android key codes, mapped to actions by one function): Up / Down move one row; **Left on any row moves
       the focus to Launch** (one press from anywhere; then OK = Launch: two presses); Up on the filter row reaches the
       bar too; on the bar Left / Right move between Launch and Cancel and Down returns to the row the focus came from;
       **the pad's Start = Launch** (one press); **Back / the pad's B = Cancel**; OK on a header opens / closes it, on
       an entry ticks / unticks it, on "Selected only" toggles it; **L1 / R1, the remote's Channel ± and Page ± move
       the focus a screen** (`pageSize` rows).
     - **Filter:** typing (the on-screen keyboard on the filter row) narrows the list to entries whose label contains
       every typed word (case-folded); while a filter or "Selected only" is on, the matching sections show open and
       their headers count the matches. **The selection is kept across filters, "Selected only" and collapsing.**
     - **Launch:** the selected entries' `index` values in the source's order and their labels for the profile label
       (as today); none selected → today's "No cheats selected" message.
   - **Deviation from the queue's wording, stated here:** the queue says "one Up from anywhere". Up must still move
     one row up inside the list, so the one-press jump to Launch is **Left** (unused in a vertical list), and Up does
     it from the filter row; the measured test is the queue's: Launch in ≤ 2 presses from any row.
2. **`MainActivity.kt`:** in `showGameCheatEntryDialog`, when the switch is on, open **`showCheatPickerScreen`**
   instead of the multi-choice dialog: a full-screen `android.app.Dialog` holding the bar (two buttons and the count),
   the filter row (`EditText` + a "Selected only" toggle) and a **`ListView` with a `BaseAdapter` over the model's
   rows** (the platform recycles row views: only the visible rows are laid out); keys go to the model and the view
   redraws. Launch / Cancel call exactly what today's dialog's buttons call. The switch off → today's code.
3. **No hub change in B84** (B85 adds the fields; the picker works on today's raw list too).

## Tests (`app/src/test/java/streaming/B84CheatPickerTest.kt`, the model the screen runs)

Fake catalogs (made-up labels): **Launch in ≤ 2 presses from every row** (focus each row, Left then OK → Launch;
Start alone → Launch); the bar's Cancel and Back → Cancel; **the filter** narrows and its words match in any order;
**the sections' counts** (collapsed headers, the counts under a filter); **Start launches** the ticked indexes;
**the selection survives** a filter, "Selected only" and closing a section; **2,092 entries**: the model builds and
lists ≤ 9 rows within the time budget, an opened section lists only its own rows; paging by `pageSize`; a hub without
B85 (no `group`) → one General section; the property (`0` / `off` = today). Mutations of the key lines. The Android
view (dialog, `ListView`) is not exercised on the JVM (no Robolectric) — disclosed; HOME-12's C49 is its check.
