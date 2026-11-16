---
memory_schema: 1
as_of: 2026-11-16
status: BUILT (session B, queue AN) — tools/h7_endscreen.py reads the end screen independent of tone (spec version 2: each picture's pixels ranked against its own screen-mask tone; the game's picture found inside a window by the tool; several sources learnt together; a version-1 spec refused with "learn it again"; `replay`). On the real pictures, read only: **0 fights read as the screen in every arrangement**; learnt from H7-V1's screenshots alone, **495 / 508 live pictures read right** (the 12 others are range-edge pictures read as "other" + the one `ignore`); learnt from the live run alone, H7-V1's 1,152 frames all right; learnt from everything (the spec A will use) every class separable and everything right but 12 range-edge pictures (`unknown`); **no reading changed under offsets ±30, gains 0.8-1.2, gammas 0.8-1.25 or any pair of their extremes**; replay: `ended` 2.0 s after the select screen returns (K = 3), 1.0 s (K = 2), both on the user's sides. Four design amendments, each hashed before the code or run it changed, two of them after runs on the real pictures (disclosed, both runs kept). No companion change. Nothing committed. No title, code name, character name, path or picture in this record
---

# B104 — the reader made independent of tone (`tools/h7_endscreen.py`) (2026-11-16)

**Why:** H7-V2 — the hub read all 516 live pictures as `other`; the select screen sat at 19.2-20.2 against 14.66
because B102 compares absolute grey levels and the live window is darker than the headless screenshots (Cowork: ~16
levels in the mid tones, ~6 in the bright — a gain and an offset or a curve, cause unsettled). **Baseline:** HEAD
`d61f9b56`. **Design** hashed 04:15:29Z, before code (`b104_2026-11-16/design.sha256`).

## The design and its four amendments (all in `b104_2026-11-16/`)

- **Disclosed first — a look before the design** (`pre_design_look/`, scripts only): the pictures reduced in memory,
  three tone removals compared under tone changes; ranks kept the widest gap under the worst pair (2.6 × vs 1.5 × for
  a standardised picture, 1.1 × for median / IQR). It also showed **the window's bars must not be found from dark
  content**: the game fills the window's height (1318 × 1080, the screenshots' 1.219 aspect) and its own dark border
  rows read 0 in the window but 22 in the screenshots.
- **Amendment 1** (04:16:39Z, before any code): ranks with a tolerance τ = 2 % of the picture's own contrast — picture
  noise in flat areas otherwise scatters the ranks.
