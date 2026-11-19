---
memory_schema: 1
as_of: 2026-11-19
status: TASK — session G6, docs only. Scores G6-HM3 part 2 as pre-registered, records the user's remarks, and writes G6-HM1a (the design amendment for the PS2 layout everywhere), hashed before any code. Stops for the user's approval. Nothing adopted; nothing committed.
---

# G6-HM3 score + G6-HM1a — the PS2 layout everywhere

**Docs only.** You read code and logs and never change them. Nothing under `PrivyHub/`, `companion/` or `tools/` is
edited: no build, no APK, no adb, no stream, no service restart, nothing fetched. Touch no other session's files.
Questions the user has not settled come back to them as options; do not pick.

## Part A — score the tablet run (G6-HM3 part 2)

The run was a PS2 game, about 199 s: decoder report `logs/games/decoder_sessions/native_decoder_20261119_154811_583.json`,
recovery log 15:44–15:48Z.

1. Check that the pre-registration's sha256 is still `bcbeff14…`.
2. Score c1–c7 exactly as written, each with its value. Cowork's preview, which you must confirm from the raw files:
   - c1–c3 and c5–c6 met;
   - c4's `max_output_gap_ms` 936 is NOT MET (bound 250);
   - c7: End met, and `back_swallowed` 0, so Back was not tried.
3. Context, not cells:
   - `video.lost_packets` 1738;
   - about 90 stall signals;
   - the `link_notice_shown` `rssi_weak` row (5180 MHz, −72 dBm, 65 Mb/s).

   Say whether c4's gap falls inside a stall or loss burst in the recovery log.
4. **The user's remarks, verbatim (2026-11-19):**
   - "Handheld games, portrait PrivyHub menu is cutoff." When asked which screen: **the main app** (the catalog and
     Settings outside a game, held upright).
   - "R\L buttons need to be lower, there positioning isn't goood either."
   - "I decided we should be using PS2 setup for everything because this literally won't work for PS2 and GameCube."
   - "I also get a persistent wifi weak signal message even if I'm right next to the router."

   Write part A into `docs/memory/evidence/G6_HM3_PORTRAIT_SCREEN_2026-11-19.md` §4, with the verdict per the
   pre-registered rule.

## Part B — G6-HM1a, the design amendment (hashed before any code)

Write `docs/memory/evidence/g6_hm1a_2026-11-19/design_amendment_written_before_code.md` and its sha256. It amends the
hashed design (`c38dbd82…`) and the answers file without editing either.

### B1. The user's new decision

