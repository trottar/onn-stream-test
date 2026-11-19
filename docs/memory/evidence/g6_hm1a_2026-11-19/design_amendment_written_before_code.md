# G6-HM1a — design amendment: the PS2 layout on every system (written and hashed before any code, 2026-11-19)

This amends the hashed design `../g6_hm1_2026-11-19/design_written_before_code.md` (sha256 `c38dbd82…`) and the
answers file `../g6_hm1_2026-11-19/user_answers_2026-11-19.md`. **Neither is edited.** Where this file and they
differ, this file is newer. Task: `../../handoffs/G6-HM3S_SCORE_AND_HM1A_TASK.md`. G6-HM3's score and the user's
remarks: `../G6_HM3_PORTRAIT_SCREEN_2026-11-19.md` §4. **No code exists for this amendment.** It waits for the user's
approval, and G6-HM4 starts only on the user's word.

**Labels.**
- **Verified:** read in the code or the logs at the cited place.
- **Proposed:** this amendment.
- **Assumption:** not checked; the stage named checks it.
- **Question:** the user's to settle (§8); none is picked here.

## 1. The user's decision (B1)

> "I decided we should be using PS2 setup for everything because this literally won't work for PS2 and GameCube."
> (the user, 2026-11-19)

**The PS2 (DualShock 2) layout on every system.** It replaces D3 ("the PS1 layout first") and Q6 (b) ("the PS1
layout until a system's own exists"). The controls:
- the D-pad, 8-way;
- the four face buttons;
- L1, L2, R1, R2;
- **two analog sticks, absolute by default, with L3 and R3**;
- Select and Start;
- End (Q5 (c), unchanged).

**Why one layout serves every system (verified on the client side).** The touch pad writes the same PHI1 fields a
real pad's events write: XUSB buttons, four stick shorts, two trigger bytes (`NativeControllerSender.writePlayerState`,
G6-HM2). The PS2 layout sets every field a DualShock sets. So each system gets what a DualShock on that player would
send. The hub's per-system mapping is not re-read here (an **assumption** that it treats the touch pad's packets as any
pad's: the packet is identical).

**The sticks move from G6-HM5 into G6-HM4.** The stage table, restated:

