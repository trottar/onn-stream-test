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
| D3 | **The PS1 layout first.** |
| D4 | Tablet landscape **keeps today's full-screen fill** (about 6.7 % stretched, inferred); no letterbox. |
| D1 | **Partly settled** by D2. Open: portrait as a Settings choice, or following the rotation. |

**Open points:** whether a later pad should take over P1; what the lower region shows when a real pad is P1; D1's rest.

## 6. The portrait stages (proposed, none started)

| Id | Aim |
|---|---|
| G6-HM1 | The design, hashed before any code |
| G6-HM2 | The bench logic and its JVM tests |
| G6-HM3 | Portrait video with an inert pad; the onn's confirmation sits before any APK replaces `ca53df0d…` |
| G6-HM4 | The PS1 digital controls live |
| G6-HM5 | Sticks, L3 / R3, a latency video |
| G6-HM6 | Live rotation, customization, the battery / heat comparison (feeds G6-S5) |

Each stage starts only on the user's word, under the conflict rules in §3.
