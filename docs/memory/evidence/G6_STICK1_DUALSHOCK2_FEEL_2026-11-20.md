---
memory_schema: 1
as_of: 2026-11-20
status: RECORD — G6-STICK1 NOT MET as pre-registered, on c4 alone (max_rx_to_decode_ms 126 > 100; every other cell met; the user: "Done, it feels a lot better. Much more smooth and responsive" — §7). Part 1: the touch sticks as a DualShock 2 end to end (dead zone 0.1, full at 0.75 of the throw — the user's choice, first 0.9 — the circle to the square, PCSX2's AxisScale 1.33 compensated on the tablet); candidate 786cb2f8… tablet only; the run pre-registered as preregistration_v2.md (3cb6fe05…, 16:56:07Z), superseding b297729d… before any run. No hub change, no restart. The onn keeps ca53df0d…. Nothing adopted. Part 2 after the run.
---

# G6-STICK1 — DualShock 2 stick feel (part 1: the trace, the mapping, build, pre-registration; 2026-11-20)

Task: `../handoffs/G6-STICK1_DUALSHOCK2_FEEL_TASK.md` (a byte-for-byte copy of the Cowork file). Patch note:
`../patches/G6_STICK1_DUALSHOCK2_FEEL.md`. Files: `g6_stick1_2026-11-20/`. G6-HM5 / G6-HM6 stay reserved.
G6-SCREEN1b's run is scored in `G6_SCREEN1B_PS2_PS1_FILL_2026-11-20.md` §7 (NOT MET; the previous app and the companion
before its restart).

**The user (verbatim, 2026-11-20):**
- "Left analog movement on rotations would be too slow sometimes."
- "Yep, making feel like true dualshock 2 is a good idea"

**Preflight (16:28Z, `preflight.txt`):**
- G6-SCREEN1b committed (`b2716e17`).
- No game running; the last session ended 16:26:50Z.
- No gradle running; the other two sessions idle; outside 03:45–05:30Z.

## 1. B1 — the chain, traced (read only)

1. **The touch point → `TouchPadState.stickDeflection`** (`PrivyHub/…/streaming/TouchPadState.kt`, `stickVector`):
   - the offset over the throw (r 115.5 px = 0.875 × 132);
   - 0 inside 0.1 of it, with no ramp: just past the dead zone the value jumps to 0.1;
   - clamped to the unit circle.
   - Until G6-STICK1, `output()` sent `round(v × 32767)` per axis.
2. **→ `NativeControllerSender.writePlayerState`:** the int16 stored as given (`ly` positive up).
3. **→ the hub** (`companion/native_session_io.py`):
   - its uinput "PrivyHub Virtual Gamepad" axes are `AbsInfo(min −32768, max 32767, flat 128)`;
   - `ABS_X` / `ABS_RX` are written as sent (`_clamp_axis`), `ABS_Y` / `ABS_RY` sign-flipped (`_invert_axis`);
   - no scaling.
4. **→ SDL → PCSX2** (`data/games/ps2/config/PCSX2/inis/PCSX2.ini` as the hub launches it):
   - `[InputSources] SDL = true, SDLControllerEnhancedMode = true`;
   - `[Pad1] Type = DualShock2, Deadzone = 0, AxisScale = 1.33, ButtonDeadzone = 0, InvertL/R = 0`;
   - the sticks bound to `SDL-0/±LeftX|Y`, `±RightX|Y` (Pad2 the same keys at their defaults);
   - the hub's `settings_for` / `pad_sections` (`companion/ps2_session.py`) never write `Deadzone` or `AxisScale`, so
     these are PCSX2's defaults;
   - B77's input profiles change bindings only; the per-title game settings files carry no pad keys.
   - **Nothing else shapes the sticks.**
   - SDL's Linux driver applies the uinput `flat` (128 = 0.4 %) only with its dead-zone hint on, which is off by
     default.
