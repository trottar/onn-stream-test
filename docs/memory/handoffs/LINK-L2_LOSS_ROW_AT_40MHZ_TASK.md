---
memory_schema: 1
as_of: 2026-10-01
status: TASK HANDOFF — LINK-L2: the LINK-L1 day repeated on the user's 40 MHz link — the same pre-registered rule (STILL MET / TIME OF DAY / MOVED / MIXED), six 20-min holds one per 4-hour block, adaptive bitrate switched to shadow per session so the holds are comparable with LINK-L1, the Opal's air view read-only before every hold. Stops before the holds if the air view still reads 80 MHz. Decides the link; Part 2 (the 1080p rung) waits for the user's word
---

# LINK-L2 — the loss row at 40 MHz

**Why.** LINK-L1 (2026-10-01) was MIXED on the 80 MHz link: 3 of 6 holds
met post-FEC loss < 10/min, misses at every hour, 0 neighbours on
primary 36 but 3-4 strong ones on the 80 MHz block's secondaries. The
user is changing the Opal's 5 GHz width to 40 MHz by hand (channel 36
kept). This task measures the same thing again so the two days can be
read side by side. **Nothing else changes**: the adopted profile at 7000
now carries the PS1 source at 4x (C5-M4A), which LINK-L1 did not; its
frame-size effect is small (per-second largest frame p50 44 → 47-50 KB,
no ≥ 80-packet frames) and is reported beside the rows.

Read first: `evidence/LINK_L1_LOSS_ROW_2026-10-01.md` (the rule, the
history table, the air view and its tools — `link_l1_air.py`),
`link_l1_2026-10-01/link_l1_preregistration.txt`,
`evidence/C3_L4_D1_LIVE_DEFAULT_2026-10-01.md` (live is the default; the
per-session kill switch `POST /plugins/games/adaptive-bitrate/disable`
→ shadow for one session), `evidence/C5_M4A_PS1_4X_SOURCE_ADOPTION_2026-10-01.md`
(the hold harness that already expects the 4x window and the APK
`de072762…835e`), `TOOLS.md`, `CURRENT.md`.

## 0. First: the air view, read-only

Before anything else, read the Opal as LINK-L1's A2 did: channel, width,
idle utilization, noise, the onn's link rate / MCS / RSSI, neighbour
counts on primary 36, in the 36-40 block and the 44-48 pair, 52-64, as
counts only. **If the width is not 40 MHz, write
`evidence/LINK_L2_LOSS_ROW_<date>.md` with that one finding and stop** —
the user makes the change and prompts again. If it is 40 MHz, continue.

## 1. Pre-registration, before any hold

`evidence/link_l2_<date>/link_l2_preregistration.txt`, hashed. **The
rule is LINK-L1's, verbatim** (six holds, one per local 4-hour block,
≥ 30 min idle before each; STILL MET ≥ 5 of 6; TIME OF DAY = every miss
inside one contiguous ≤ 12-hour window with ≥ 2 meets and ≥ 2 misses;
MOVED ≤ 1 meet; otherwise MIXED), plus:

- **Adaptive bitrate in shadow for every hold**: the disable route is
  called after PLAYING (as D1 documents it), and the status must read
  shadow / `acts false` for the hold; the decision log is kept. A hold
  in which the controller nonetheless acted is excluded and re-run once
  (the two-retry limit). This keeps the loss row comparable with
  LINK-L1's adaptive-off holds.
- The holds carry the adopted 4x PS1 source; the frame-size columns
  (per-second largest frame p50/p90, cap hits s/min, ≥ 80-packet
  frames/min) are reported beside LINK-L1's.
- The side-by-side: LINK-L1's six holds and these six, same blocks, loss
  and max gap in one table, plus retries and link rate / MCS — reported;
  the classification is this day's alone.

## 2. The six holds

C5-M4A's harness (`c5_m4a_hold.sh` / `c5_m4_run.sh`), 20 minutes each,
attract mode at 7000, `any_override` false, T2 on, the air view read
once at the start of each hold and once between holds. Teardown after
each: the companion back to live by default (the disable is
per-session; confirm the next session's status reads live before its
own disable), stream 7000, no game, 0 banners.

## 3. The record

`evidence/LINK_L2_LOSS_ROW_<date>.md`: the air view (then and now: 80 vs
40 MHz, link rate / MCS, neighbour counts, utilization); the six holds
scored; the side-by-side with LINK-L1; the classification; **what it
means, as options, not a decision**:

- STILL MET → the baseline holds on this width; Part 2's screening can be
  scheduled;
- TIME OF DAY → the window named; screening in it;
- MOVED → 40 MHz made it worse: the user reverts to 80 MHz (hand) and the
  next lever is the channel (the empty 52-64 block) or a wired hop;
- MIXED → no change from the width; the levers left are the channel, the
  onn's placement, or a wired hop — with what the air view says.

`investigations/ACTIVE.md`: the LINK item updated. `evidence/RUNTIME_VALIDATION.md`.
`CURRENT.md` last — Next Action 1: the user's commit; 2: the user's call
on the link from the options above; 3: Part 2, the 1080p rung
(`C5_M4_PS1_NATIVE_1080P_SOURCE_2026-10-01.md` §4's design: first the
mid-session size change on the encoder restart, then the rung, tests,
replays, one pre-registered night) on the user's word, after the link is
settled; the user's picture look at 4x (dither mode) whenever they like.
Evidence dir with manifest and the redactor `--check`
(`evidence/h2_prep_2026-09-22/h2_prep_redact.py`); `check_memory_health.py`
healthy; `git status --short` and `git diff --stat` to
`logs/link_l2_git_status.txt`.

No `nft`, no real `sudo`, the Opal read-only, no addresses, MACs, SSIDs,
BSSIDs, ADB endpoints, serials or credentials anywhere. Adopted profile,
source and APK throughout. Nothing adopted. Nothing committed.
