---
memory_schema: 1
as_of: 2026-11-19
status: TASK — session G6, code for the tablet only. G6-HM4 part 1: the PS2 touch layout live, the main app's 2 columns upright, a tablet-only candidate APK, and the tablet run pre-registered. The onn keeps ca53df0d…. Nothing adopted; nothing committed.
---

# G6-HM4 — the PS2 touch controls live (part 1: code, build, pre-registration)

**Inputs, all hashed before code:**
- the design `g6_hm1_2026-11-19/design_written_before_code.md` (`c38dbd82…`) and `user_answers_2026-11-19.md`;
- the amendment `g6_hm1a_2026-11-19/design_amendment_written_before_code.md` (`2272705f…`) and its
  `user_answers_2026-11-19.md`;
- the shoulder addendum `g6_hm1a_2026-11-19/layout_addendum_b.md` (`775f77c7…`).

Records: `G6_HM3_PORTRAIT_SCREEN_2026-11-19.md` (§5: the re-run MET) and `G6_PLACE_PLACEMENT_TEST_2026-11-19.md`.

## Decisions in force

- **The PS2 layout on every system** (amendment §1): D-pad, four face buttons, L1/L2/R1/R2, two absolute sticks with
  L3/R3, Select, Start, End.
- **The shoulders: addendum B2.** The user deferred this to the ergonomics chat, which settled it on Microsoft's
  rule (rank each action by how often it is used; the most-used go nearest the grip):
  - the D-pad at (300, 520) and the right stick at (900, 520);
  - the left stick at (300, 1030) and the face cluster's centre at (900, 1030);
  - L3 and R3 as in the amendment;
  - L2 / L1 / R1 / R2 side by side at y 774, L2 and R2 on the outside, at the addendum's x positions.

  Use `layout_check_b.py`'s B2 numbers exactly; a JVM test re-checks them. The user may change this at the run.
- **The right stick above the face buttons** (Q-L1 (a)).
- **The sticks** (amendment §3): absolute; dead zone 0.1 r; clamp 1; a finger keeps its stick until it lifts; the
  sign as G6-HM2's `stickY` (up positive; the sender stores `-AXIS_Y`); X right-positive. L3 / R3 are XUSB
  `LEFT_THUMB` 0x0040 / `RIGHT_THUMB` 0x0080.
- **`TOUCH_LIVE` true:**
  - D2's 5-s rule from the gameplay release, again after each unpause, with the countdown;
  - Q2 (d)'s 2-s takeover;
  - End;
  - Back swallowed;
  - Q1 (c)'s status panel.
- **The main app upright (Q-B4 (a))**, amendment §4 (a): with the handheld choice on, a touchscreen, and the measured
  width under 960 dp, the catalog grid uses 2 columns; the cards stay 300 dp. Behind `useHandheldGameScreen()` only.
  The onn's path is unchanged. Also check that Settings fits upright, the one part §4 could not explain. If something
  is cut off there, fix it behind the same condition or list it.
- **The weak-signal notice (Q-B5): nothing in the app.** Wi-Fi scanning and Bluetooth scanning off is part of the
  tablet's setup (the plan's tablet setup note).
- **Q-PAD (b):** the takeover is proved by JVM tests here and live at G6-S4. No pad pairs to the tablet.

## Rules

- **Code for the tablet only.** The onn's code paths stay as they are, shown as at G6-HM3:
  - `NativeStreamActivity`'s manifest element is byte for byte the same;
  - every hook's default is today's expression;
  - `PadSlots.kt` and `PointerGuard.kt` are unchanged;
  - the `MainActivity` change sits behind `useHandheldGameScreen()`.
- No adb, no install, no stream, no service restart, nothing fetched. The companion and `tools/` are untouched.
- The onn keeps `ca53df0d…`, and the pins are not moved.
- Preflight: no game, gradle or other Claude Code session running. If one is, stop and say so.
- Record `git status --short` and the baseline at the start. Touch no other session's files.

## Steps