- **Amendment 2** (04:19:14Z, after the first run of B102's unchanged tests on the new code, before any real picture):
  the alignment search ranks its candidates by the **mean** rank distance (the median of a mostly flat screen hardly
  moves when it shifts: B102's 6-px case failed).
- **Amendment 3** (04:29:53Z, **after the first run on the real pictures** — `run1_before_amendment3_a1/a2/a3.jsonl`,
  kept; checks in `amendment3_look/`): the measure held (learnt from H7-V1 alone 495 / 507 labelled live pictures right,
  0 fights as the screen) but **learning failed whenever live pictures were in the learning set** — learnt from
  everything nothing separable; in 2a **21 start pictures read as `end_P2`**. Three causes, none in the measure: (1)
  B102's absolute steadiness test dropped the tally itself (other characters shift the tally's ranks ~0.04, its stroke
  edges up to ~0.1 — between stretches; frame to frame the live tally moves ~0.001); (2) 3-5 range-edge pictures per
  class (the seconds of a launch or an END — the kind H7-V1's labels mark `ignore` for RetroArch's own notice) read
  nearer another class than their label, and B102 sets every threshold past the worst own frame; (3) a confound by
  construction in arrangement 2 (a pair of classes never seen in one source differ by the characters as much as the
  tally). **Changes:** the outcome mask only from class pairs that both have frames **in one source**, its steadiness
  judged against the separation (difference > 3 × the pixel's 10th-90th percentile within-class spread); **a labelled
  frame not nearest its own class's reference does not set its class's threshold** (counted as `unlike_label`; the
  foreign side stays strict); **a gap under 0.05 is "not separable"**. Disclosed: the hashed text says a prototype of
  "exactly these rules" gave its numbers; the prototype's last form had no minimum gap — that rule was added from its
  2a result (end_P2 pictures read as the start on a 0.009 gap).
- **Amendment 4** (04:38:51Z, **after a second real run, which I stopped** after the 4a tone grid —
  `run2_before_amendment4_stopped.jsonl`, 41 lines, kept): (1) offsets +20 / +30 turned the bars grey above the fixed
  16, so 111 held-out live screens read `unknown`; (2) gamma 1.25 with −30 let **one held-out fight read as the screen
  (`unknown`)** — that spec's screen threshold had been set past a range-edge picture. **Changes:** the bars relative
  to the picture's darkest pixel + 16; a frame unlike its label does not set the screen's threshold either.
- **Then the whole evaluation once more, from the start, on the tool's code** (run 3, 04:41:01-04:58:25Z,
  `real_eval_results.jsonl`, 88 lines; `real_eval.py`): the numbers below.

## The measure (stated; why; what it loses)

- **The game's area, one way, inside `reduce`** (learn, read, replay and the watcher all call it): whole edge columns /
  rows no brighter than the picture's darkest + 16 are a window's bars; per axis the smaller side; one axis only, ≥ 5 %
  of it, leaving at least half. The H7-V2 window cuts to 1320 × 1080; a 640 × 525 screenshot is not cut. Then 320 × 240
  → 160 × 120 as B102.
- **Ranks against the picture's own screen-mask tone:** each pixel → the share of the screen mask's pixels darker than
  it by more than τ, plus half the share within ± τ (τ = 2 % of the picture's 2nd-98th percentile spread over the mask;
  ¼-level histogram, O(n)). The screen distance = the median |rank − reference| over the screen mask (B102's median);
  a class distance = the mean over the outcome mask, the same ranks. **Why:** any gain, offset or monotone curve on the
  whole picture leaves every rank unchanged — the reading does not depend on what the tone change is or where it comes
  from; only clipping and JPEG noise move ranks.
- **Departure from a literal reading of "again over the outcome mask" (disclosed):** the outcome pixels are ranked
  against the picture's own screen-mask tone, not the patch's own: a tally patch's own tone taken out over the patch
  alone makes an all-bright 0-0 the same as an all-dark 1-1 (B102's unseen 1-1 would read as the start).
- **What it loses:** two classes that differ only by a whole-picture tone change are **not separable** (the learn
  report says so; tested); **a tally that differs only in tone from the rest of the picture IS told apart** (the
  queue's expected "not told apart" holds for the other reading — tested and stated); a fade of the screen reads as
  the screen while its contrast holds; magnitudes are lost and levels closer than τ count as one; **a flat picture**
  (spread < 8 levels: black, a fade's bottom) has no tone — distance 1.0, never the screen; framing as B102 (the
  search).
- **Thresholds:** B102's halfway rule (`SAFETY` 0.5) across each gap, the own side from frames like their label, the
  foreign side strict; margin needed = half the smallest margin among frames nearest their own class; gap < 0.05 →
  never named.
- **A cost found by the tests (stated):** the tone reference is the screen mask itself, so when much of the still part
  changes, every rank moves: on the synthetic screen a flat patch over **~12-15 % of the still part** is the most that
  still reads as the screen (B102's absolute median allowed up to half). On H7-V2's live pictures other characters
  moved the ranks ~0.04 and every live screen still read (median 0.011 against 0.091); a spec learnt from several
  pairs of characters (as arrangement 3) leaves the portraits out of the still part altogether.
- **The spec:** `"version": 2`, `"measure": "rank-against-screen-mask"`, the rule's constants; **a version-1 spec →
  "this end-screen spec was learnt with the old measure (absolute grey levels): learn it again"**, never read.
- **Commands:** `learn <runs> <labels> [<runs> <labels> …] <out>`, `score` likewise, `read`, **`replay <run folder>
  <spec> [--k K] [--labels L]`** (one `Reader` and `Ended` over the run in order, re-armed after each end; every read,
  every change, each `ended` against the first end-labelled picture after the preceding `other` stretch).

## On the real pictures (run 3; read only; specs in memory, none written; numbers only)

H7-V1: 1,152 labelled frames (start 788, end_P1 72, end_P2 74, other 218), 640 × 525 screenshots. Live: 508 window
pictures, 1920 × 1080, 507 labelled (start 73, end_P1 117, end_P2 103, other 214) + 1 `ignore`.

| arrangement | learnt from | scored on | start | end_P1 | end_P2 | other | **other as screen** | wrong class |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1a | H7-V1 alone | all live | 70 / 73 | 113 / 117 | 98 / 103 | 214 / 214 | **0** | 0 (12 range-edge → `other`) |
| 1b | live alone | all H7-V1 | 788 / 788 | 72 / 72 | 74 / 74 | 218 / 218 | **0** | 0 |
| 2a | live M1 + H7-V1's end_P2 run | live M2 | 0 / 24 | — | 0 / 103 | 112 / 112 | **0** | 0 (all `unknown`) |
| 2b | live M2 + H7-V1's end_P1 run | live M1 | 0 / 49 | 0 / 117 | — | 102 / 102 | **0** | 0 (all `unknown`) |
| 3 | everything | H7-V1 | 788 / 788 | 72 / 72 | 74 / 74 | 218 / 218 | **0** | 0 |
| 3 | everything | live | 70 / 73 | 113 / 117 | 98 / 103 | 214 / 214 | **0** | 0 (12 range-edge → `unknown`) |

- **1a — the question H7-V2 failed:** **495 / 508 live pictures read right** (the 13 others: 12 range-edge pictures —
  the first 3 s after the relaunch, the last 4-5 s before each END — read `other`, and the `ignore` fade); **0 fights
  read as the screen**; least margins 0.19-0.20 (needed 0.100); the live screens' distance median 0.011, 95th 0.014
  against a threshold of 0.091; the nearest fight 0.179. Learn: screen worst own 0.002 / best foreign 0.181; classes'
  gaps 0.20-0.21; masks 16,736 px and 100 px.
- **1b:** learnt from the live pictures alone (3 / 4 / 5 range-edge frames per class counted `unlike_label`), every
  H7-V1 frame right; gaps 0.17; masks 10,346 / 85 px.
- **2a / 2b — across matches and characters:** the learner says what the data can show: in 2a (start and end_P1 from
  match 1 with one pair, end_P2 only from H7-V1 with another) start and end_P2 are **not separable** (gaps 0.010 /
  0.012 < 0.05) and match 2 reads `unknown` throughout; 2b the mirror. **No picture named the wrong class; no fight as
  the screen.** Before amendment 3 the same arrangement named 21 start pictures `end_P2`.
- **3 — the spec A will use** (learnt from both, 11.5 s): **screen threshold 0.0902** (worst own 0.0067, best foreign
  0.1736, gap 0.1669); **class thresholds start 0.1007, end_P1 0.1032, end_P2 0.0990** (gaps 0.176 / 0.190 / 0.177,
  all separable); **margin needed 0.0929**; **screen mask 13,756 px (71.7 %), outcome mask 97 px** (x 63-108, y 84-92 —
  the tallies, as B102's); `unlike_label` start 3, end_P1 4, end_P2 5 (the range-edge pictures); aspect 1.219.
  Read: everything right but the 12 range-edge live pictures (`unknown`); the nearest fight 0.174 (live) / 0.185.

### 4 — tone changes in memory (the full picture, clipped 0-255, before reduction)

27 variants: none; offset −30, −20, −10, +10, +20, +30; gain 0.8, 0.9, 1.1, 1.2; gamma 0.8, 0.9, 1.1, 1.25; every pair
of extremes (gain × offset, gamma × offset, gain × gamma: 12).

- **4a** (learnt on the first halves of both sources; the 831 held-out second halves): **every variant reads every
  picture exactly as untouched — 0 changed, 0 misread, 0 fights as the screen** (right: start 431, end_P1 91 / 95,
  end_P2 84 / 89, other 216; the 9 misses are range-edge pictures read `other` in every variant). The nearest fight
  under the worst pair (gamma 1.25, −30) 0.153 against a threshold of 0.092.
- **4b** (learnt from H7-V1 alone; all 508 live pictures held out): **the same — 0 changed in any variant, 0 fights as
  the screen**; the nearest fight under the worst pair 0.157 against 0.091.
- **The range absorbed with nothing misread: offsets ±30, gains 0.8-1.2, gammas 0.8-1.25 and every pair of those
  extremes** — the whole grid asked for.

### 5 — H7-V1 alone as in B102 (first halves → second halves)

- **Every class right** (start 394, end_P1 36, end_P2 37, other 109 of each); 0 fights as the screen.
- **The search, B102's moved cases:** +2, +4, +8 px; 0, +4 / +8; +8, +8; −6, +5; scales 0.95, 0.97, 1.03, 1.05;
  +5, +3 × 1.04; −4, −6 × 0.96 — **all right**; **+12 px all right** (B102: 145 / 33 / 36); **scale 0.92: 204 / 19 /
  27** (B102: 0 / 1 / 36); +16 px nothing (as B102); **scale 1.08: the ends right, the start `unknown` 394 / 394
  (B102: all right) — the one case the new measure absorbs less** (never `other`, never another class). In every case
  0 fights as the screen.
- **Times on the hub:** one read **1.4 ms** (a 640 × 525 screenshot) / **4.3 ms** (a 1920 × 1080 window), decoded; a
  full search 197-201 ms (B102: 158), at most once per 10 s; learn from everything 11.5 s.

### Replay (`replay`, the arrangement-3 spec, the live run's 508 pictures in order)

- Classes read: start 70, end_P1 113, end_P2 98, other 214, unknown 13; 11 changes.
- **K = 3: `ended` end_P1 at 153.0 s — 2.0 s after the first select-screen picture after match 1 (151.0 s); `ended`
  end_P2 at 420.0 s — 2.0 s after it after match 2 (418.0 s)**; both on the sides the user named.
- **K = 2: 1.0 s after each** (152.0 s, 419.0 s).

## Tests (`tests/b104_h7_tone/`, 19; synthetic pictures with B102's drawing — no game art)

The spec is version 2; **the same screen under offsets ±30, gains 0.8 / 1.2, gammas 0.8 / 1.25 reads the same class
with no search**, and pairs that clip the dark end into one black read the class or `unknown`, never another; **15
fights under each tone never read as the screen**; **two classes differing only by a whole-picture tone → "not
separable"** (outcome mask 0 px; never named); a tally whose tone alone differs → told apart (disclosed); **a picture
inside black bars of other sizes (pillar, letter box, 1920 × 1080, 2 ×) reads as the bare picture with no search, and
so does a window whose bars changed tone with it**; a one-sided or thin dark border not cut; flat pictures never the
screen; **a version-1 spec refused with the plain line** (load, Reader, the CLI) and a version-3 one with B102's; two
sources of different sizes and tones learnt together (every held-out picture right, per source); a slip (a 0-0 labelled
1-0) does not set 1-0's threshold and makes 0-0 "not separable" — loud at learning, never a guess; a labelled screen
under a notice does not loosen the screen's threshold; a pair never seen in one source cannot make the outcome mask (a
source-bound patch left out); a mark under the tally in half of one class's frames stays out of the outcome mask; a
tiny positive gap (one source's noiseless 0-1 against the other's 0-0) is "not separable"; a labelled screen mostly
under a notice does not set the screen's threshold; a flat patch over ~12 % of the still part still reads (the median,
where a mean would not); **`replay`** (the ended moments 2.0 / 1.0 s after the end screen, re-armed, the CLI);
one read in milliseconds. **B102's 16 unchanged, green.** Results: `tests_x3.txt` (3 runs), `tests_mutations.txt`.
**Disclosed: the first mutation run (15 tests) caught 11 / 15** (`tests_mutations_first.txt`, `tests_x3_first.txt`):
the steadiness against the separation, the minimum gap, the screen-side "unlike" rule and the median were not pinned by
any test. The four tests above were added for them (the fourth found the 12-15 % limit stated above), and the 3 runs
and all 15 mutations run again: **3 runs × (19 + B102's 16) green, temp dirs left 0; 14 / 15 caught** — still missed: **M13, the screen distance a mean instead of the median**: with a mean the thresholds are learnt in the mean too, and every synthetic case still reads; the median is kept as B102's (it tolerates more change of the still part on the real pictures), but no test pins it.

## Disclosed

- The design was chosen after a read-only look at the real pictures (above), and two amendments came after runs on
  them; every run is kept, and the reported numbers are from one full run after the last amendment.
- The hub was otherwise idle; the evaluation ran niced on 8 processes; nothing was written beside the pictures; the
  reduced arrays of the first look and the prototypes' cache sit outside git under the session's own temp folder.
- The mutation runner is B101's with one change: several suites per mutation (`scripts/mutate.py`).
- File names in the scripts carry the queue's label for the run folders as the queue does; no title, character name
  or path of the user's is in any file here (title / redact checks).

## Files

`b104_2026-11-16/`: start files, the design + amendments 1-4 + their hashes and times, `pre_design_look/`,
`amendment3_look/`, `run1_before_amendment3_*`, `run2_before_amendment4_stopped.*`, `real_eval.py` +
`real_eval_results.jsonl` (run 3) + its times, `b104.diff` (applies on `d61f9b56`), `diffs_apply_in_order.txt`,
`sha256_before_after.txt`, `tests_x3.txt`, `tests_mutations.txt`, `scripts/` (`run_all.sh`, `mutate.py`,
`mutations.json`), redact / title checks, `manifest.sha256`. Patch note: `patches/B104_H7_TONE_INDEPENDENT_READ.md`.