| Stage | Aim | State |
|---|---|---|
| G6-HM1 | the design, hashed before code | done (`c38dbd82…`), answers recorded |
| **G6-HM1a** | this amendment: the PS2 layout everywhere, the shoulders lower, the main app upright, the weak-signal notice | **written, awaiting approval** |
| G6-HM2 | bench logic + JVM tests | met (346 / 346). Extended at G6-HM4 for the PS2 controls |
| G6-HM3 | portrait video with an inert pad | **NOT MET** by its rule (c4's gap 936 ms, inside a link stall); every other cell met |
| **G6-HM4** | **the PS2 layout live, sticks and L3 / R3 included**; D2's 5-s rule, the takeover and End live; the new shoulder positions; the user's picks for §4 and §5 | proposed (§6) |
| G6-HM5 | a latency video (touch → picture) | proposed (the sticks have left this stage) |
| G6-HM6 | live rotation, customization (size, spacing, position), the battery / heat comparison | proposed, unchanged |

## 2. The ergonomic basis (B2)

These sources are cited as the task gives them; this docs-only session fetched nothing.
- **Two thumbs, radial comfort, absolute stick, 8-way D-pad.** Touch allows about two simultaneous inputs, one per
  thumb. The comfortable regions are roughly radial from where the device is gripped, and the most-used controls go
  there. The upper and lower zones need a conscious thumb move, more so on tablets. Use an absolute stick for character
  movement and an 8-way D-pad for diagonals. Source: Microsoft, the touch-layout designer's guide
  (https://learn.microsoft.com/en-us/gaming/gdk/docs/features/common/game-streaming/building-touch-layouts/game-streaming-tak-designers-guide).
- **Distance costs effort on large tablets.** Targets farther from the palm need more thumb extension and more forearm
  muscle activity in a two-handed grip. Source: Applied Ergonomics study (https://pmc.ncbi.nlm.nih.gov/articles/PMC7641204).
- **Sizes.** A target needs at least about 1 cm × 1 cm, and a thumb's contact is about 2.5 cm wide. Source: NN/g
  (https://www.nngroup.com/articles/touch-target-size/).
- **Adjustable.** Players should be able to adjust the size, spacing and position of every touch target. Source: Xbox
  accessibility guideline 107
  (https://devdocs.xbox.com/build/game-principles/accessibility/xag-deep-dives/xag-107-input.md). That is G6-HM6's
  customization, unchanged.

## 3. The layout (B3, proposed for approval)

**The region:** 1200 × 1325 px under the 1200 × 675 video box (verified, G6-HM3's report: `pad_region` `1200x1325`,
`density` 1.5).
- **Sizes** are given at Android's 1.5 density (240 dpi, 94.5 px/cm), which is the stricter for minimum sizes, and at
  the panel's own ~224 ppi (2000 × 1200 at 10.4", 88.2 px/cm). The region is 12.7 × 14.0 cm at 240 dpi and
  13.6 × 15.0 cm at 224 ppi.
- **The grip (assumption, measured at G6-HM4):** each hand holds a lower side. The thumb's base is at the side edge
  about 3 cm above the bottom, at y 1042 in the region.
- **The checks:** every number below is checked by `layout_check.py`. The output is in `layout_check_output.txt`:
  ALL CHECKS OK, no two of 120 press-area pairs overlapping, nothing in the bottom tenth, every target ≥ 1 cm, the
  D-pad and both sticks ≥ 2.5 cm.

| Control | Centre (px) | Drawn size (cm, 240 / 224) | Press area | From the thumb base (cm, 224) |
|---|---|---|---|---|
| Left stick | (300, 1000) | Ø 2.79 / 2.99 | r 158 px (×1.2) | 3.4 |
| D-pad | (300, 660) | Ø 2.65 / 2.83 | r 156 px (×1.25) | 5.5 |
| L3 | (540, 1040) | Ø 1.02 / 1.09 | r 58 px (×1.2) | 6.1 |
| L1 | (62, 700) on the left edge | 1.20 × 2.20 / 1.28 × 2.36 | 124 × 229 px (×1.1) | 3.9 |
| L2 | (62, 465), directly above L1 | 1.20 × 2.20 / 1.28 × 2.36 | 124 × 229 px | 6.6 |
| △ ○ ✕ □ | cluster centre (900, 1000), ±90 px | each Ø 1.10 / 1.18; the cluster 3.01 / 3.22 across | r 62 px each (×1.2) | 2.4–4.4 |
| Right stick | (900, 660) | Ø 2.79 / 2.99 | r 158 px | 5.5 |
| R3 | (690, 790) | Ø 1.02 / 1.09 | r 58 px | 6.4 |
| R1 | (1138, 700) on the right edge | 1.20 × 2.20 / 1.28 × 2.36 | 124 × 229 px | 3.9 |
| R2 | (1138, 465), directly above R1 | as R1 | 124 × 229 px | 6.6 |
| Select | (400, 70) | 1.60 × 1.01 / 1.71 × 1.08 | 181 × 114 px (×1.2) | 11.9 |
| Start | (600, 70) | as Select | 181 × 114 px | 12.9 |
| End | (960, 70), kept apart from Start | as Select | 181 × 114 px | 11.3 |

**The sketch.** One character is 25 × 50 px, so circles look squashed. `L`/`R` = sticks, `+` = D-pad, `3` = L3 / R3,
`1`/`2` = L1 R1 / L2 R2, `^ o x #` = △ ○ ✕ □, `s S E` = Select Start End. The dots are the bottom tenth, kept clear for
the home gesture.

```
+------------------------------------------------+   (the video box is above)
|             ssssss  SSSSSS        EEEEEE       |
|             ssssss  SSSSSS        EEEEEE       |
|                                                |
|                                                |
|                                                |
|                                                |
|                                                |
|22222                                      22222|
|22222                                      22222|
|22222                                      22222|
|22222                                      22222|
|        ++++++++                RRRRRRRR        |
|11111  ++++++++++              RRRRRRRRRR  11111|
|11111  ++++++++++              RRRRRRRRRR  11111|
|11111   ++++++++               RRRRRRRRRR  11111|
|11111     ++++            333    RRRRRR    11111|
|                          333                   |
|          LLLL                    ^^^^          |
|        LLLLLLLL                  ^^^^          |
|       LLLLLLLLLL              ###    ooo       |
|       LLLLLLLLLL   333        ###    ooo       |
|        LLLLLLLL    333           xxxx          |
|          LLLL                    xxxx          |
|                                                |
|................................................|
|................................................|
+------------------------------------------------+
```

**How it follows the task's sketch, and where it departs (disclosed for approval):**
- **Left arc as asked.** The stick is at the thumb's rest spot, low, 3.4 cm from the thumb base. The D-pad is above
  it, inside the arc. L3 is on the stick's inner side.
- **Right arc: the right stick sits *above* the face buttons, not below-inward.** Below the face cluster there is no
  room: the bottom tenth is kept for the home gesture (design §7), and a full-size stick under the cluster would reach
  into it. The stick therefore mirrors the D-pad. The face buttons keep the right thumb's rest spot (2.4–4.4 cm), and
  R3 is on the stick's lower inner side. The alternative is Q-L1 (§8).
- **The shoulders, the user's "lower".** They are not a top strip any more (G6-HM3 had them at 3–13 % of the region's
  height). They are tall edge buttons for a rocking thumb. L1 / R1 sit at the D-pad's and the right stick's height,
  centres at 53 % of the region's height. L2 / R2 sit directly above them (35 %).
  - Placing L1 just above the D-pad, as the task's sketch has it, would push L2 to about 9 cm from the thumb base,
    out of reach without moving the grip.
  - Even here, L2 / R2 are 6.6 cm from the thumb base: a stretch, per the Applied Ergonomics finding. G6-HM4 reads
    whether they are reachable (§6). Q-L2 (§8) holds the alternatives.
- **Select, Start and End** form the top row: infrequent, away from both arcs, and 11–13 cm from the thumb bases (a
  conscious move, per Microsoft's zones). End is 3.8 cm from Start.

**The sticks (proposed):**
- Absolute: the base is fixed, and the finger's offset from the centre over the drawn radius gives the deflection,
  clamped at 1.
- Dead zone 0.1 r.
- A finger keeps its stick until it lifts, even outside the base.
- The sign is G6-HM2's `stickY`: up is positive, as the sender stores `-AXIS_Y` (verified, `NativeControllerSender`
  `toStick(-ly)`). X is right-positive.
- L3 / R3 are separate buttons, because a touch cannot click a stick.

**`TouchPadState` at G6-HM4 (proposed):**
- the controls `LSTICK`, `RSTICK`, `L3`, `R3` added;
- the layout replaced by this table's fractions;
- the output's `lx` / `ly` / `rx` / `ry` from the sticks;
- XUSB `LEFT_THUMB` 0x0040 / `RIGHT_THUMB` 0x0080 for L3 / R3, pinned by a test (verified values, sender lines 45-46).

New JVM tests:
- each stick's four directions and sign;
- the clamp and the dead zone;
- a stick and a button held together;
- a stick finger leaving its base;
- this table's non-overlap, as `layout_check.py` checks it.

## 4. The main app cut off upright (B4)

**Verified: the catalog grid is 3 columns of fixed-width cards.**
- `res/layout/activity_main.xml` declares `source_grid` as a `GridLayout` with `columnCount="3"` inside a vertical
  `ScrollView` with 12 dp side padding. `MainActivity.kt:1754-1759` sets 3 columns, or 1 on the TV guide list.
- Each card is `dp(300)` wide (`MainActivity.kt:2382`) with a 6 dp margin on each side.
- So a row needs 3 × 312 + 24 = **960 dp**: exactly the onn's width at 1920 px and density 2.0. The onn's density is
  an **assumption** here; the grid fits there today.
- The tablet upright is 1200 px / 1.5 = **800 dp** wide, so the third column (160 dp) falls off the right edge. The
  `ScrollView` scrolls only vertically, so it cannot be reached.
- Landscape, the tablet is 1333 dp wide and the grid fits.

**Verified: the other rows fit in 800 dp.**
- The top bar is 104 + 112 + 122 + 104 dp of buttons, plus a weighted breadcrumb and 32 dp of padding (≈ 474 dp).
- The now-playing bar is 280 + 184 + 125 dp, plus a weighted title (≈ 589 dp).

**Not explained by the code read: Settings.**
- `showCompanionSettings()` (`MainActivity.kt:1053-1376`) builds a vertical container with 24 dp padding and no fixed
  widths.
- It has no `ScrollView`, which matters for height, not width.
- What is cut off there should be looked at in G6-HM4's run (§6).

**Also verified:** `MainActivity`'s manifest entry has no `screenOrientation` and no `configChanges`. It turns with
the tablet, and Android rebuilds it on each turn.

**Options (Q-B4; not picked), with what each touches on the onn:**
- **(a) The main app follows the handheld choice.** With "Handheld" on and a touchscreen, the grid's column count
  comes from the measured width (2 upright: 2 × 312 + 24 = 648 ≤ 800 dp). Card widths stay at 300 dp.
  - **Onn:** nothing; the new code runs only behind `useHandheldGameScreen()`, which is false on the onn.
  - The paused screen and B73's bar also live in `MainActivity` and would follow.
- **(b) The main app is locked to landscape on the tablet; only the game turns upright.** At runtime,
  `requestedOrientation = LANDSCAPE` when "Handheld" is on and the device has a touchscreen.
  - **Onn:** nothing; the manifest entry is unchanged, and the onn is always landscape anyway.
  - **Cost:** the tablet turns sideways at each End / pause and back upright at each game.
- **(c) The column count from the measured width for every device** (as (a), but not behind the choice).
  - **Onn:** its code path changes; the result there is still 3 columns if its width is 960 dp (assumption above).
  - Not "nothing" on the onn, so it needs the onn's confirmation before any APK replaces `ca53df0d…`.
- **(d) Narrower cards upright, 3 columns kept.** The card width is (width − 24 dp) / 3 − 12 dp, about 247 dp. This
  runs behind the handheld choice, as (a).
  - **Onn:** nothing.
  - The game cards (118 dp tall with art) keep their height, so the art is scaled down.

## 5. The weak-signal notice (B5)

**Verified: the rule** (`streaming/LinkNotice.kt:13`, `:66-69`):
- the notice shows when RSSI ≤ −72 dBm, or tx ≤ 54 Mb/s, is held 10 s (or on 2.4 GHz at once);
- it clears only after **30 s** of good readings;
- it shows at most once a session unless the band changes.

**Verified: the readings.** These are the heartbeat link rows kept by `privyhub-diag` (`~/privyhub_diag/*/raw/`,
deduplicated by receipt time), and each session's `link_notice_shown` row. The decoder reports carry only
`link_notice_shown` / `link_notice_last_reasons`.

| Client, session | Rows | Band | RSSI median [min..max] | Rows ≤ −72 | tx median [min..max] Mb/s | Rows tx ≤ 54 | Notice shown |
|---|---|---|---|---|---|---|---|
| tablet, s10 (04:27Z, G6-S1) | 14 | 5180 | −72 [−73..−72] | 14 | 65 [58..97] | 0 | yes: −73 dBm, 65 Mb/s |
| tablet, s11 (06:30Z, PS2, the CONFIRMED APK) | 92 | 5180 | −73 [−80..−71] | 91 | 40 [6..65] | 77 | yes: −80 dBm, 7 Mb/s |
| tablet, s12 (15:44Z, the G6-HM3 run) | 99 | 5180 | −71 [−74..−50] | 43 | 65 [29..325] | 3 | yes: −72 dBm, 65 Mb/s at 15:45:45Z |
| the onn, 2026-11-18 | 2055 | 5180 | −69 [−70..−68] | 0 | 195 [97..390] | 0 | never |
| the onn, 2026-11-12 … 11-18 | 13847 | 5180 / 5500 | −60 [−70..−42] | 0 | 292 [97..866] | 0 | never |
| the onn, LINK-R1 (2026-10-23) | — | 5180 | −68 / −69 | — | — | — | — |

**What the evidence supports:**
- **The notice is reading the tablet correctly by its rule.** In s10 and s11 nearly every row is at or under
  −72 dBm, and s11's tx was mostly ≤ 54 Mb/s. The onn on the same band reads 3–4 dB better and never reaches −72.
- **The tablet's link was really stalling, not only reading low.** s12 had 5 dark spans and 90 stall signals, and
  s11 had 6 stall episodes, 3 with lost packets (334, 16 and 196; 06:31–06:33Z).
- **"Persistent even next to the router" fits the clear rule.**
  - s12's last 20 s read −50…−55 dBm at 325 Mb/s, which looks like the tablet moved close.
  - The notice needs 30 s of good readings to clear, and the session ended first.
  - Which router the tablet uses is not known from the logs (G6-S1: the home 5 GHz network, not the travel router's).
- **Placement or grip matters within one session:** s12 swung from −74 to −50 dBm. Whether hands over the tablet's
  antenna lower the reading upright is an **assumption**.

**Options (Q-B5; not picked):**
- **(a) A tablet-specific threshold** (e.g. −75 dBm).
  - **Evidence against:** at −71…−73 the tablet's link stalled. A lower threshold would hide a link that is actually
    failing.
  - **Onn:** nothing, if it is set only in the handheld activity.
- **(b) In handheld mode, the notice as a line in the pad region's status area instead of over the picture.**
  - **Evidence for:** the notice is true, so it keeps the information without covering the game.
  - **Onn:** nothing (the handheld activity only).
- **(c) A grip and placement test first:** the tablet flat beside the router versus held upright, a minute each, read
  from the link rows.
  - **Evidence for:** the −74…−50 swing in one session. It can double as the re-run of G6-HM3's c4 (Q-HM3).
  - **Onn:** nothing.
- **(d) A faster clear in handheld mode** (e.g. 10 s good instead of 30 s).
  - **Evidence for:** s12's last 20 s were good, and the notice stayed.
  - **Onn:** nothing only if the clear time is passed in by the handheld activity; `LinkNotice` itself is shared.

## 6. G6-HM4: scope and cells (B6; the cells are pre-registered at G6-HM4's start, not here)

**Scope:**
- the PS2 layout live (§3), sticks and L3 / R3 included;
- D2's 5-s rule, the takeover (Q2 (d)) and End;
- `TOUCH_LIVE` true;
- the shoulder positions;
- the user's picks for Q-B4 and Q-B5, and for Q-L1 / Q-L2.

**New keys in the `handheld` block (proposed):**
- `layout: "ps2"`;
- `p1_join_after_release_ms`;
- `takeovers`;
- `controls_pressed`: the set of controls pressed at least once;
- `stick_max_deflection` per stick.

**Cells (proposed):**

| Cell | What |
|---|---|
| G6-HM4.c1–c3 | as G6-HM3's c1–c3 |
| G6-HM4.c4 | as Q-HM3 decides |
| G6-HM4.c5 the join | `touch_slot` 0, `p1_join_after_release_ms` in 5000–5300 |
| G6-HM4.c6 every control | `controls_pressed` holds all 16 controls after a scripted run of presses |
| G6-HM4.c7 sticks | each stick's deflection reaches ≥ 0.9 in each direction |
| G6-HM4.c8 End | as G6-HM3's c7 |
| G6-HM4.c9 the takeover | `takeovers` 1 and `touch_slot` −1 after a real pad's 2-s hold (needs a pad on the tablet: Q-PAD) |

**The user's remarks, not cells:** whether the shoulders and L2 / R2 are reachable without moving the grip; the
main app upright (Q-B4); the notice (Q-B5).

## 7. Unchanged from the design and the answers

Everything not named here is unchanged:
- D1 (the Settings choice), D2, D4;
- Q1 (c), Q2 (d), Q3 (b) / (i), Q4 (b), Q5 (c);
- the hooks;
- the pointer-guard exemption;
- release safety;
- the onn's paths and its APK rule (CL-B7 §6).

## 8. Questions for the user (options; none picked)

- **Q-HM3. G6-HM3's missed c4** (936 ms, inside a link stall):
  - (a) re-run G6-HM3 once as pre-registered, with the tablet placed for a good link; it can be one of Q-B5 (c)'s
    minutes;
  - (b) leave G6-HM3 NOT MET on record and carry c4's bound unchanged into G6-HM4;
  - (c) leave it NOT MET, and pre-register G6-HM4's c4 as the largest gap outside the stall episodes (a new cell,
    stated before that run; G6-HM3 is not re-scored).
- **Q-B4. The main app upright:** (a), (b), (c) or (d) of §4.
- **Q-B5. The weak-signal notice:** (a), (b), (c) or (d) of §5. They can be combined (e.g. (c) first, then (b)).
- **Q-L1. The right stick:**
  - (a) above the face buttons, as checked in §3;
  - (b) below-inward, as on a DualShock, with the face cluster raised off the thumb's rest spot so the stick clears the
    bottom tenth.
- **Q-L2. L2 / R2 at 6.6 cm from the thumb base:**
  - (a) as in §3, judged at G6-HM4;
  - (b) L1 and L2 side by side on the edge at the same height, L2 on the outside, so both are within ~4–5 cm;
  - (c) L2 / R2 as the outer half of a double-height L1 / R1 button (one rock reaches either).
- **Q-PAD. The takeover's live test needs a real pad paired to the tablet.** The plan's conflict rules say no pad pairs
  to the tablet before G6-S4.
  - (a) bring G6-S4 forward for one pad that is not one of the onn's pads;
  - (b) leave the takeover to its JVM tests at G6-HM4, and test it live at G6-S4.
