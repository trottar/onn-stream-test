---
memory_schema: 1
as_of: 2026-11-06
baseline_commit: 795d80d4 (clean; B42 built in /tmp/b_q06n_b42, integrated by the coordinator)
---

# B42 — the screen-loss hold and stable slots on by default (`surface_hold` / `pad_slots`: absent / empty / junk = ON, `0` / `off` off)

**Classification: BUILT**, in the form B13 / B19 / B25 / B27 used. This follows the user's decisions of 2026-11-06:
**G-A11 yes** (the hold on by default) and **G-A12 yes** (stable slots on by default), after HOME-2's C1' and C4' were
met on `0132b944…` (CONFIRMED).
- **Tests:** `HoldAndSlotsDefaultOnTest` 6 new; JVM **201 / 201** (195 + 6), three runs. A mutation back to the old
  parses fails 5.
- **Proof** `proof_zero_is_today.md`: **PROVEN**. Only the two flag objects changed, and `0` / `off` give the CONFIRMED
  build's absent.
- **Host suites:** as the queue-N baseline line for line (43 OK; the four `tools/` tests fail in a copy as at every
  baseline). No host code changed.
- NOT ADOPTED as a host line (none needed); no live run; nothing committed; not installed.

Design `b42_2026-11-06/design_written_before_code.md`, sha256 `ea051792…ccae1`, hashed **17:52:57Z**, before any B42
code. Precondition: only the companion and `privyhub-diag` active (`units_at_start.txt`).

## 1. Built (`b42.diff`)

**`SurfaceHoldFlag` (`SurfaceHold.kt`):**

