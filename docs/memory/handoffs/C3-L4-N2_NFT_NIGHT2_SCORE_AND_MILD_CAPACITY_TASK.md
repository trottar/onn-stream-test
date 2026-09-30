---
memory_schema: 1
as_of: 2026-09-29
status: TASK HANDOFF — C3-L4-N2: (1) score the user's nft night 2 (run c3_l4_nft_night_20260929_174201Z, --only F1,F3) against its pre-registration, read-only; (2) add the mild-capacity rule the user approved on 2026-09-29 ("Go") to the LIVE policy — ROUTINE one rung down on fps < 57 on >= 4 of 5 and lost >= 50 on >= 3 of 5; (3) replays with the stop rule; (4) a 30-minute silent live hold; (5) night 3's pre-registration (--only F1) and the user's hand steps; then the C5 nights follow on the same prompt; nothing adopted; nothing committed
---

# C3-L4-N2 — night 2 scored, the mild-capacity rule

**Why.** Night 2 (2026-09-29 17:42-18:10Z, run dir
`logs/streaming/c3_l4_nft_night_20260929_174201Z/`, `--only F1,F3`):
the capacity FALLBACK fired 14 s after the cap (7000 → 5000, one
transition, no recovery cycle); the blend climbed 5000 → 5500 (fits) →
6000 (does not fit); **at 6000 under the cap the stream sat degraded for
the remaining 4 minutes** — fps median 55.8, p10 47.9, under 50 on only
17 % of reports, ~61 lost packets per report, 39 % clean, queue 0 — and
nothing fired: the capacity trigger needs fps < 50 on all 5, ROUTINE
needs queue ≥ 1. Cap off → 6000 → 7000 after ≥ 93 reports; F3's cap
brought the stream to 5000 in 17 s and the 15 s full drop recovered with
one `encoder_restart`, the level held at 5000. Teardown clean.

**The user approved on 2026-09-29 ("Go")** a milder form of the capacity
rule for the shortfall that is not severe enough for the strict one.
Cowork's simulation on the recorded samples (to be confirmed): the rule
fires 45 s into the 6000 rung of night 2 and 8 s into night 1's caps;
never at 5000 or 5500 under the cap, never with the cap off, never in
night 1's 2 % random loss or any baseline.

Read first: night 2's run dir (every file), its `preregistration.txt`
(sha256 `3cdcfa2e…`), `C3_L4_N1_CAPACITY_TRIGGER_2026-09-29.md` (§2 the
rules as built, §3 the replay harness and stop rule, §5 the harness
`--only`), `C3_L4_NFT_NIGHT1_2026-09-29.md` (the record shape),
`companion/adaptive_bitrate_live.py`, `decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`,
`TOOLS.md`.

## 1. Score night 2 (read-only, first)

Against the night-2 pre-registration row by row (F1a-f, F3pre, F3a, F3b,
the all-sessions rows), from the run dir only. Expected (confirm or
correct): F1a MET (capacity FALLBACK at +14 s, one `ssrc_change`); F1b —
say plainly which branch applied: the climb 5000 → 5500 → 6000 matched
the rules and their spacing (117 and 134 reports apart), but the
expected capacity FALLBACK from 6000 never came, so the HOLD row was
never reached — record F1b as MET on every transition that occurred and
name the 6000 rung's 4 minutes as the finding; F1c MET; F1d MET (one
rung to 7000 after ≥ 93 reports); F1e backstop did not fire, MET; F1f
recovery cycles under the cap 0, MET; F3pre MET (+17 s); F3a MET; F3b —
confirm the restart's level from the decoder report's bitrate after the
`ssrc_change` (the recovery log's cycle does not carry it) and the
absence of `level_sync`; the all-sessions rows. Two things to check and
state: (i) after F3's BACK the harness read `level 5000` where F1's read
7000 — a status-read race or a real reset defect? (the
`session_ended_reset` rows at 18:09:16/19 and the teardown's 7000 say
which); (ii) the four `session_ended_reset` rows at the end — harmless
duplicates or not. Classification per the pre-registration. Write
`evidence/C3_L4_NFT_NIGHT2_2026-09-29.md`; copy the run dir into
`evidence/c3_l4_nft_night2_2026-09-29/` (redacted, manifest).

## 2. The rule — LIVE policy only (the shadow stays unchanged)

**Mild capacity** — class ROUTINE, reason `capacity_mild`, one rung down
(the ROUTINE step; from 6000 → 5500, from 5500 → 5000, from 7000 → 6000;
at 5000 `at_floor`, logged): over the last 5 fresh evaluated reports,
**fps < 57 on ≥ 4 of 5 and `lost_packets_delta` ≥ 50 on ≥ 3 of 5**. The
strict capacity trigger (fps < 50 on all 5 …) keeps precedence when both
hold. Same blackout, hold-downs (ROUTINE 60), rate limit, oscillation
guard, guards as every ROUTINE; a stale report or missing delta does not
count. Everything else in `LivePolicy` unchanged. Decision record: append
as the user's decision of 2026-09-29.

## 3. Tests and replays — before any session

- Synthetic: fires at 4/5 fps < 57 with 3/5 loss ≥ 50; not at 3/5 fps or
  2/5 loss; not on loss alone; not on fps alone (the old ROUTINE's queue
  path unchanged); strict wins when both hold; one rung, never two; at
  5000 → `at_floor`; blackout / hold-down / rate limit / recovery guard
  all bind; the L1/L2/N1 suites and the shadow suite pass; parity
  (shadow night → live) still zero actions.
- **Night 2's samples** through the new policy: expected `capacity_mild`
  6000 → 5500 ~45 s into the 6000 rung, then (counterfactual) the
  increase to 6000 ≥ 93 reports later, `capacity_mild` back to 5500 after
  the ROUTINE hold-down, then HOLD `oscillation` — state it as a
  prediction; nothing at 5000/5500 under the cap, cap off, or F3.
- **Night 1's samples**: `capacity_mild` ~8 s into each cap (the strict
  rule at ~14 s: strict wins if both hold in the same window — say which
  fires first as built); nothing in F2 or the baselines.
