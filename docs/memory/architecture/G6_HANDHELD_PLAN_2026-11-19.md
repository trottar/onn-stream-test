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

**2026-11-19:** G6-HM4b's run scored **NOT MET** (c6: 14 of 16, L3 and R3 not in `controls_pressed`). c1–c5, c7 and c8 met: join 5091 ms, worst gap 75 ms, every stick direction ≥ 0.966, no loss, no resync (`../evidence/G6_HM4B_SHORTER_STICKS_2026-11-19.md` §4). The user: "Played very nice with no issues". The user then confirmed L3 / R3 were skipped this run (they had worked in G6-HM4's run): a step not followed, not a code fault; NOT MET stands as scored.

**2026-11-20 (note, read only):** the green-screen hiccup at ≈ 04:20Z: the tablet left the stream activity (Android's "user leave") for 12.1 s, just past the 12 s surface hold, so the hub restarted the stream (`surface_lost`, `outcome` `restarted`); meanwhile the hub's stall recovery ran five save / pause / load cycles (04:20:20–04:20:32Z; picture checks three `static`, two `ok`). The hub kept 60 fps while the tablet was away (44 / 43 in the restart's two seconds), load ≈ 2, GPU ≤ 47 °C. Observed; the cause of the leave not known (`../evidence/G6_SCREEN1_4X3_PICTURE_2026-11-20.md` §0.1).

**2026-11-20 (note):** the tablet now reaches the hub over Tailscale from the user's home Wi-Fi: sessions classed `remote-direct` from 05:48:24Z, the remote ladder in force (floor start, cap 7000 kbps). The 05:49–05:57Z session: 8 min 12 s, no `client_stall`, no link notice, 7 lost packets, 0 resyncs, 59.98 fps, −64 … −73 dBm. One session, not yet a finding. G6-WIFI1 held, not run, not withdrawn (record §0.2).

**2026-11-20:** G6-SCREEN1 part 1 done (`../evidence/G6_SCREEN1_4X3_PICTURE_2026-11-20.md`): the portrait video box 4:3 (1200 x 900; pad region 1200 x 1100), SNES and N64 cropped to fill it (PS2, PS1, GameCube and the rest not: not provable 4:3; PS2 has four widescreen-patched titles), SELECT / START 225 px lower on the screen, End at x 1080, the cluster unchanged on the screen. Candidate `e4263fd9…` for the tablet only; 365 tests pass; the onn unchanged (`ca53df0d…`). The run pre-registered (`eddc7ddc…`, 06:25:50Z); a PS2 game, so its picture stays 16:9 at the top of the box. G6-HM5 / G6-HM6 stay reserved.

**2026-11-20:** G6-SCREEN1b part 1 done (`../evidence/G6_SCREEN1B_PS2_PS1_FILL_2026-11-20.md`), on the user's decisions ("Those wide screen ps2 games are a patch that can be toggled off just for handheld. PS1 should be stretched, it cant be by much"): a handheld launch (`display=handheld`) runs PS2 without its widescreen patch for that launch only (the title's game settings journalled, written off, put back before the launch returns; every launch without the field identical); the tablet crops PS2 on the reply's `widescreen: false` and stretches PS1 (`202,0,876x720` → the 4:3 box, 9.6 % wide). Candidate `adcb1222…` tablet only; the companion to be restarted by the user after the commit. A savestate loaded across the two modes can show the wrong shape (record §1.4). G6-SCREEN1's run superseded, not run.

**2026-11-20:** G6-SCREEN1b's run scored **NOT MET** as pre-registered (c4, c6, c7, c9, c10, c11): the scored session (08:12–08:14Z) ran the previous app and the companion before its restart, by the user's own sequence, not a code fault (`../evidence/G6_SCREEN1B_PS2_PS1_FILL_2026-11-20.md` §7). After the restart the user's free play showed the 4:3 box, the PS2 crop and the hub's handheld line (context). The user: "It ran super well. I think the analog could use a little fine tuning"; "Left analog movement on rotations would be too slow sometimes."

**2026-11-20:** G6-STICK1 part 1 done (`../evidence/G6_STICK1_DUALSHOCK2_FEEL_2026-11-20.md`): the touch sticks as a DualShock 2 end to end (dead zone 0.1, full at 0.9 of the throw, the circle to the square, PCSX2's AxisScale 1.33 compensated on the tablet). Traced: PCSX2's 1.33 already brought a full diagonal to 0.938; the new mapping makes it 1.000, and a mid-throw cardinal push softer (75 %: 0.992 → 0.812). Candidate `3d4a7203…` tablet only; no hub change, no restart; the run pre-registered (`b297729d…`, 16:34:29Z), carrying SCREEN1b's screen cells.

**2026-11-20:** G6-STICK1 retuned on the user's decision ("Yep that sounds reasonable. We can always iterate later"): full at **0.75** of the throw instead of 0.9, where PCSX2's 1.33 already made a straight push full; the rest of the mapping as built. Candidate `786cb2f8…` tablet only; the first pre-registration (`b297729d…`) superseded before any run; the run pre-registered as `preregistration_v2.md` (`3cb6fe05…`, 16:56:07Z).

**2026-11-20:** G6-STICK1's run scored **NOT MET on c4 alone** (`max_rx_to_decode_ms` 126 > 100, slow rows in the session's first 8 s, mostly feed delay; G6-STICK1 changed no decode code); c1–c3 and c5–c13 met: all 16 controls, both sticks full, diagonals 0.992 / 1.0 end to end, the 4:3 crop and the hub's handheld line (`../evidence/G6_STICK1_DUALSHOCK2_FEEL_2026-11-20.md` §7). The user: "Done, it feels a lot better. Much more smooth and responsive".

**2026-11-20:** G6-JOIN1 part 1 done (`../evidence/G6_JOIN1_HOLD_TO_JOIN_2026-11-20.md`), on the user's request ("if I hold a virtual button that registers P1"): during the countdown, any touch control held for a real pad's join hold (500 ms) makes the touch pad P1 at once; the 5-s countdown stays as the fallback; the joining press is not sent until lifted. Candidate `6d2fff76…` tablet only; no hub change, no restart; the run pre-registered (`ce8fdb41…`, 17:31:57Z).

**2026-11-21:** G6-JOIN1's run scored **NOT MET** (c4: one 283-ms output gap at 50 s; c7 / c12: the right stick not pushed fully up, left and into a corner). The change under test, the hold-to-join (c5), **met**: joined by the hold 2530 ms after the release (`../evidence/G6_JOIN1_HOLD_TO_JOIN_2026-11-20.md` §6). The user: "done, worked just as expected".

**2026-11-21 — the user reverses G6-HM1b's choice** ("right stick above the face buttons"), after play: "After playing a while on the tablet I think ergonomically it would be better to swap the right face and analogs everything else remains unchanged". The right side now matches the left (the D-pad above the left stick; the face buttons above the right stick), as on a DualShock 2.

**2026-11-21:** G6-SWAP1 part 1 done (`../evidence/G6_SWAP1_RIGHT_SIDE_SWAP_2026-11-21.md`): the face diamond around (900, 295), the right stick at (900, 805); every other control unchanged; the geometry check passes (End's nearest press area △ at 0.78 cm). Candidate `0a631e79…` tablet only; no hub change, no restart; the run pre-registered (`4f7bdadd…`, 00:59:37Z), with c14 `layout_version` `"ps2-swap1"`.
