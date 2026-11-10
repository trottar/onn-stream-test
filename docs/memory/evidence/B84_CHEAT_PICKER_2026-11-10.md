---
memory_schema: 1
as_of: 2026-11-10
status: BUILT, NOT INSTALLED (session B, queue AE) — the cheat picker as PrivyHub's own screen: Launch / Cancel fixed at the top (Left from any row, the pad's Start), a filter, sections collapsed with counts, paging; in APK c801caab… (pinned, NOT installed). Default on; debug.privyhub.cheat_picker=0 = today's dialog. Nothing committed. No title, serial, path or identifier in this record
---

# B84 — the cheat picker, usable from the couch (2026-11-10)

**Why:** HOME-12's C46 (`HOME_12_PARITY_2026-11-10.md`): Android's multi-choice dialog puts "Launch Cheat Session"
after every entry in D-pad order; on a 677-entry list the user held Down a minute and never reached it — "we need to
fix this bloat first".

**Baseline:** HEAD `c514c543` (HOME-12 committed); `git status --short` empty at the check; only the companion and
`privyhub-diag` active (`b84_2026-11-10/`). **Design** hashed before code at 21:12:02Z (`design.sha256`).

## What was built (`b84.diff`)

- **`streaming/CheatPicker.kt`:** `CheatPicker` (the property, the words) and **`CheatPickerModel`** — the screen's
  whole behaviour, pure Kotlin: rows (the bar, the filter row, a header per section, the entries of opened sections),
  the focus, the keys, the filter, the sections, the selection.
  - **Launch at the top:** "Launch Cheat Session · Cancel · n selected" fixed above the list; **Left from any row** puts
    the focus on Launch, OK launches (two presses); **the pad's Start launches** (one press); Back / the pad's B cancels;
    Up from the filter row reaches the bar; Down from the bar returns to the row the focus came from.
  - **A filter row:** OK opens the on-screen keyboard; typing narrows the list to entries with every typed word (any
    order, any case); Right on the filter row toggles **"Selected only"**.
  - **Sections** from B85's groups — General, Player 1 … Player 4, Other, Your files — **collapsed to their header with
    a count** until OK opens one; under a filter the matching sections show open with the match counts. A variant (B85)
    sits indented under its first.
  - **Paging:** L1 / R1, the remote's Channel ± and Page ± move a screen.
  - **The selection** survives filtering, "Selected only" and closing a section; Launch sends the ticked entries'
    indexes as today (the hub keeps the selection as the game's saved cheat profile, as today).
- **`MainActivity.kt`:** `showGameCheatEntryDialog` opens **`showCheatPickerScreen`** when the property is on: a
  full-screen dialog with the bar and the filter row as fixed views and a **`ListView` over the model's rows** (the
  platform reuses row views; only visible rows are laid out). Launch / Cancel call exactly what today's buttons call.
- A hub without B85 (or `raw=1`): every entry in one General section.

## The switch

`debug.privyhub.cheat_picker=0` (or `off`) → `showGameCheatEntryDialog` runs today's code unchanged
(`proof_flag_absent.md`).

## Tests (`B84CheatPickerTest.kt`, 11, JVM)

Launch in ≤ 2 presses from **every** row of a 300-entry list with all sections open (Left, OK) and Start alone;
Up / Down around the bar; Cancel and Back; the key codes; **the sections' counts** collapsed (headers only) and their
labels; **the filter** (words in any order, no match, cleared); **Start launches the ticked indexes**; **the selection
survives** a filter, "Selected only" and closing a section; **2,092 entries open as the bar, the filter and six headers
— no entry row — built in well under a second**, an opened section lists only its own rows, a filter over 2,092 under a
second; paging by a screen (never into the bar); no groups → one General section; the property.

- 3 runs: 11 / 11 each (`tests_x3.txt`). Mutations: **6 / 6 caught** (`tests_mutations_jvm.txt`).
- The whole JVM suite in the work copy 294 / 294; in the APK tree 283 / 283 (`b86_2026-11-10/tests_jvm_apk_copy.txt`).

## Disclosed

- **The jump key is Left, not Up** (stated in the hashed design): Up must still move one row up inside the list; the
  queue's measured rule (Launch in ≤ 2 presses from any row) holds, and Start launches in one.
- **The Android view is not exercised on the JVM:** the project has no Robolectric and nothing may be fetched to add it.
  The tests drive the model the screen runs; the dialog, the `ListView` and the keyboard are HOME-12's C49 at the TV.
- The filter row's keyboard: while typing, the keyboard owns the keys; Down or Back leaves it.

## Files

`b84_2026-11-10/`: start files, the design + hash, `b84.diff`, `proof_flag_absent.md`, `tests_x3.txt`,
`tests_mutations_jvm.txt`, `scripts/` (`mutate_jvm.sh`, `jvm_mutations.sh`), redact / title checks,
`manifest.sha256`. The APK's files are in `b86_2026-11-10/`. Patch note: `patches/B84_CHEAT_PICKER.md`.