5. **PCSX2's DualShock 2 value**, as PCSX2 2.x is understood (not read from its source: nothing fetched):
   - per direction `raw = min(255, floor(v × 1.33 × 255))`;
   - merged `127 + (raw + 1) // 2` (positive) or `127 − raw // 2` (negative);
   - centre 127, full 255 / 0.

**Today vs new, end to end** (`b1_table.py`, output `b1_table.txt`; the DualShock 2 byte and its fraction of full, per
axis). The middle column is the first mapping (full at 0.9, pre-registration v1, superseded). The last column is the
mapping built, full at 0.75:

| Push (of the throw) | Direction | Today | Full at 0.9 (v1) | **Full at 0.75 (built)** |
|---|---|---|---|---|
| 50 % | cardinal | 212 (0.664) | 191 (0.500) | **205 (0.609)** |
| 75 % | cardinal | 254 (0.992) | 231 (0.812) | **255 (1.000)** |
| 90 % | cardinal | 255 (1.000) | 255 (1.000) | **255 (1.000)** |
| 100 % | cardinal | 255 (1.000) | 255 (1.000) | **255 (1.000)** |
| 50 % | 45° diagonal, each axis | 187 (0.469) | 191 (0.500) | **205 (0.609)** |
| 75 % | 45° diagonal, each axis | 217 (0.703) | 231 (0.812) | **255 (1.000)** |
| 90 % | 45° diagonal, each axis | 235 (0.844) | 255 (1.000) | **255 (1.000)** |
| 100 % | 45° diagonal, each axis | 247 (0.938) | 255 (1.000) | **255 (1.000)** |

**Said plainly:**
- **PCSX2's 1.33 already squares the diagonal most of the way.** Today a full diagonal reaches **0.938** per axis, and
  a cardinal push is full from **0.752** of the throw.
- So the full-push diagonal deficit is only about 6 %. The rest of "rotations too slow" is most likely the thumb
  riding inside the ring while circling: at 75–90 % of the throw a diagonal gives 0.70–0.84 today, against 0.81–1.00
  now.
