---
memory_schema: 1
as_of: 2026-11-17
status: DONE (session B, queue AS) — both readers on the unlocked select screens, on H7-C2's labelled pictures (read only). **T88: H7-V3's spec as it stands already reads the unlocked start / end_P1 / end_P2** (C2 — start 34 / 38, the 4 others the pictures under RetroArch's notices; end_P1 37 / 37; end_P2 37 / 37; fights 17 / 17; 0 wrong, 0 fights as the screen) but with less headroom (the unlocked screens 0.041 from its reference against a threshold of 0.090; the locked ones 0.002-0.003). **Learnt from all three sources** every class is separable and every source reads with 0 wrong and 0 fights as the screen (the unlocked screens 0.0036). The fold without the live run does not separate the start and lets one live fight read as the screen (class unknown, never an end): C2's four notice-covered start pictures; with them set to ignore in memory, every fold holds. **T89: B122's spec already reads the unlocked start 38 / 38, the locked start 17 / 17, the results 38 / 38**; learnt from C1 + C2 the same, and C1's five folds again 0 places wrong. One spec per title (no spec per setup). The darkest gamma + offset pair still drops the 1920 x 1080 unlocked screens (to other / unknown, never a wrong class). Replay: each end load ended 2 s after its end screen with the right side / places; C1's replay unchanged line for line; LIVE's end_P2 1 s earlier (an ignore-labelled fade now read end_P2). Tool unchanged; no patch. Nothing adopted; nothing committed
---

# B126 — both readers taught the unlocked select screens

Queue: `handoffs/QUEUE_2026-11-17AS.md` §B126. T88 = H7's 2-player PS1 title (the duel); T89 = the users' N64 four-
player title (the round's end). The directory is `b126_2026-11-17/`: the design and its two amendments (each hashed
before the runs it covers), `scripts/b126_eval.py` (every number below), the results (`t88_results.jsonl`,
`t88tone_results.jsonl`, `t89_results.jsonl`, `t89tone_results.jsonl`, `replay_results.jsonl`, `a1_results.jsonl`,
`a2_results.jsonl`, each with its empty `.err`), `pre_design_score_rules_spec_on_c2.json`, the checks, `manifest.sha256`.
No title, character name, cheat name, serial, game id or path; no picture in git. **Nothing of A's or the users'
touched:** the pictures and Cowork's labels read only, nothing written beside them; the rules folder read only (the
T88 spec read in place to score it; its sha256 `06058b7b…` / `922415bc…` = H7-V3's); every spec here learnt in memory.
**`tools/h7_endscreen.py` unchanged — no patch for B126.**

**Disclosed, before the design (03:10:24Z):** the queue's first question run once with the tool's own `score` on the
rules folder's spec, and one look at two C2 pictures (4 and 8) to see why 4-7 read `unknown` — RetroArch's notices
(the cheat applied, the pads configured) over the screen; nothing copied. Amendment 1 (03:16:21Z) and amendment 2
(03:31:20Z) were written after runs on the real pictures (disclosed in each); they add diagnostics only.

Sources: **V1** = H7-V1's screenshots (640 × 525; locked grid); **LIVE** = H7-V2's window run (1920 × 1080; locked);
**C2** = H7-C2's T88 run (1920 × 1080; every select screen unlocked; `other` = the kept mid-fight state) — Cowork's
labels: start 38, end_P1 37, end_P2 37, other 17; **C1** = H7-C1's T89 run (960 × 720; locked; five matches);
**T89C2** = H7-C2's T89 run (start 4-41 unlocked = 38, 86-102 locked = 17; end_r1234 38; no `other`).

## T88 (spec version 2)

### 1 — H7-V3's spec as it stands, on the unlocked screens: **it reads them**

Learnt in memory from V1 + LIVE: **equal to the rules folder's spec in every number and every array.**

| scored on | start | end_P1 | end_P2 | other | wrong class | fights as the screen |
| --- | --- | --- | --- | --- | --- | --- |
| **C2 (unlocked)** | **34 / 38** (4 `unknown`: pictures 4-7, under the notices) | **37 / 37** | **37 / 37** | **17 / 17** | **0** | **0** |
| V1 | 788 / 788 | 72 / 72 | 74 / 74 | 218 / 218 | 0 | 0 |
| LIVE | 70 / 73 | 113 / 117 | 98 / 103 | 214 / 214 | 0 (12 range-edge `unknown`, as H7-V3) | 0 |

The C2 screens' screen distance: median **0.0412**, worst 0.0863 against the threshold **0.0902** (LIVE's median
0.0033; V1's 0.0018) — read, with less headroom; the nearest C2 fight 0.2307; least margins start 0.174, end_P1
0.198, end_P2 0.195 (needed 0.0929). **The plain answer: yes — H7-V3's spec reads the unlocked start, end_P1 and
end_P2; the unlocked grid lies mostly outside its outcome mask (the tallies) and inside what its screen mask
tolerates.**

### 2 — learnt from all three (V1 + LIVE + C2, Cowork's labels as they stand)

**Screen threshold 0.0820** (worst own 0.0054, best foreign 0.1587, gap 0.1533); **classes start 0.0958 (gap 0.1671),
end_P1 0.1044 (0.1916), end_P2 0.0983 (0.1757)** — all separable; **margin needed 0.0921**; **screen mask 12,244 px
(63.8 %), outcome mask 104 px** (x 63-108, y 84-92 of 160 × 120 — the tallies); `unlike_label` start 7, end_P1 4,
end_P2 5 (range-edge and notice pictures).

| scored on | start | end_P1 | end_P2 | other | wrong | fights as the screen | screens' distance (median) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V1 | 788 / 788 | 72 / 72 | 74 / 74 | 218 / 218 | 0 | 0 | 0.0020 |
| LIVE | 70 / 73 | 113 / 117 | 98 / 103 | 214 / 214 | 0 | 0 (nearest 0.1587) | 0.0027 |
| C2 | 34 / 38 (3 `other` + 1 `unknown`: 4-7) | 37 / 37 | 37 / 37 | 17 / 17 | 0 | 0 (nearest 0.2236) | **0.0036** |

LIVE's 12 range-edge pictures now read `other` (were `unknown`): the same right counts.

### 3 — folds; `other` read as the screen

| learnt from | held out | start | end_P1 | end_P2 | other | wrong | **fights as the screen** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V1 + LIVE (= 1.) | C2 | 34 / 38 | 37 / 37 | 37 / 37 | 17 / 17 | 0 | **0** |
| **V1 + C2** | **LIVE** | **0 / 73** (start not separable: gap −0.009) | 113 / 117 | 98 / 103 | 213 / 214 | 0 | **1** (class `unknown`) |
| LIVE + C2 | V1 | 788 / 788 | 72 / 72 | 74 / 74 | 218 / 218 | 0 | 0 |
| *A1:* V1 + C2′ (C2's 4-7 ignored) | LIVE | 70 / 73 | 113 / 117 | 98 / 103 | 214 / 214 | 0 | **0** |
| *A1:* LIVE + C2′ | V1 | 788 / 788 | 72 / 72 | 74 / 74 | 218 / 218 | 0 | 0 |
| *A1:* V1 + LIVE + C2′ | C2′ / C2 | 34 / 34 / 34 / 38 (4-7 `other`) | 37 / 37 | 37 / 37 | 17 / 17 | 0 | 0 |

**The fold without the live run is not met as labelled:** C2's start pictures 4-7 (RetroArch's notices over the
screen, labelled `start`; the labels mark only 1-3 `ignore`) fall nearest `start` in that arrangement and widen the
learnt screen threshold to 0.1547 (their screen distances 0.122-0.132) and the start's own worst to 0.2103 — the start
is then not separable (73 live start pictures `unknown`) and **one live fight reads as the screen** (as `unknown`,
never an end class: it can never end a mini game). **With those four pictures set to `ignore` (amendment 1, in memory;
Cowork's file unchanged) every fold holds** — the live run read as B104's arrangement 1a, 0 fights as the screen.

### 4 — B104's tone grid (27 variants: offsets ±10/20/30, gains 0.8-1.2, gammas 0.8-1.25, the 12 extreme pairs)

- **H7-V3's spec → all 129 C2 pictures (held out):** **0 misread, 0 fights as the screen** in every variant; **gain 0.8
  with offset −30 and gamma 1.25 with offset −30 each turn 112 of 129 to `other` / `unknown`** (the unlocked screens
  start at 0.041 and cross the threshold); the nine other variants that change anything: 1-4 readings each (offsets
  −10 / −20 / −30, gain 1.2 with −30, gamma 0.8 with −30: 4; the gain × gamma pairs: 2; gamma 0.8, gamma 0.8 with +30:
  1). 250 changed readings over 3,354.
- **V1 + LIVE + C2 first halves → C2's second halves (66 held out):** **0 readings changed in every variant** — but in
  this arrangement the start class cannot be learnt (amendment 2: LIVE's range-edge pictures 285-287, labelled `start`
  and off the screen, fall nearest `start` once C2 is in), so the 19 held-out C2 start pictures read `unknown` in every
  variant; ends 19 / 19 + 19 / 19, fights 9 / 9. With C2's 4-7 also ignored: the same (17 start `unknown`).
- **Amendment 2 — the three-source spec on all of C2 (not held out, disclosed):** **gamma 1.25 with offset −30 still
  turns 109 of 129 to `other` / `unknown`**; gain 0.8 with −30 now 1; every other variant ≤ 1; 0 misread, 0 fights.
- **The limit, stated:** the 1920 × 1080 unlocked screens do not survive the darkest gamma + offset pair (B122 saw the
  same pair change 1 of T89's 19,604 readings); never a wrong class, never a fight as the screen.

### 5 — one spec per title, not one per setup

**One spec reads the locked and the unlocked screens alike** (§1, §2): no spec per setup is needed and B127 builds
none. **The spec for H7-V5:** learnt from all three sources (V1 + LIVE + C2) — the unlocked screens then sit at
0.0036 instead of 0.041 (headroom under tone changes), and its replay ends the unlocked end_P2 in 2 s where H7-V3's
takes 9 s (§Replay). If a setup ever needed its own spec, the hub would choose `<game id>.<profile_id prefix>.endscreen.json`
when the session's `cheat_session.profile_id` is set and that file exists, else the title's spec (not built).

## T89 (spec version 3)

- **6 — C2 held out (B122's all-five spec, C1 alone, learnt in memory — every number = B122's: start 0.0912, end 0.1017,
  row spacing 40, offsets (57, 129) (57, 169) (57, 209) (57, 249), places 0.2273 / 0.2211 / 0.1807 / 0.1901, margin
  0.0916):** **the unlocked start 38 / 38, the locked start 17 / 17, the results 38 / 38 (every place right)**, 0
  wrong. **It already reads the unlocked screen.**
- **7 — learnt from C1 + T89C2:** start threshold **0.0932** (worst own 0.0262, gap 0.1341; mask 8,826 px), end
  **0.1011** (gap 0.1768; mask 5,785 px); the row as B122's (spacing 40, the same four offsets, cell 12 × 8, glyph
  163 px); places **0.2212 / 0.2218 / 0.1744 / 0.1915**, margin needed **0.0796**; usable. **C1: start 369 / 369,
  other 246 / 246, results 139 / 139 (every row, every place); T89C2: the unlocked start 38 / 38, the locked start
  17 / 17, the results 38 / 38; 0 fights as the screen** (C1's 246).
- **8 — C1's five folds again, all of T89C2 in training:** M1 (1 2 3 4) 34 / 34, M2 (4 1 2 3) 5 / 5, M3 (3 4 1 2)
  39 / 39, M4 (3 4 2 1) 32 / 32, M5 (1 3 2 4) 29 / 29 — **0 places wrong, 0 unread**; the held-out starts 151 / 64 /
  112 / 26 / 16 and fights 110 / 33 / 34 / 39 / 30 all right; **0 fights as the screen.**
- **9 — the tone grid on T89C2 held out (C1 alone; 93 pictures × 26 variants): 0 readings changed.**

## Replay (K = 3; the tool's replay and per load — each load's stretch read from its load with `start_loaded()`, as a hub watch begun with the load)

| run, spec | load | the reads | `ended` |
| --- | --- | --- | --- |
| C2 (T88), three-source | the users' cheat slot 1 | start 34, other 6, unknown 1 | — (first start read **6.97 s after the load**: the notices cover the first 6 s — inside B105's 8 s `recognised`) |
| | kept end P1 | end_P1 37, other 3 | **end_P1, 2.0 s** after its first end picture |
| | kept end P2 | end_P2 37, other 3 | **end_P2, 2.0 s** |
| | mid-fight | other 20 | none |
| C2 (T88), H7-V3's | kept end P1 / end P2 | end_P1 37 + other 1 + unknown 2 / end_P2 30 + unknown 10 | end_P1 2.0 s; **end_P2 9.0 s** |
| T89C2, C1 + T89C2 (and B122's: the same) | the users' cheat slot 1 | start 41 (from the first picture) | — |
| | kept results_1 | end 41 | **end, places [1, 2, 3, 4], 2.0 s after the load** (1 s before the first picture Cowork labelled, under the notice) |
| | kept begin (locked) | start 20 | — |

K = 2: each 1 s sooner. **The earlier runs:** C1 with the C1 + T89C2 spec — **unchanged line for line** (the five
ends, places and times as B122's; 0 reads differ). LIVE with the three-source spec — **the same two ends and sides,
not identical:** end_P2 said at 419.02 s (was 420.03 s) because the fade picture at 417.02 s (labelled `ignore`) now
reads end_P2 (was `unknown`); 12 range-edge reads `other` (were `unknown`); end_P1 at 153.03 s as before.

## What this means for A

- Both titles' readers read everything unlocked: T88 by H7-V3's spec already (the three-source spec better), T89 by
  B122's (the C1 + T89C2 spec the same); **one spec per title.**
- **Cowork's C2 T88 labels would be cleaner with pictures 4-7 as `ignore`** (RetroArch's notices still over the screen —
  the labels' own definition of `ignore`): every fold then holds. The three-source spec as labelled is the one H7-V5
  learns (its numbers above; deterministic).