**The PS2 (DualShock 2) layout for every system.** It replaces D3 ("PS1 first") and Q6 (b) ("the PS1 layout until a
system's own exists"). The controls are:
- the D-pad (8-way);
- four face buttons;
- L1, L2, R1, R2;
- two analog sticks, absolute by default, with L3 and R3;
- Select and Start;
- End.

The sticks therefore move from G6-HM5 into G6-HM4. Restate the stage table.

### B2. The ergonomic basis (cite each in the amendment)

- Touch allows about two simultaneous inputs, one per thumb. Comfortable regions are roughly radial from where the
  device is gripped. The most-used controls go there. The upper and lower zones need a conscious thumb move,
  especially on tablets. Use an absolute stick for character movement and an 8-way D-pad for diagonals. Source:
  [Microsoft, touch-layout designer's guide](https://learn.microsoft.com/en-us/gaming/gdk/docs/features/common/game-streaming/building-touch-layouts/game-streaming-tak-designers-guide).
- On larger tablets, targets farther from the palm need more thumb extension and more forearm muscle activity in a
  two-handed grip. Source: [Applied Ergonomics study (PMC7641204)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7641204).
- Minimum target about 1 cm × 1 cm, and a thumb's contact area is about 2.5 cm wide. Source:
  [NN/g](https://www.nngroup.com/articles/touch-target-size/).
- Players should be able to adjust the size, spacing and position of all touch targets. Source:
  [Xbox accessibility guideline 107](https://devdocs.xbox.com/build/game-principles/accessibility/xag-deep-dives/xag-107-input.md).
  That is G6-HM6's customization, unchanged.

### B3. The layout (proposed, for approval)

Inside the 1200×1325 pad region, in fractions of the region. Compute millimetres from the display's real dpi (the
decoder report gives density 1.5) and state the sizes. Every target is at least 1 cm; the main controls are at least
2.5 cm.

- **The grip.** The two hands hold the lower sides, so each thumb's arc is anchored near a lower corner.
- **Left arc.** The left stick sits at the thumb's resting spot, low and near the edge. The D-pad sits above it,
  still inside the arc. L3 is a small button on the stick's inner side.
- **Right arc.** The face buttons sit at the resting spot, mirroring the left stick. The right stick sits below and
  inward. R3 is on its inner side.
- **Shoulders, the user's "lower".** They are not on a top strip. L1 and R1 sit on the outer side edges, at the top of
  each thumb's arc, just above the D-pad and the face buttons. L2 and R2 sit directly above L1 and R1, still reachable
  without moving the grip. Each is a tall edge button, so the thumb can rock onto it.
- **Select, Start and End.** These are infrequent, so they go in a centred row at the top of the pad region, away
  from both arcs. End is kept apart from Start.
- State each control's hit area (larger than its drawing), and that nothing overlaps.

Include a picture of the layout as a simple text or ASCII sketch in the amendment. It needs no code.

### B4. The main app cut off in portrait

Read `MainActivity.kt` and its layouts, read only, and say what is cut off when the tablet is upright and why: fixed
widths, landscape-only rows, or the catalog grid. Give the user options, with what each touches on the onn (nothing is
the requirement), for example:
- (a) the main app follows the handheld choice: portrait-friendly layouts on touchscreen devices only;
- (b) the main app is locked to landscape and only the game turns upright;
- (c) another option you find.

Do not pick.

### B5. The weak-signal notice

From every tablet session's link rows (the recovery log's `link_notice_*` rows and the decoder reports' link
fields), list the tablet's RSSI, tx rate and band. Compare them with the onn's typical readings (LINK-R1: −68/−69 dBm,
5180 MHz).

Give the user options, for example:
- (a) a tablet-specific threshold;
- (b) in handheld mode, the notice as a line in the status area instead of over the picture;
- (c) a grip and placement test first: the tablet flat beside the Opal vs held upright, a minute each, read from the
  link rows.

Say what the evidence supports. Do not pick.

### B6. The test and cell changes for G6-HM4

Revise G6-HM4's scope and its cells (still to be pre-registered at G6-HM4):
- the PS2 layout live, sticks included;
- the 5 s rule, the takeover and End live;
- the shoulder positions;
- whatever B4 and B5 lead to, once the user picks.

## Files and gates

- `docs/memory/handoffs/G6-HM3S_SCORE_AND_HM1A_TASK.md`: this task, copied in from
  `Claude outputs/G6_tablet/G6-HM3S_SCORE_AND_HM1A_TASK.md`.
- `G6_HM3_PORTRAIT_SCREEN_2026-11-19.md` §4: part A.
- `g6_hm1a_2026-11-19/design_amendment_written_before_code.md` and `design_amendment.sha256`.
- Update the plan file's stage table and dated line, `CURRENT.md`'s G6 line, and the plan's decisions (D3 replaced by
  the PS2-everywhere decision).
- `logs/g6_hm3s_git_status.txt`: this task's files only.

**Gates:** `tools/check_memory_health.py` passes; `git diff --check` is clean; the redaction check is clean; and
nothing of this task's is under `PrivyHub/`, `companion/` or `tools/`. No address, serial, token or pairing code;
device ids as 4 hex digits and "…"; no game title.

Your last reply begins "YOU, now: commit", then:
- the seven cells with their values and the verdict;
- the amendment's sha256;
- the layout in a few lines;
- B4's and B5's options, each with the evidence for it.
