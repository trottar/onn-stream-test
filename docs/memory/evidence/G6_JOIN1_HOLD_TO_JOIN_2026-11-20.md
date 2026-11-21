---
memory_schema: 1
as_of: 2026-11-20
status: RECORD — G6-JOIN1 NOT MET as pre-registered (c4 gap 283 ms; c7 and c12 the right stick short); the change under test, the hold-to-join (c5), met — §6; the user: "done, worked just as expected". Part 1: holding any touch control for a real pad's join hold (500 ms) during the countdown makes the touch pad P1 at once; the 5-s countdown stays as the fallback; the joining press is not sent. Candidate 6d2fff76… tablet only; the run pre-registered (ce8fdb41…, 17:31:57Z). No hub change, no restart. The onn keeps ca53df0d…. Nothing adopted. Part 2 after the run.
---

# G6-JOIN1 — hold any touch button to be P1 (part 1: reading, code, build, pre-registration; 2026-11-20)

Task: `../handoffs/G6-JOIN1_HOLD_TO_JOIN_TASK.md` (a byte-for-byte copy of the Cowork file). Its Part A (G6-STICK1S,
`../handoffs/G6-STICK1S_SCORE_TASK.md`) is recorded as part 2 of `G6_STICK1_DUALSHOCK2_FEEL_2026-11-20.md`: **NOT MET
on c4 alone** (`max_rx_to_decode_ms` 126 > 100; c1–c3 and c5–c13 met). Patch note: `../patches/G6_JOIN1_HOLD_TO_JOIN.md`.
Files: `g6_join1_2026-11-20/`. G6-HM5 / G6-HM6 stay reserved.

**The user's request (verbatim, 2026-11-20):** "Before we run this, I also think I'd rather be able to hold any button
on virtual controller. We can still keep the 5 seconds but if I hold a virtual button that registers P1"

**Preflight (17:27Z, `preflight.txt`):**
- G6-STICK1 committed (`6cfdb746`).
- No game running; the last scored session ended 17:15:54Z and the hub's status was inactive.
- No gradle running; the other two sessions idle; outside 03:45–05:30Z.

## 1. B1 — how P1 is chosen today (read only)

