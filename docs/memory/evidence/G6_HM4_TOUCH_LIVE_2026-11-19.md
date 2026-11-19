---
memory_schema: 1
as_of: 2026-11-19
status: RECORD — G6-HM4 NOT MET by its pre-registered rule (c6: SELECT and START not pressed; c7: the right stick up 0.379 / left 0.791). c1–c5 and c8 met (join 5007 ms; worst gap 173 ms). By the user's own account the misses are steps not followed in full, not a code fault; the verdict stands. Candidate 12bb09e7… on the tablet only; the onn keeps ca53df0d…. Nothing adopted.
---

# G6-HM4 — the PS2 touch controls live (part 1: code, build, pre-registration; 2026-11-19)

Task: `../handoffs/G6-HM4_TOUCH_LIVE_TASK.md`. Patch note: `../patches/G6_HM4_TOUCH_LIVE.md`.

**The inputs, all hashed before code:**
- the design `g6_hm1_2026-11-19/` (`c38dbd82…`) with its answers;
- the amendment `g6_hm1a_2026-11-19/` (`2272705f…`) with its answers;
- addendum B2 (`layout_addendum_b.md`, `775f77c7…`), the shoulders as settled by the ergonomics chat at the user's
  request.

**Preflight (19:02Z, `g6_hm4_2026-11-19/preflight.txt`):**
- no game and no gradle process;
- three other Claude Code session processes exist, all idle: no children, ~0 % CPU, transcripts last written 12+ h
  earlier; only this session was active;
- baseline `7fb2518a`; the tree held only the user's prompt file (`git_status_at_start.txt`).

## 1. What was written