| value | `0132b944…` | B42 |
| --- | --- | --- |
| absent / empty / a failed read | off | **ON, 12 000 ms** |
| `1` | 12 000 | 12 000 |
| an integer 10 000-30 000 | that bound | that bound |
| `0` / `off` | off | **off** (B32's absent) |
| junk (`yes`, `9999`, `30001`, `-5`, `OFF`, …) | off | **ON, 12 000 ms** |

**`PadSlotsFlag` (`PadSlots.kt`):**

| value | `0132b944…` | B42 |
| --- | --- | --- |
| absent / empty / a failed read | off | **stable** |
| `stable` | stable | stable |
| `off` / `0` | off | **off** (today's first-input order; `0` as B27's convention) |
| junk (`1`, `Stable`, `junk`, …) | off | **stable** |

- **The off words:** `0` and `off` turn either flag off, matched after `trim()`, lower-case exact. The queue names `0`
  for the hold and `off` for the slots; accepting both on both means the same word works on either property (`OFF` is
  junk, so on, as B25's single exact off word).
- **Nothing else changed:**
  - B32 / B34 / B38 / B39's behaviour is untouched. Only the two objects' `parse` and failed-read `catch` changed (plus
    one header line each).
  - `NativeStreamActivity.kt` is byte-equal to the base. Its two consumers (`padSlots`, `surfaceHold`) build their
    objects from `fromSystem()` exactly as before. Their comments still read "(null = today)", which is now the `0` /
    `off` case; left unedited to keep the activity byte-equal.
  - The player prompt (`debug.privyhub.player_prompt`, B41) stays opt-in and is not touched here.

## 2. The host: no change; what it will see

The host reads neither property. It acts on the client's keys. From an APK with B42, with no property set:
- **every session sends `pad_slots`** (the start query and each heartbeat). So:
  - the host writes a `pad_slots` recovery row at each start (and on a change);
  - **B38's changed-only counter turns on for every session:** the heartbeat row's `updates_by_player` is the change
    count, and `packets_by_player` carries the old per-packet count;
  - `/status` gains `changes_by_player`; its own `updates_by_player` stays per-packet (the `tools/` probes read it so);
  - so **a record comparing `updates_by_player` across this change must read `packets_by_player` for the old meaning**.
- **every foreground loss** gives a `surface_lost` row and the report's `surface_hold` object.
- B36's keeper and `diag_read` already read all of these.

## 3. Tests (`tests_jvm.txt` ×3, `tests_hold_and_slots_default_on.xml`, `tests_mutations.txt`)

**`HoldAndSlotsDefaultOnTest` (new, 6):**
- the hold on for absent / empty / blank / twelve junk values / a failed read; its values `1` / 10000 / 20000 / 30000
  kept; off only for `0` / `off`;
- the slots stable for absent / empty / `stable` / junk / a failed read; off only for `off` / `0`;
- **the off words give today's absent:** `0132b944…`'s two parses copied verbatim into the test. For `0` and `off` the
  new parse returns exactly what the old one returned for absent (null / false). Every value the old parse turned on
  gives the same value.

**Edited existing lines (disclosed, as B13 / B19 / B25):**
- `SurfaceHoldTest.theFlagIsOffUnlessOneOrABoundInRange`: `null` / `""` / `yes` / `9999` / `30001` → 12 000 (were null);
  `fromSystem()` → 12 000 (was null). `0` → null kept. The test's name is kept.
- `PadSlotsTest.theFlagIsStableOnly`: `null` / `""` / `1` / `Stable` / `junk` → true (were false); `0` → false kept;
  `fromSystem()` → true (was false). The name is kept.
- `VirtualRemoteNoSlotTest.absentIsToday`: `null` / `""` / `1` → true (were false); `off` → false added.

**The mutation:** both main files back to their predecessors with the tests kept → **5 fail** (the two new on-tests and
the three moved flag tests).

## 4. Proof (`proof_zero_is_today.py` / `_output.txt`, `proof_zero_is_today.md`)

- Every changed line of `SurfaceHold.kt` (11) and `PadSlots.kt` (5) lies inside `object SurfaceHoldFlag` /
  `object PadSlotsFlag`, or is one comment line in the header above it. 0 elsewhere.
- The only consumers are the activity's two lazies, unchanged.
- With `0` / `off` they receive null / false, exactly as `0132b944…` with no property: no `SurfaceHold`, no `PadSlots`,
  today's paths. **PROVEN.**

## 5. For HOME-3 (the coordinator's handoff)

- **C1'' — the hold with no property.**
  - **Do:** install the APK with every property empty (`adb shell getprop debug.privyhub.surface_hold` reads empty);
    start a game; press the remote's Home and come back within 3 s; play ~30 s; exit with Back.
  - **Pass:**
    - a recovery row `"event": "surface_lost"`, `"outcome": "held"`, `away_ms` < 12000;
    - no `restart_fast` and no `session_ended` at the return;
    - the exit's report: `surface_hold.held` 1, `losses` 1, `restarted` 0.
  - **Off check:** `adb shell setprop debug.privyhub.surface_hold 0` → a Home press of ~3 s gives today's restart
    (`restart_fast`, no `surface_lost` row, no `surface_hold` key); then `setprop … ""`.
- **C4'' — two pads with no property.**
  - **Do:** every property empty; two pads paired; a two-player PS1 title. Press pad B first; exit and relaunch; press
    pad A first; then in one session only pad A ~5 s, then only pad B ~5 s.
  - **Pass:**
    - both starts write `"event": "pad_slots", "when": "start"` with `count` 2: slots 0 and 1, the same two pad hashes,
      no `google`-class entry;
    - the heartbeat rows' `updates_by_player` rises only on the pressed pad's slot; `packets_by_player` on all four.
  - **Off check:** `adb shell setprop debug.privyhub.pad_slots off` → no `pad_slots` row or key, no `packets_by_player`;
    then `setprop … ""`.

## 6. Files

- **`b42_2026-11-06/`:** `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
  `predecessors/` (the five files) + `predecessor_sha256.txt`; the design + `design.sha256` + `design_hashed_at.txt`;
  `b42.diff`; `proof_zero_is_today.py` / `_output.txt` / `.md`; `tests_jvm.txt`,
  `tests_hold_and_slots_default_on.xml`, `tests_mutations.txt`, `tests_regression_after.txt`; `after_sha256.txt`;
  `redact_check.py` / `.txt`; `manifest.sha256`.
- **Elsewhere (in the copy; the coordinator applies):** `SurfaceHold.kt`, `PadSlots.kt`; `HoldAndSlotsDefaultOnTest.kt`
  (new); `SurfaceHoldTest.kt`, `PadSlotsTest.kt`, `VirtualRemoteNoSlotTest.kt` (flag lines moved).
  `patches/B42_HOLD_AND_SLOTS_DEFAULT_ON.md`.
- **Left in /tmp:** `b_q06n_b42` (the copy), `b_q06n_b42_scratch/mut1/`, `b_q06n_b42_gradle1-3.txt`.
- **The rules held:** no stream, no companion restart, no adb, no sudo, no nft; `privyhub-diag` and `~/privyhub_diag/`
  untouched; the tree's code untouched; nothing fetched, deleted, adopted or committed.
