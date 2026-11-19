---
memory_schema: 1
as_of: 2026-11-19
status: RECORD — G6-HM4b NOT MET by its pre-registered rule (c6: 14 of 16, L3 and R3 absent). c1–c5, c7 and c8 met (join 5091 ms; worst gap 75 ms; every stick direction ≥ 0.966). Candidate 965d4f19… on the tablet only; the onn keeps ca53df0d…. Nothing adopted.
---

# G6-HM4b — the sticks' throw about 12.5 % shorter (part 1: code, build, pre-registration; 2026-11-19)

Task: `../handoffs/G6-HM4B_SCORE_AND_SHORTER_STICKS_TASK.md`. Patch note: `../patches/G6_HM4B_SHORTER_STICKS.md`.
G6-HM4's run, scored NOT MET (c6, c7), is in `G6_HM4_TOUCH_LIVE_2026-11-19.md` §4.

**The user's request (verbatim):** "I think the sticks might actually have too much give. When driving I really had to
pull them pretty far for turning. Maybe like 10-15% smaller would be excellent." Cowork's reading is the midpoint:
0.875.

**Preflight (20:15Z, `g6_hm4b_2026-11-19/preflight.txt`):**
- no game running;
- the gradle and Kotlin daemons idle, left by G6-HM4 part 1's build at ~19:07Z (no build running);
- three other Claude Code session processes idle (no children, transcripts last written 12+ h earlier); only this
  session active;
- baseline `43016a37`.

## 1. The change (`TouchPadState.kt`, +8 / −2: the stick constants only)