- **Every recorded series** (as N1 §3, plus N1's silent hold and night
  2): the would-fire list. **Stop rule unchanged**: if the new rule fires
  on a clean-link session outside a deliberate fault or a recorded link
  drop, stop before any session, record it with the samples, leave the
  rule as approved — the user decides.

## 4. Session — silent live hold

30 minutes attract mode, live mode, clean link, T2 on. Pre-registered:
**SILENT** if zero transitions and the close-out rows met; otherwise what
fired and why. Also report the near-miss count for the new rule (windows
with ≥ 4/5 under 57; windows with ≥ 3/5 lost ≥ 50). Flag unset and
absent afterwards.

## 5. Night 3 — `--only F1`, the pre-registration and the hand steps

`c3_l4_nft_night3_preregistration.txt`, written before the night: F1a
the strict capacity FALLBACK 7000 → 5000 within 60 s; F1b the climb
5000 → 5500 (≥ 93 reports), 5500 → 6000 (≥ 93), then **`capacity_mild`
6000 → 5500 within 90 s of arriving at 6000** (one transition), then the
next increase attempt (≥ 93 reports) → 6000 → `capacity_mild` back after
the ROUTINE hold-down → the third direction change inside 10 min becomes
HOLD `oscillation` at 5500 for the session; or "climbed to <rung> and
stayed" if the calibrated cap lets it through (recorded, not a failure);
if the 3rd direction change falls more than 10 min after the 1st it is
an INCREASE, not a HOLD (as built); F1c-f as night 2; after removal:
nothing if HOLD, else one rung per ≥ 93 reports; BACK resets to 7000.
The hand steps: one PowerShell SSH window, as L2B.4 with `--only F1`
(about 25 minutes).

## 6. Then, on this same prompt

Only after §1-5 are recorded and the flags confirmed absent: run
`C5-M2_1080P60_FOLLOWUP_ARMS_TASK.md` and then
`C5-M3_LOW_RUNG_SCREENING_TASK.md`, exactly as written, under
`QUEUE_2026-09-29B.md`'s rules (the profile selector only inside their
arm holds; unset and absent at the end). `CURRENT.md` at the very end:
Next Action 1 is the user's night 3 (`--only F1`); then the user's
picture check on any CAPABLE 1080p or low-rung arm; then the next
adopted APK with `CL-B1`; then C7/D8 checkpoint and a commit (the
user's).

## Record and memory

`evidence/C3_L4_NFT_NIGHT2_2026-09-29.md`;
`evidence/C3_L4_N2_MILD_CAPACITY_2026-09-29.md` (the rule as built, tests,
replays and would-fire lists, the silent hold, night 3's pre-registration
and hand steps); evidence dirs with manifests; `patches/C3-L4-N2_*.md`;
`PATCH_INDEX.md`; the decision record (append);
`architecture/ADAPTIVE_BITRATE.md`; `docs/ROADMAP.md` C3; `CURRENT.md`;
`investigations/ACTIVE.md`; `TOOLS.md`; the daily file;
`evidence/RUNTIME_VALIDATION.md`; then the C5-M2 and C5-M3 records as
their tasks say. Adopted profile and APK throughout; flags and selector
unset and absent at the end; Code never runs `nft` or real `sudo`. No
addresses. Nothing adopted. Nothing committed.