- **The other side, which Cowork should see:** the end-to-end-linear target makes a **cardinal** push softer in the
  middle of the throw. 75 % gives **0.812** (today 0.992, because PCSX2's 1.33 saturated it early), and full comes at
  90 % instead of 75 %. That is the task's design ("does not saturate early").
- **The user's decision (2026-11-20, verbatim): "Yep that sounds reasonable. We can always iterate later"**, to full at
  **0.75** of the throw instead of 0.9. That is where PCSX2's 1.33 already made a straight push full today, and the
  user's earlier "10-15% smaller" throw was tuned on that feel. A straight push now reaches full where it did today
  (and a little sooner below it: 50 % gives 0.609 against 0.664), and every diagonal reaches full at the same 75 %.

## 2. B2 — the mapping (`TouchPadState.kt`, `object Ds2Stick`; the touch pad's own path only)

1. Dead zone 0.1 of the throw.
2. Linear past it, full at **0.75** of the throw (the user's choice; first 0.9); the outer quarter is full.
3. The circle mapped to the square (× 1 / max(|cos θ|, |sin θ|)): a full 45° push is full on both axes; a cardinal one
   is unchanged.
4. **PCSX2's 1.33 compensated on the tablet:**
   - each axis's target `t` is sent as `round(t / 1.33 × 32767)`, and a full target as 32767 (PCSX2 clamps it);
   - within 1e-4 of full counts as full, because float rounding at 45° gives 0.99999994 against PCSX2's 1/128 step;
   - the end-to-end residual is at most 1/127 (tested over 1000 targets each way).
5. The throw (0.875), the drawn ring, the press area, ownership until lift and the signs are unchanged. The knob and
   the report's `stick_max_deflection` keep the circular deflection.
6. Real controllers, the onn and every non-touch path are untouched: only `TouchPadState.output()` (the touch pad)
   uses it.

## 3. B3 — the report (the handheld block, per stick `left` / `right`)

- `stick_out_max` (the largest sent int16 per direction).
- `stick_diag_max` (`sent`: the largest min(|x|, |y|) sent; `end_to_end`: its PCSX2 fraction by the model above).
- `stick_edge_frac` (owned time at ≥ 0.75 of the throw, where the output is full).
- `stick_mag_hist` (10 bins of owned time by magnitude, 0–1 of the throw, past the ring in the last; sampled at the
  100-ms tick).
- `stick_mapping` `"ds2-square-0.75-c1.33"` (the first build, full at 0.9: `"ds2-square-0.9-c1.33"`).
- `stick_max_deflection` is kept as it was.

## 4. Tests and build (`tests_jvm.txt`, `build_console.txt`; full at 0.75: `tests_jvm_v2.txt`, `build_console_v2.txt`)

**Full at 0.75 (the build in force), 16:55Z:** BUILD SUCCESSFUL, **377 tests, 0 failures**. `G6Stick1Test` now pins
full at 0.75 (and not at 0.74), a full 45° push at 0.75 full on both axes end to end, the ramp `(m − 0.1) / 0.65`
monotonic, the string `"ds2-square-0.75-c1.33"` and the edge fraction at ≥ 0.75. `G6TouchPs2Test`'s half-throw
assertion becomes 0.4 / 0.65 end to end. **Candidate:**
**`786cb2f8e78cf1e07bb2e5a7a67db663ff380ec3ba70144933c0701c68706a8a`** (`g6_stick1_candidate/app-debug.apk`, also
`PrivyHub-handheld-preview-786cb2f8.apk`). The first build, `PrivyHub-handheld-preview-3d4a7203.apk`, is kept beside it.

The first build (full at 0.9), as recorded then:

- `gradlew --offline :app:testDebugUnitTest :app:assembleDebug`: **BUILD SUCCESSFUL, 377 tests, 0 failures** (16:32Z;
  SCREEN1b: 370).
- **New, `G6Stick1Test` (7):**
  - the dead zone;
  - full at 0.9 and never beyond, not saturated at 0.89;
  - a full 45° push full on both axes end to end in all four corners (and at 0.9; a half 45° push half on both);
  - cardinal values monotonic, keeping their direction and the target end to end;
  - the 1.33 compensation and its residual;
  - the touch pad sends the mapping while the knob keeps the circle;
  - the report's figures.
- **Updated, disclosed** (they pinned the old circular, uncompensated sent values that the task replaces), in
  `G6TouchPs2Test`:
  - `theClampAndTheDeadZone`: the full diagonal is now 32767 / 32767, not 23170 / 23170;
  - `fullDeflectionAt0875OfTheOldRadius`: half the throw is now half end to end (sent 12318, not 16384), and
    G6-HM4's 80 % (91 % of the throw) is now full.
  - Every other test unchanged and passing.
- **A first build failed 2 tests** on the 45° float rounding above (24637 sent instead of full); fixed with the 1e-4
  rule.
- **Candidate:** `PrivyHub/app/build/g6_stick1_candidate/app-debug.apk`, sha256
  **`3d4a7203a64f8ac3dcd13eb65d4e718175edde36074095641dad290adefd160a`** (also `PrivyHub-handheld-preview-3d4a7203.apk`).
  SCREEN1b's `adcb1222…` was copied first to `PrivyHub/app/build/g6_stick1_preserved_outputs/`.

## 5. Checks

- **The onn unchanged** (`onn_unchanged_checks.txt`, by `onn_checks_stick1.py`, against `b2716e17`):
  1. the manifest's element `4d36c0bb…` as pre-G6;
  2. `NativeStreamActivity` not changed, hook defaults 10 / 10;
  3. `PadSlots.kt` and `PointerGuard.kt` unchanged since pre-G6;
  4. `MainActivity` not changed;
  5. nothing under `companion/`, `tools/` or `data/` changed.
  - The onn keeps `ca53df0d…`; the pins are not moved.
- **The diff** (`g6_stick1.diff`): `git diff --check` clean, `git apply -R --check` OK. The redaction check is clean.
- **The companion already runs G6-SCREEN1b's commit:** committed 08:18:57Z, the unit active since 08:19:07Z, no
  companion file changed since. G6-STICK1 needs no restart.

## 6. The run, pre-registered (`preregistration_v2.md`; first `preregistration.md`)

**`preregistration.md` (`b297729d…`, 16:34:29Z) was superseded before any run.** At 16:54Z no decoder report had come
in after its hash time, and no report in `logs/games/decoder_sessions/` carries a `ds2-square` mapping string. It stays
as hashed and is not edited. **`preregistration_v2.md`** is identical except the candidate's hash (and its sha8 file
name) and the mapping string in "Which session" and c13 (`"ds2-square-0.75-c1.33"`): sha256
**`3cb6fe0510a6bd85e2d4d73cd9c67311396103c1a02d0bcdd2dda493710b5390`**, hashed at **2026-11-20T16:56:07Z**. It is the one
the run is scored by.

The first pre-registration, as recorded then:

- sha256 **`b297729d0a40ecd11d6f4ea646329d772560d213242f279b9a95885ad3f39596`**, hashed at **2026-11-20T16:34:29Z**.
- G6-SCREEN1b's, copied exactly, changing only:
  - the candidate;
  - the companion condition (already on SCREEN1b's commit);
  - "Which session" (this candidate's `stick_mapping`; older-app sessions noted and skipped);
  - one added step 5 (the diagonal corners, two slow circles, each stick), so the later steps and control 16's
    pointer move by one;
  - c12: each stick's `stick_diag_max.end_to_end` ≥ 0.95;
  - c13: `stick_mapping` = `"ds2-square-0.9-c1.33"`;
  - three remarks: the diagonals, DualShock 2 feel, anything too twitchy.

## 7. Part 2 — the run, scored (G6-STICK1S, 2026-11-20; read only)

Figures as extracted: `g6_join1_2026-11-20/stick1_part2_figures.txt`.

**Pre-registration intact:** `preregistration_v2.md` sha256 `3cb6fe05…` checks OK; hashed at 16:56:07Z.

**The session** (its "Which session" rule): the first tablet PS2 handheld session after the hash whose report shows
`stick_mapping` `"ds2-square-0.75-c1.33"`.
- No session came between the hash and it.
- Launch 17:11:25Z (class `remote-direct`); `session_started` 17:11:42.363Z → `session_end_bye` 17:15:54.413Z
  (**252.05 s PLAYING**).
- Report `native_decoder_20261120_171554_547.json` (`2d312bf8…`, 265 s).

| Cell | Value | Bound | Verdict |
|---|---|---|---|
| c1 decode | `OMX.Exynos.avc.dec`, hardware true, low latency true | hardware, low latency | **MET** |
| c2 rate | `recent_fps` 60.12 | ≥ 58 | **MET** |
| c3 drops | decoder 51 / 15885 = 0.32 %; video 0 / 15885 | each ≤ 1 % | **MET** |
| c4 latency | `max_rx_to_decode_ms` **126**; `max_output_gap_ms` 148 | ≤ 100; ≤ 250 | **NOT MET** |
| c5 the join | `touch_slot` 0; `p1_join_after_release_ms` 5021 | 0; 5000–5300 | **MET** |
| c6 every control | `controls_pressed` 16 of 16 | all 16 | **MET** |
| c7 sticks | left 1, 1, 1, 1; right 1, 1, 0.999, 1 | each ≥ 0.9 | **MET** |
| c8 End | `end_presses` 1; one bye after 252.05 s PLAYING | 1; ≥ 60 s | **MET** |
| c9 the box | `1200x900`; `1200x1100` | as bound | **MET** |
| c10 the crop (PS2) | `"4:3"`; `"160,0,960x720"` | as bound | **MET** |
| c11 the hub's handheld launch | `20261120-121123-ps2.log` 17:11:23.423Z: `PS2 handheld: widescreen patch off for this launch only (the title's setting: off)` | present | **MET** |
| c12 the diagonals | `stick_diag_max` left 0.992 (sent 24609), right 1.0 (sent 32767), end to end | each ≥ 0.95 | **MET** |
| c13 the mapping | `"ds2-square-0.75-c1.33"` | equal | **MET** |

**Verdict by the pre-registered rule: G6-STICK1 NOT MET, on c4 alone** (`max_rx_to_decode_ms` 126 > 100). No
threshold changes after the hash.

**c4's slow rows, as the report has them** (`slow_events_top_latency`: elapsed ms, rx-to-decode, feed delay, codec,
codec in flight, queue depth, output gap), every row ≥ 100 ms:

| Elapsed | rx→decode | feed delay | codec | in flight | queue | output gap |
|---|---|---|---|---|---|---|
| 3277 | 126 | 73 | 52 | 2 | 3 | 42 |
| 3306 | 110 | 44 | 65 | 1 | 3 | 28 |
| 3332 | 107 | 83 | 24 | 2 | 1 | 25 |
| 3343 | 107 | 85 | 21 | 1 | 1 | 11 |
| 4561 | 104 | 4 | **100** | 1 | 2 | 47 |
| 7312 | 112 | 98 | 14 | 1 | 2 | 93 |
| 7376 | 117 | 108 | 8 | 1 | 0 | 48 |
| 7392 | 112 | 94 | 17 | 0 | 0 | 15 |

They sit in the first 8 s of the session, mostly feed delay (73–108 ms). One, at 4.56 s, is codec time (100 ms):
Cowork's preview did not list it. Nothing is read into them beyond what the files show.

**c4 compared** (`max_rx_to_decode_ms`, with `max_output_gap_ms`, figures only):

| Session | rx→decode | output gap |
|---|---|---|
| G6-HM3 (`154811_583`) | 74 | 936 |
| G6-PLACE P1 (`170414_871`) | 56 | 64 |
| G6-PLACE P2 (`170835_621`) | 90 | 918 |
| G6-HM4 (`193238_516`) | 60 | 173 |
| G6-HM4b (`221003_090`) | 55 | 75 |
| G6-SCREEN1b scored (`081452_382`) | 50 | 538 |
| 2026-11-20 free play, 38 handheld reports 04:20–16:26Z | 26–117 (117 at `161940_868`; every other ≤ 91) | — |
| **G6-STICK1 scored (`171554_547`)** | **126** | 148 |
| after it, the same candidate (`172025_181`, `172510_613`, `172604_123`) | 53, 31, 38 | 61, 73, 51 |

**G6-STICK1 changed no decode code.** Its diff (`g6_stick1.diff`, `6cfdb746`) touches `TouchPadState.kt`,
`HandheldStreamActivity.kt` (the touch mapping and the report) and two tests only: no decoder, `NativeStreamActivity`
or stream file.

**Context, not cells:**
- `touch_writes` 7556, `takeovers` 0, `back_swallowed` 0;
- 0 lost packets, 0 resyncs, no link notice;
- `stick_edge_frac` left 0.657 / right 0.668;
- `stick_mag_hist` left `[0.01, 0.022, 0.052, 0.059, 0.059, 0.045, 0.063, 0.07, 0.049, 0.571]`, right `[0.031,
  0.031, 0.043, 0.062, 0.018, 0.018, 0.104, 0.074, 0.086, 0.533]`.

**The user's remark, verbatim (2026-11-20):** "Done, it feels a lot better. Much more smooth and responsive".
- **Not given** (recorded as not given; the user was not asked): the reach of each control without moving the grip,
  the countdown, the status panel, the main app's 2 columns and Settings, the bigger picture, End's place, the optional
  PS1 session, turning through the diagonals, DualShock 2 feel, anything too twitchy.