| | G6-HM4 | G6-HM4b |
|---|---|---|
| full deflection (= the drawn ring) | r 132 px | **r 115.5 px** (0.875 ×) |
| finger travel to full deflection | 15.0 mm | **13.1 mm** (at the panel's ~224 ppi) |
| drawn diameter | 2.79 cm (240 dpi) / 2.99 cm (224 ppi) | **2.44 cm** (240 dpi) / **2.62 cm** (224 ppi) |
| press (catch) area | r 158.4 px, Ø 3.35 / 3.59 cm | unchanged |
| dead zone, clamp, sign, a finger keeps its stick | 0.1 r, 1, up / right positive, until it lifts | unchanged (0.1 of the new r) |

**The 2.5 cm minimum, said plainly.** The amendment's 2.5 cm minimum was for the sticks' drawn size. At 0.875 × the
drawn ring is **2.44 cm** on the stricter 240-dpi measure, **under** the minimum (2.62 cm at the panel's own ~224 ppi).
**The 0.875 throw is kept anyway:** the user asked for it, and the press area, which is what a thumb must land on,
stays 3.35 cm.

**The layout re-check** (`layout_check_hm4b.py`, output `layout_check_hm4b_output.txt`): B2's numbers with the smaller
rings. All checks are OK across 120 press-area pairs, and nothing newly overlaps; the press areas are unchanged. The
sticks' drawn size under 2.5 cm is **reported**, not failed, as the task asks.

## 2. Tests and build (`tests_jvm.txt`, `build_console.txt`)

- `gradlew --offline :app:testDebugUnitTest :app:assembleDebug`: **BUILD SUCCESSFUL. 358 tests, 0 failures, 0 errors,
  0 skipped** (the run at 20:17Z).
- **New in `G6TouchPs2Test`:** `fullDeflectionAt0875OfTheOldRadius` checks:
  - full deflection at 115.5 px;
  - half the throw gives half;
  - G6-HM4's 80 % travel now gives about 91 %;
  - a touch 150 px out, outside the new ring, still lands on the stick.
- **Updated to the new radius** (as the task asks): the four-directions-and-sign test and the clamp / dead-zone test.
- **The minimum-size test** now pins the sticks' ring at 115.5 px and their press area ≥ 2.5 cm, instead of the drawn
  ring ≥ 2.5 cm (disclosed above).
- Every other test is unchanged and passes.
- **The candidate:** `PrivyHub/app/build/g6_hm4b_candidate/app-debug.apk`,
  sha256 `965d4f197213a639fd0277dbbd06f1db2b9c25f1899a5eaace879dabc83d66e5` (also `PrivyHub-handheld-preview-965d4f19.apk`).
  The previous `build/outputs` APK (`12bb09e7…`) was copied first to `PrivyHub/app/build/g6_hm4b_preserved_outputs/`.

## 3. The onn is unchanged (`onn_unchanged_checks.txt`)

1. The manifest's `NativeStreamActivity` element is byte for byte as before any G6 code (`4d36c0bb…`); G6-HM4b does
   not touch the manifest.
2. G6-HM4b does not touch `NativeStreamActivity.kt`; the 7 hook defaults are today's.
3. `PadSlots.kt` and `PointerGuard.kt` are unchanged since `f52ce75b`.
4. G6-HM4b does not touch `MainActivity.kt`; its G6 statement is still inside `useHandheldGameScreen()`.
5. `companion/` and `tools/` are untouched. The onn keeps `ca53df0d…`, and the pins are not moved.

The only code file changed is `TouchPadState.kt`. `git diff --check` is clean; `git apply -R --check g6_hm4b.diff`
is OK. The redactor is clean on the Kotlin files and the records.

## 4. Part 2 — the tablet run, scored (2026-11-19)

**Pre-registration intact:** `preregistration.md` sha256 `e9694ff0…` checks OK; hashed at 20:18:05Z.

**The session (verified):**
- the only tablet game session after the hash: recovery-log session 17, a PS2 game;
- `launch_ports` 22:07:02.2Z, `session_started` 22:07:10.2Z, `session_end_bye` 22:10:03.0Z (`client_frame` 10585):
  **172.8 s PLAYING**;
- decoder report `logs/games/decoder_sessions/native_decoder_20261119_221003_090.json` (`cad1863e…`, received
  22:10:03.090Z, `duration_ms` 176751), with a `handheld` block, `layout` `ps2`, `touch_live` true.

Figures as extracted: `g6_hm4b_2026-11-19/part2_figures.txt`.

| Cell | Value | Bound | Verdict |
|---|---|---|---|
| G6-HM4.c1 decode | `OMX.Exynos.avc.dec`, hardware true, low latency true | hardware, low latency | **MET** |
| G6-HM4.c2 rate | `recent_fps` 59.66 | ≥ 58 | **MET** |
| G6-HM4.c3 drops | decoder 7 / 10590 = 0.07 %; video 0 / 10590 = 0 % | each ≤ 1 % | **MET** |
| G6-HM4.c4 latency | `max_rx_to_decode_ms` 55; `max_output_gap_ms` 75 | ≤ 100; ≤ 250 | **MET** |
| G6-HM4.c5 the join | `touch_slot` 0; `p1_join_after_release_ms` **5091** | 0; 5000–5300 | **MET** |
| G6-HM4.c6 every control | `controls_pressed` **14 of 16**: `L3` and `R3` absent | all 16 | **NOT MET** |
| G6-HM4.c7 sticks | left: up 1, down 0.966, left 1, right 1; right: up 1, down 1, left 0.999, right 1 | each ≥ 0.9 | **MET** |
| G6-HM4.c8 End | `end_presses` 1; one bye after 172.8 s PLAYING | 1; ≥ 60 s | **MET** |

**Verdict by the pre-registered rule: G6-HM4b NOT MET** (c6: L3 and R3 not in `controls_pressed`). No threshold
changes after the hash.

**Context (not cells):**
- `touch_writes` 5680; `touch_events` 4098; `pointer_exempted_events` 4104;
- `takeovers` 0 (no pad); `back_swallowed` 0;
- `video.lost_packets` 0, `fec_unrecoverable_groups` 0, **0 sequence resyncs**, 0 stall signals;
- no `link_notice_shown`;
- the order of first presses: LSTICK, DPAD, CROSS, TRIANGLE, CIRCLE, SQUARE, R2, L2, L1, R1, SELECT, START, RSTICK,
  END. G6-HM4's run on the previous candidate did record L3 and R3; G6-HM4b changed only the sticks' constants.

**The user's remarks, verbatim (2026-11-19, asked once):**

> "Played very nice with no issues"

The question listed L3 / R3, the shorter throw for driving, each control's reach, the stick feel, the countdown, and
the main app's 2 columns and Settings upright. The answer covers them as one remark and does not take them one by one.
- **Not inferred:** whether L3 and R3 were pressed. c6 stays NOT MET as scored.
- **The code read beside it, no claim made:** only the sticks' constants changed since G6-HM4, whose run recorded L3
  and R3. `G6TouchPs2Test` still presses L3 and R3 at their centres (`l3AndR3BitsArePinned`,
  `all16ControlsAreReachableAtTheirCentres`), and `layout_check_hm4b.py` finds no press area over them.

**The user's follow-up, verbatim (2026-11-19):** "I pressed those last time, that was in the list. But they worked fine
then". Asked whether L3 / R3 were pressed in this run, the user chose: **"Skipped them this time"**, because they had
already worked in G6-HM4's run.
- **Reading of c6's miss (recorded, not re-scored):** L3 and R3 were skipped in this run by the user's own account.
  It is a step not followed, not a fault found in the code.
- **G6-HM4's run recorded both** (`G6_HM4_TOUCH_LIVE_2026-11-19.md` §4: `controls_pressed` held `R3` and `L3`).
- **NOT MET stands as scored.**
