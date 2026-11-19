---
memory_schema: 1
as_of: 2026-11-19
status: PLAN — the G6 tablet handheld track (ROADMAP §G6). G6 OPEN 2026-11-19 at secondary priority; G6-S1 MET; G6-S2 … G6-S6 and G6-HM1 … G6-HM6 proposed, none started. Nothing adopted.
---

# G6 — the tablet handheld track (2026-11-19)

`docs/ROADMAP.md` §G6 "Portable handheld validation" was explicitly pending at the G9 checkpoint (row 10: no
representative handheld). The hardware now exists: a **Samsung Galaxy Tab S6 Lite (2020), SM-P610** (Exynos 9611,
2000×1200). This file records the track, its conflict rules, the portrait-mode result and the user's decisions.

**Sources:** the user's briefs `../handoffs/G6_TABLET_PROJECT_HANDOFF_2026-11-19.md` and
`../handoffs/G6_PORTRAIT_INVESTIGATION_HANDOFF_2026-11-19.md`; Cowork's notes
(`../evidence/g6_s1_2026-11-19/G6_TABLET_PLAN_2026-11-19_cowork_notes.md`). The portrait investigation's full report
is the user's own document, kept out of this public repo.

**Labels.** "Verified" = read in the source or the logs. "Proposed" = planned, not built. "The user" = the user's
decision. Nothing perceptual is a cell.

## 1. Ids

The user's steps T1–T6 are **G6-S1 … G6-S6** (`T1`–`T3` are D-BASE findings; `T88` / `T89` are game codes). The
portrait stages are **G6-HM1 … G6-HM6**. A cell is `G6-S<n>.c<m>` or `G6-HM<n>.c<m>`, never a bare `C<n>`.

## 2. The track

| Id | User's step | Aim | State |
|---|---|---|---|
| G6-S1 | T1 | The CONFIRMED APK unchanged: install, launch, catalog, touch, connect, one stream | **MET** 2026-11-19 (`../evidence/G6_S1_TABLET_FIRST_INSTALL_2026-11-19.md`) |
| G6-S2 | T2 | Tablet interface fixes: launcher, touch, scaling, orientation, navigation | proposed |
| G6-S3 | T3 | 720p60 hardware decode, continuity, audio, UDP and latency with the existing diagnostics; the 3-min hold | proposed |
| G6-S4 | T4 | A controller on the tablet: mappings, player slots, input latency | proposed |
| G6-S5 | T5 | Battery at 50 % brightness; reversible optimizations only after the baseline | proposed |
| G6-S6 | T6 | The physical handheld (grips / a telescopic pad); no purchase before the software is validated | proposed |

The user's battery target: about four hours of streaming from 100 % to 20 %. The user's reference: Firefox video uses
about 10 % per 30 min at 50 % brightness.

## 3. Conflict rules

- **The tablet is never connected to the hub's adb** (USB or wireless debugging). Verified: `tools/e1_suite.py`
  (`sh(["adb", *args])`) and `tools/c3_l4_nft_night.py` (`adb devices`, `adb shell …`) call bare `adb` with no `-s`.
  A second adb device makes them fail with "more than one device", the nightly included. G6-S1 installed by
  sideloading the APK file.
- **The prompt file is `_cowork_prompt_g6.txt`**, never another session's (`_cowork_prompt.txt` = A, `_b` = B, `_c` = C;
  `COMMUNICATION.md`).
- **Secondary priority.** G6 yields to every other chat and session and **never runs alongside another session's run**.
  One companion, one stream: a tablet game stream waits until no Code session is running, the onn is not streaming,
  and it is outside 04:30–05:30Z and the 45 min before. The tablet's catalog reads are light HTTP, like the onn's.
- **The onn's pads stay paired to the onn.** No pad pairs to the tablet before G6-S4.

## 4. Portrait handheld mode (read-only investigation, 2026-11-19)

**Result:** feasible with no change to the companion, the decoder or the PHI1 packet.