| File | Change |
|---|---|
| `TouchPadState.kt` (+106, −6) | `Kind.PS2`: addendum B2's numbers exactly (the object `Ps2TouchLayout`), scaled from the measured size. The new controls `LSTICK`, `RSTICK`, `L3`, `R3`. Absolute sticks: dead zone 0.1 r, clamped to the unit circle, a finger keeps its stick until it lifts, up and right positive. L3 / R3 = XUSB 0x0040 / 0x0080. `heldControls()`, `stickDeflection()`, `endRect()`, and the press-area sizes in `Drawn`. `Kind.PS1` (G6-HM2's layout) stays the default, so G6-HM2's tests run unchanged; the app uses PS2. The 6 replaced lines are this file's own G6 lines (the class line, the control list, `Drawn`, its mapping, the output's return) |
| `HandheldStreamActivity.kt` (+120, −42) | `TOUCH_LIVE = true` and the PS2 pad. End is a view on B2's End rectangle (`PadArea`), on top of the pad and the status panel. The countdown line, then "Touch buttons: Player 1". The sticks drawn with a knob at the deflection; held controls drawn lighter. The edge-gesture exclusion moved to the shoulders (the controls at the edges). The report's `handheld` block gains `layout`, `p1_join_after_release_ms`, `takeovers`, `controls_pressed` and `stick_max_deflection` |
| `HandheldInput.kt` (+15) | `HandheldGeometry.catalogColumns`: 1 on the TV guide list; 2 with the handheld choice on a touchscreen device narrower than 960 dp; else 3 |
| `MainActivity.kt` (+11, −0) | after today's column assignment, one statement inside `if (!tvGuideListPage && useHandheldGameScreen())` |
| `G6TouchPs2Test.kt` (new, 11 tests) | see §2 |

**Settings upright (the one part the amendment's §4 could not explain), listed, not changed.**
- `showCompanionSettings()` (`MainActivity.kt:1053+`) has no fixed width: a vertical container with 24 dp padding,
  holding text fields, check boxes and hint lines.
- It has no scroll view. That limits height, not width, and the tablet upright is 1333 dp tall.
- No cause of a cut-off was found in the code. The user looks at it in step 7 of the run.

## 2. Build and tests (`tests_jvm.txt`, `build_console.txt`)

- **`gradlew --offline :app:testDebugUnitTest :app:assembleDebug`: BUILD SUCCESSFUL.** **357 tests, 0 failures, 0
  errors, 0 skipped** (346 earlier, unchanged, plus 11 new). One compiler warning, in an existing line
  (`MainActivity.kt:10117`, `SHOW_IMPLICIT`).
- **The new tests (`G6TouchPs2Test`):**
  - the layout equals B2's centres, and End is at (960, 70);
  - each stick's four directions and the sign;
  - the clamp and the dead zone;
  - a stick and a button together;
  - a stick finger leaving its base;
  - L3 / R3 bits;
  - B2's non-overlap (End included), the bottom tenth, the shoulders 1 cm above it, and the minimum sizes;
  - all 16 controls reachable at their centres (End's centre claimed by no pad control);
  - scaling with the measured size;
  - PS1 still the default;
  - the 2-column rule (the onn's case included).
- **The candidate:** `PrivyHub/app/build/g6_hm4_candidate/app-debug.apk`,
  sha256 `12bb09e72126a93f2c1c45ced62c0f390c37bb399bfc826080e220c1ecae6514` (also `PrivyHub-handheld-preview-12bb09e7.apk`).
  The previous `build/outputs` APK (`1d658a3f…`, G6-HM3's) was copied first to `PrivyHub/app/build/g6_hm4_preserved_outputs/`.

## 3. The onn is unchanged (`onn_unchanged_checks.txt`)

1. The manifest's `NativeStreamActivity` element is byte for byte as before any G6 code (`f52ce75b`; `4d36c0bb…`);
   G6-HM4 does not touch the manifest.
2. G6-HM4 does not touch `NativeStreamActivity.kt`. Every hook's default is still today's expression; the 9 lines
   replaced since `f52ce75b` are G6-HM3's, as listed there.
3. `PadSlots.kt` and `PointerGuard.kt` are unchanged since `f52ce75b`.
4. `MainActivity.kt`: +11 / −0. The only statement sits inside `useHandheldGameScreen()`, which needs a touchscreen
   and the stored choice.
5. `companion/` and `tools/` are untouched. The onn keeps `ca53df0d…`, and the pins are not moved.

`git diff --check` is clean; `git apply -R --check g6_hm4.diff` is OK. The redactor is clean on the Kotlin files and
the records.

## 4. Part 2 — the tablet run, scored (2026-11-19; scored by G6-HM4B)

**Pre-registration intact:** `preregistration.md` sha256 `0fbaf9f2…` checks OK; hashed at 19:09:08Z.

**The session (verified):**
- the only tablet game session after the hash: recovery-log session 16, a PS2 game;
- `launch_ports` 19:29:26.5Z, `session_started` 19:29:34.7Z, `session_end_bye` 19:32:38.4Z (`client_frame` 11230):
  **183.7 s PLAYING**;
- decoder report `logs/games/decoder_sessions/native_decoder_20261119_193238_516.json` (`4bab27a3…`, received
  19:32:38.516Z, `duration_ms` 187738), with a `handheld` block, `layout` `ps2`, `touch_live` true.

Figures as extracted: `g6_hm4b_2026-11-19/hm4_part2_figures.txt`.

| Cell | Value | Bound | Verdict |
|---|---|---|---|
| G6-HM4.c1 decode | `OMX.Exynos.avc.dec`, hardware true, low latency true | hardware, low latency | **MET** |
| G6-HM4.c2 rate | `recent_fps` 59.61 | ≥ 58 | **MET** |
| G6-HM4.c3 drops | decoder 7 / 11236 = 0.06 %; video 1 / 11236 = 0.01 % | each ≤ 1 % | **MET** |
| G6-HM4.c4 latency | `max_rx_to_decode_ms` 60; `max_output_gap_ms` 173 | ≤ 100; ≤ 250 | **MET** |
| G6-HM4.c5 the join | `touch_slot` 0; `p1_join_after_release_ms` **5007** | 0; 5000–5300 | **MET** |
| G6-HM4.c6 every control | `controls_pressed` **14 of 16**: `SELECT` and `START` absent | all 16 | **NOT MET** |
| G6-HM4.c7 sticks | left: up 1, down 1, left 1, right 1; right: **up 0.379**, down 1, **left 0.791**, right 0.993 | each ≥ 0.9 | **NOT MET** (the right stick's up and left) |
| G6-HM4.c8 End | `end_presses` 1; one bye after 183.7 s PLAYING | 1; ≥ 60 s | **MET** |

**Verdict by the pre-registered rule: G6-HM4 NOT MET** (c6 and c7). No threshold changes after the hash.

**Context (not cells):**
- `touch_writes` 5852; `touch_events` 4094; `pointer_exempted_events` 4099;
- `takeovers` 0 (no pad, as expected); `back_swallowed` 0;
- `video.lost_packets` 2 (0 in resyncs), `fec_unrecoverable_groups` 1, **0 sequence resyncs**, 1 stall signal;
- no `link_notice_shown`;
- the order of first presses: RSTICK, LSTICK, CROSS, TRIANGLE, CIRCLE, SQUARE, R1, L1, L2, R2, DPAD, R3, L3, END.

**The user's remarks and answers, verbatim (2026-11-19):**
- "Overall played pretty nice. I think the sticks might actually have too much give. When driving I really had to
  pull them pretty far for turning. Maybe like 10-15% smaller would be excellent."
- Asked whether they pressed SELECT and START and pushed the right stick fully up and left: "I used the right stick
  naturally, but never clicked select and start thAt was an oversight".

**Reading of the misses (recorded, not re-scored).** By the user's own account, c6's miss (SELECT and START never
pressed) and c7's miss (the right stick not pushed fully up and left; it was used "naturally") were steps of the run
not followed in full. They are not a fault found in the code. NOT MET stands as scored.

**Next:** G6-HM4b (`G6_HM4B_SHORTER_STICKS_2026-11-19.md`): the sticks' throw about 12.5 % shorter, as the user
asked, a new candidate, and the run pre-registered again with steps that are harder to miss.