**A physical pad** (`PrivyHub/…/streaming/PlayerPrompt.kt`, B54's hold-to-join):
- `onJoinKey`: an unclaimed pad's keys are consumed, not sent. A down of a face button (A / B / X / Y) or Start starts
  a hold.
- `tick` (the activity ticks every 50 ms while a hold is pending): a hold of **`HOLD_MS` = 500 ms** joins the pad as
  the next player (`join`). The joining key goes into `needsUp`: **not sent to the game until lifted**.
- The join shows a 2-s "P1" badge (`BADGE_MS`) and the line "P1 joined — hold to add Player 2". A tap (an up before
  500 ms) does nothing.

**The touch pad** (G6-HM2's D2, `TouchPlayerRules.kt` `TouchP1Rule`; `HandheldStreamActivity`'s 100-ms tick):
- The rule is armed at the first gameplay release after a start (not a self-restart). At `WAIT_MS` = 5000 ms, with
  P1 free, `tick` returns `JOIN_P1` and the activity calls `PlayerPrompt.joinAsP1WithoutHold` (the same `join`: badge
  and stored count). A real pad on P1 before then ends the rule (`GIVE_UP`, the status panel).
- "A touch during the wait does not join early." Until the touch pad holds a slot, its touches send nothing
  (`onPadOutput` returns without a slot).
- `takeOverP1` lets a real pad's 2-s hold take P1 from the touch pad (Q2 (d)); unchanged here.
- The line read "Touch buttons: P1 in 5…" during the countdown, then "Touch buttons: Player 1".

## 2. B2 — the change (`TouchPlayerRules.kt`, `TouchPadState.kt`, `HandheldStreamActivity.kt`; the touch pad only)

1. **`class TouchHoldJoin`:**
   - `observe(held, now)` on every touch event and tick: a control's hold starts when it is first seen held and ends
     when it is lifted;
   - `step(now, rule, p1Free, p1HeldByRealPad)` on the tick: while the countdown runs (`rule.armed()`) and no device
     holds P1, any touch control held ≥ **`PlayerPrompt.HOLD_MS` (500 ms, the physical hold)** → **`HOLD`**, and the
     countdown is cancelled (no timer join, no countdown text);
   - otherwise the countdown's own tick → **`TIMER`** at 5 s as before.
   - The controls are the D-pad, the face buttons, the shoulders, both sticks, L3 / R3, Select and Start. End is its
     own view and never a pad control.
2. **Shorter than 500 ms:** nothing; the countdown goes on. A new hold starts from its own down.
3. **P1 taken** (a real pad, or the countdown already joined), or no countdown yet: a hold does nothing new.
4. **The joining press is not sent:**
   - the controls held at a hold-join go into a suppressed set, sent through `TouchPadState.output(skip)` (those
     fingers, a stick's deflection included, left out) until each is lifted;
   - as a real pad's `needsUp`; other controls are sent at once.
5. **The line during the countdown:** "Hold any button to join · P1 in 5…" (then "Touch buttons: Player 1" as before).
6. **End:** unchanged at all times (its own Button view; not part of the hold rule).
7. **The report** (the handheld block):
   - `p1_join_via`: `"hold"`, `"timer"`, or `"none"` before a join;
   - `p1_join_hold_ms`: 500, the hold time used;
   - `p1_join_after_release_ms`: unchanged.
8. **Untouched:** `PlayerPrompt.kt`, `NativeStreamActivity`, `MainActivity`, real controllers, the onn.

## 3. Tests and build (`tests_jvm.txt`, `build_console.txt`)

- `gradlew --offline :app:testDebugUnitTest :app:assembleDebug`: **BUILD SUCCESSFUL, 384 tests, 0 failures** (17:31Z;
  G6-STICK1: 377).
- **New, `G6Join1Test` (7):**
  - the hold time is `PlayerPrompt.HOLD_MS` 500;
  - a 500-ms hold on each of the 15 touch controls joins with `"hold"` (not at 499 ms), stops the countdown, and no
    timer join follows;
  - a 450-ms hold does nothing and the countdown goes on; a new hold starts from its own down;
  - no hold → `"timer"` at 5000 ms, once;
  - with P1 held by a real pad, by the touch pad already, or before the countdown, a hold does nothing;
  - the joining press is not sent (`output(skip)`; a stick's deflection too), other controls are;
  - End is never a pad control.
- Every earlier test unchanged and passing.
- **Candidate:** `PrivyHub/app/build/g6_join1_candidate/app-debug.apk`, sha256
  **`6d2fff764d4380d4d03b52d64cd1379de13085ab7526bde1634bbf96aacaf207`** (also `PrivyHub-handheld-preview-6d2fff76.apk`).
  G6-STICK1's `786cb2f8…` was copied first to `PrivyHub/app/build/g6_join1_preserved_outputs/`.

## 4. Checks

- **The onn unchanged** (`onn_unchanged_checks.txt`, by `onn_checks_join1.py`, against `6cfdb746`):
  1. the manifest's element `4d36c0bb…` as pre-G6;
  2. `NativeStreamActivity` not changed, hook defaults 10 / 10;
  3. `PadSlots.kt` and `PointerGuard.kt` unchanged since pre-G6;
  4. `MainActivity` not changed;
  5. nothing under `companion/`, `tools/` or `data/` changed.
  - The onn keeps `ca53df0d…`; the pins are not moved. No restart needed: the companion still runs G6-SCREEN1b's
    commit, and G6-JOIN1 changes nothing on the hub.
- **The diff** (`g6_join1.diff`): `git diff --check` clean, `git apply -R --check` OK. The redaction check is clean.

## 5. The run, pre-registered (`preregistration.md`)

- sha256 **`ce8fdb412d96ae24cfef026a0faa3edd5f6a51fe9dea737e6f8def2e7e837624`**, hashed at **2026-11-20T17:31:57Z**.
- G6-STICK1's `preregistration_v2.md`, copied exactly, changing only:
  - the candidate's hash (and its sha8 file name);
  - "Which session": a report with `p1_join_via`, i.e. this candidate; older apps noted and skipped;
  - step 2: hold ✕ during the countdown until "Touch buttons: Player 1", about 0.5 s;
  - c5: `touch_slot` 0, `p1_join_via` `"hold"`, `p1_join_after_release_ms` < 5000;
  - one added remark: whether holding to join feels right.
- The header note was rewritten for this run, as for every earlier new run.

## 6. Part 2 — the run, scored (G6-JOIN1S, 2026-11-21; read only)

Figures as extracted: `g6_swap1_2026-11-21/join1_part2_figures.txt`.

**Pre-registration intact:** `preregistration.md` sha256 `ce8fdb41…` checks OK; hashed at 17:31:57Z.

**The session** (its "Which session" rule: a report with `p1_join_via`):
- **Skipped, older app:** 17:31:58.466Z → 17:39:15.945Z, `native_decoder_20261120_173916_032.json`
  (`stick_mapping` present, no `p1_join_via` key: G6-STICK1's app).
- **Scored:** launch 17:43:02Z (class `remote-direct`); `session_started` 17:43:11.058Z → `session_end_bye`
  17:46:46.939Z (**215.9 s PLAYING**); report `native_decoder_20261120_174647_052.json` (`734c1867…`, 220 s); its
  launch's game log `20261120-124301-ps2.log`.

| Cell | Value | Bound | Verdict |
|---|---|---|---|
| c1 decode | `OMX.Exynos.avc.dec`, hardware true, low latency true | hardware, low latency | **MET** |
| c2 rate | `recent_fps` 59.51 | ≥ 58 | **MET** |
| c3 drops | decoder 8 / 13168 = 0.06 %; video 1 / 13168 = 0.01 % | each ≤ 1 % | **MET** |
| c4 latency | `max_rx_to_decode_ms` 62; `max_output_gap_ms` **283** | ≤ 100; ≤ 250 | **NOT MET** |
| c5 the join | `touch_slot` 0; `p1_join_via` `"hold"` (`p1_join_hold_ms` 500); `p1_join_after_release_ms` 2530 | 0; `"hold"`; < 5000 | **MET** |
| c6 every control | `controls_pressed` 16 of 16 | all 16 | **MET** |
| c7 sticks | left 1, 1, 1, 1; right up **0.823**, down 0.942, left **0.706**, right 1 | each ≥ 0.9 | **NOT MET** |
| c8 End | `end_presses` 1; one bye after 215.9 s PLAYING | 1; ≥ 60 s | **MET** |
| c9 the box | `1200x900`; `1200x1100` | as bound | **MET** |
| c10 the crop (PS2) | `"4:3"`; `"160,0,960x720"` | as bound | **MET** |
| c11 the hub's handheld launch | `20261120-124301-ps2.log` 17:43:01.238Z: `PS2 handheld: widescreen patch off for this launch only (the title's setting: off)` | present | **MET** |
| c12 the diagonals | `stick_diag_max` left 1.0 (sent 32767); right **0.93** (sent 22971), end to end | each ≥ 0.95 | **NOT MET** |
| c13 the mapping | `"ds2-square-0.75-c1.33"` | equal | **MET** |

**Verdict by the pre-registered rule: G6-JOIN1 NOT MET** (c4, c7, c12). No threshold changes after the hash.
- **The change under test, the hold-to-join (c5), was met:** joined by the hold, 2530 ms after the release.
- **c7 and c12 are the right stick** not pushed fully up, left and into a corner in this session (figures only).
- **Beside them, figures only:** the right stick's largest sent values (`stick_out_max`) were up 32767 (full end to end
  under the 0.75 mapping), down 32767, left 23248 (0.945 end to end), right 32767; c7 reads the circular deflection.
  `stick_edge_frac` left 0.729, right 0.307.
- **c4's gap, as the report has it** (`slow_events_top_gap`: elapsed ms, rx-to-decode, feed delay, codec, codec in
  flight, queue depth, output gap): **[50037, 7, 1, 5, 1, 0, 283]**, then [8624, 30, 13, 17, 2, 2, 80], [1606, 16, 4,
  12, 2, 3, 78], [1339, 12, 1, 11, 1, 2, 74], [10076, 6, 0, 5, 1, 1, 73], [7570, 18, 2, 15, 1, 2, 67], [20824, 10, 0,
  9, 1, 0, 65], [3070, 11, 3, 8, 2, 1, 61]. One gap of 283 ms at 50.0 s, with rx-to-decode 7 ms; the next largest is
  80 ms.

**Context, not cells:**
- `touch_writes` 8486, `takeovers` 0, `back_swallowed` 0;
- 2 lost video packets, 0 resyncs, 1 FEC group unrecoverable;
- no link notice; class `remote-direct`.

**The user's remark, verbatim (2026-11-20):** "done, worked just as expected".
- **Not given** (recorded as not given; the user was not asked): the reach of each control without moving the grip,
  the countdown, the status panel, the main app's 2 columns and Settings, the bigger picture, End's place, the optional
  PS1 session, turning through the diagonals, DualShock 2 feel, anything too twitchy, whether holding to join feels
  right (beyond the remark above).