**Proposed shape:**
- A touch pad writes the existing pad state (XUSB bits, stick shorts, trigger bytes) through one new sender method.
- The video gets a 1200×675 box at the top of the 1200×2000 portrait screen, leaving 1200×1325 for the controls
  (not the brief's 50/50 split).

**Blockers (verified in the source):**
- `NativeStreamActivity` is landscape-locked twice: `android:screenOrientation="landscape"` in the manifest and
  `SCREEN_ORIENTATION_LANDSCAPE` in `onCreate`.
- It declares no `configChanges`, so a rotation rebuilds the activity and ends the session.
- **B70's `PointerGuard` consumes every touchscreen event in a game**: `SOURCE_TOUCHSCREEN` carries the pointer class
  bit (`SOURCE_CLASS_POINTER`, `streaming/PointerGuard.kt`).
- The overlays use fixed landscape margins.

**Architecture (proposed):**
- A handheld subclass of the stream activity with its own manifest entry; today's entry stays byte for byte.
- `TouchPadState` (pure, JVM-tested) and `TouchPadView`; a `TouchPadDevice : PadDevice`.
- A touchscreen-only pointer-guard exemption, in the subclass only.
- A Settings choice in `MainActivity`.
- The view is written in-house: the two mature on-screen pads (RadialGamePad, Moonlight's controls) are GPL-3.0.

## 5. Decisions (the user, 2026-11-19)

| Id | Decision |
|---|---|
| D2 | The touch pad becomes **P1 by default** when no real pad has joined as P1 (the existing long-press join) within **5 s** of the game starting. A later pad takes the next player. |
| D3 | ~~The PS1 layout first.~~ **Replaced 2026-11-19 by D5.** |
| D5 | **The PS2 (DualShock 2) layout on every system**: D-pad, four face buttons, L1 / L2 / R1 / R2, two analog sticks (absolute) with L3 / R3, Select / Start, End. It also replaces Q6 (b). The user: "I decided we should be using PS2 setup for everything because this literally won't work for PS2 and GameCube." (G6-HM1a, `../evidence/g6_hm1a_2026-11-19/`) |
| D4 | Tablet landscape **keeps today's full-screen fill** (about 6.7 % stretched, inferred); no letterbox. |
| D1 | **Partly settled** by D2. Open: portrait as a Settings choice, or following the rotation. |

**Open points:** whether a later pad should take over P1; what the lower region shows when a real pad is P1; D1's rest.

## 6. The portrait stages (proposed, none started)

| Id | Aim |
|---|---|
| G6-HM1 | The design, hashed before any code — done (`c38dbd82…`) |
| G6-HM1a | The amendment: the PS2 layout everywhere, the shoulders lower, the main app upright, the weak-signal notice — written, awaiting approval (`2272705f…`) |
| G6-HM2 | The bench logic and its JVM tests — met; extended at G6-HM4 for the PS2 controls |
| G6-HM3 | Portrait video with an inert pad — **NOT MET** by its rule (c4's gap 936 ms, inside a link stall); the onn's confirmation sits before any APK replaces `ca53df0d…` |
| G6-HM4 | **The PS2 layout live, sticks and L3 / R3 included**; the 5-s rule, the takeover and End live; the new shoulders; the user's picks for the main app upright and the notice |
| G6-HM5 | A latency video (touch → picture); the sticks moved to G6-HM4 |
| G6-HM6 | Live rotation, customization, the battery / heat comparison (feeds G6-S5) |

Each stage starts only on the user's word, under the conflict rules in §3.

**2026-11-19:** G6-HM1 design written, awaiting the user's approval (`../evidence/g6_hm1_2026-11-19/design_written_before_code.md`, sha256 `c38dbd82…` in `design.sha256`). The user's answers to its open questions: `../evidence/g6_hm1_2026-11-19/user_answers_2026-11-19.md` (all answered).

**2026-11-19:** G6-HM2 done (bench): the touch pad's logic and its JVM tests, 346 / 346 pass; no APK; the onn's paths unchanged (`../evidence/G6_HM2_TOUCH_PAD_LOGIC_2026-11-19.md`). Next: G6-HM3 on the user's word.

**2026-11-19:** G6-HM3 part 1 done: the portrait screen with an inert pad, candidate APK `1d658a3f…` for the tablet only; the tablet run is pre-registered (`../evidence/G6_HM3_PORTRAIT_SCREEN_2026-11-19.md`).

**2026-11-19:** G6-HM3 scored **NOT MET** (c4: `max_output_gap_ms` 936 > 250, inside a link stall; c1–c3, c5, c6 met; End met). The user's remarks recorded verbatim (record §4). D3 replaced by D5 (the PS2 layout everywhere). G6-HM1a written and hashed (`../evidence/g6_hm1a_2026-11-19/design_amendment_written_before_code.md`, `2272705f…`), awaiting the user's approval and their picks (Q-HM3, Q-B4, Q-B5, Q-L1, Q-L2, Q-PAD).

**2026-11-19:** the user's answers to G6-HM1a recorded (`../evidence/g6_hm1a_2026-11-19/user_answers_2026-11-19.md`): 2 catalog columns upright in handheld mode; the placement test first; L1 / L2 side by side with L2 outside; the right stick above the face buttons; G6-HM3 re-run as the test's first minute. The side-by-side shoulders re-checked (`layout_addendum_b.md`): no height meets every check within 4–5 cm while only the shoulders move; two alternatives back to the user (Q-L2b). **The placement test pre-registered; the user's run next** (`../evidence/g6_place_2026-11-19/preregistration.md`).

**2026-11-19:** the placement test run and scored (`../evidence/G6_PLACE_PLACEMENT_TEST_2026-11-19.md`). P1, flat about 1 m from the travel router: G6-HM3's re-run **MET** (−32 dBm, no resync, worst gap 64 ms). P2, **lying down at the usual seat** (the user's correction; not held): −70 dBm, resyncs every ~48 s; Wi-Fi scanning off did not remove the pattern. Q-B5: **nothing in the app**; Wi-Fi and Bluetooth scanning stay off on the tablet. Q-L2b: the user's side-by-side choice stands; the re-check's B0 / B1 / B2 go back to the chat that did the ergonomic research, before G6-HM4's pre-registration.

**2026-11-19 — the tablet's setup (Q-B5):** Wi-Fi scanning and Bluetooth scanning off (Android: Settings → Location → Location services); nothing in the app.

**2026-11-19:** G6-HM4 part 1 done (`../evidence/G6_HM4_TOUCH_LIVE_2026-11-19.md`): the PS2 touch controls live with the shoulders as addendum B2 (settled by the ergonomics chat at the user's request), the main app's 2 columns upright in handheld mode, 357 / 357 JVM tests, candidate APK `12bb09e7…` for the tablet only; the tablet run pre-registered (`0fbaf9f2…`). The onn keeps `ca53df0d…`.

**2026-11-19:** G6-HM4's run scored **NOT MET** (c6: SELECT and START not pressed; c7: the right stick up 0.379 / left 0.791). By the user's own account these were steps not followed in full, not a code fault; c1–c5 and c8 met (join 5007 ms, worst gap 173 ms). G6-HM4b part 1 done (`../evidence/G6_HM4B_SHORTER_STICKS_2026-11-19.md`): the sticks' throw 0.875 ×, as the user asked; candidate `965d4f19…` for the tablet only; 358 / 358 JVM tests; the run pre-registered again with steps that are harder to miss (`e9694ff0…`).