1. Code, as above, in the existing files: `TouchPadState`, `HandheldStreamActivity` / `TouchPadView`, `TouchPlayerRules`,
   and `MainActivity` behind the condition. The `handheld` report block gains:
   - `layout: "ps2"`;
   - `p1_join_after_release_ms`;
   - `takeovers`;
   - `controls_pressed`: the set, by control name;
   - `stick_max_deflection` per stick and direction.
2. JVM tests:
   - each stick's four directions and sign, the clamp and the dead zone;
   - a stick and a button held together;
   - a stick finger leaving its base;
   - L3 / R3 bits pinned;
   - B2's non-overlap and minimum sizes (as `layout_check_b.py`);
   - all 16 controls reachable by a press at their centre;
   - the 2-column rule (on with handheld + touchscreen + width < 960 dp; off otherwise, the onn's case included).

   All earlier tests pass unchanged.
3. `gradlew --offline :app:testDebugUnitTest :app:assembleDebug`.
   - The candidate goes to `PrivyHub/app/build/g6_hm4_candidate/`, plus a copy named
     `PrivyHub-handheld-preview-<sha8>.apk` for sending.
   - Preserve the previous `build/outputs` APK first, as G6-HM3 did.
4. The onn-unchanged checks (as G6-HM3 §3), the diff, `git diff --check`, `git apply -R --check`, and the redaction
   check on the Kotlin files and the records.
5. **Pre-register the tablet run, hashed before it:** `docs/memory/evidence/g6_hm4_2026-11-19/preregistration.md`.

   **Conditions:**
   - no other session running, the onn not streaming, outside 03:45–05:30Z;
   - the travel router's 5 GHz network (its name redacted in this copy), Wi-Fi and Bluetooth scanning off;
   - **the tablet within about 1 m of the travel router** (the link was shown fine there in G6-PLACE P1);
   - the handheld screen on;
   - a PS2 game.

   **The user's steps** (plain words):
   1. Install the candidate as an update.
   2. Start the game and wait for the touch controls to take Player 1 after the countdown.
   3. Press each of the 16 controls once, in an order printed in the steps.
   4. Push each stick fully up, down, left and right.
   5. Play freely for at least 2 minutes.
   6. Tap End.
   7. After End, hold the tablet upright on the main screen and look at the catalog and Settings.

   **Cells:**

   | Cell | What |
   |---|---|
   | c1–c3 | as G6-HM3 |
   | c4 | as G6-HM3 (`max_output_gap_ms` ≤ 250, `max_rx_to_decode_ms` ≤ 100) |
   | c5 the join | `touch_slot` 0 and `p1_join_after_release_ms` in 5000–5300 |
   | c6 every control | `controls_pressed` holds all 16 |
   | c7 sticks | each stick's deflection ≥ 0.9 in all four directions |
   | c8 End | `end_presses` 1 and one bye after ≥ 60 s PLAYING |

   **The verdict rule:** met when c1–c8 are met. A miss is reported with its value, and the fix goes into a new
   candidate.

   **The user's remarks, recorded as said and not cells:**
   - whether each control is reachable without moving the grip (the shoulders above all);
   - the stick feel;
   - the countdown;
   - the status panel;
   - the main app's 2 columns and Settings upright.

   Hash it (`preregistration.sha256`, the time in `preregistration_hashed_at.txt`).
6. Record: `docs/memory/evidence/G6_HM4_TOUCH_LIVE_2026-11-19.md` (part 1; part 2 is added after the run), a patch note
   in `docs/memory/patches/` with its `PATCH_INDEX.md` row, the plan's dated line, and `CURRENT.md`'s G6 line. Write
   `logs/g6_hm4_git_status.txt` with this task's files only.

**Gates:**
- every JVM test passes;
- BUILD SUCCESSFUL;
- the onn-unchanged checks pass;
- `git diff --check` is clean;
- the redaction check is clean;
- `tools/check_memory_health.py` passes.

No address, serial, token or pairing code; device ids as 4 hex digits and "…"; no game title. Nothing adopted; nothing
committed by you.

Your last reply begins "YOU, now: commit", then:
- the candidate's sha256;
- the tests (count, failures);
- the onn-unchanged checks, one line each;
- the pre-registration's sha256;
- the user's steps exactly as pre-registered, numbered.
