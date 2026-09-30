---
memory_schema: 1
as_of: 2026-09-29
status: TASK HANDOFF — C3-L4-N1: (1) score the user's first nft night (run c3_l4_nft_night_20260929_151942Z) against its pre-registration, read-only; (2) add the two rules the user approved on 2026-09-29 ("Yes, add both") to the LIVE policy — a capacity trigger and a recovery-escalation backstop; (3) replay every recorded series through them; (4) a 30-minute silent live hold; (5) the harness gains --only F1,F3 and the second night's pre-registration; nothing adopted; nothing committed
---

# C3-L4-N1 — night 1 scored, the capacity trigger, the backstop

**Why.** The user's `nft` night (2026-09-29, 15:19-16:17Z, run dir
`logs/streaming/c3_l4_nft_night_20260929_151942Z/`) found that under a
bandwidth cap the live controller **never stepped down**. Cowork's
read of the per-report samples (to be confirmed by this task):

- the cap (854 kB/s, between the 5500 and 6000 wire rates) took fps from
  ~60 to 15-40 within 4 s, with ~250 lost video packets per report and
  **queue depth 0** throughout;
- the shadow-derived triggers need queued frames (ROUTINE: queue ≥ 1 on
  ≥ 3/5; FALLBACK: fps < 50 on all 5 **and** queue ≥ 2 on ≥ 3/5 **or**
  gap > 250 on ≥ 2/5) — a capacity shortfall shows none of that until a
  freeze, and a freeze > ~1.1 s is recovery's (`client_output_silence`);
- so recovery restarted the encoder **at 7000** 9 times in 12 minutes
  (C3-F1, level-preserving), each time into the same shortfall, and the
  controller's 3 FALLBACK attempts were correctly refused by the
  recovery guard;
- F2 (2 % random loss) was correctly ignored (fps median 59.7, lost 4 per
  report); the F3 drop at 7000 recovered with one restart; K worked; the
  teardown was clean (no fault table, flag absent, 7000, no game).

A capacity-trigger simulation on the night's samples (fps < 50 on all 5
and lost ≥ 50 on ≥ 3 of 5) fired 14 s after the F1 cap and 20 s after the
K cap, and never in the baseline, after the cap was removed, or under F2.
**The user approved both rules below on 2026-09-29.**

Read first: the night's run dir (every file), its
`preregistration.txt` (sha256 `fb5ca63f…`), `C3_L4_L2_INCREASE_RULE_2026-09-29.md`
(incl. L2B), `C3_L4_L1_LIVE_CONTROLLER_2026-09-28.md` (§1 the mapping
table, §7), `companion/adaptive_bitrate.py` (the shadow's trigger
constants, lines ~64-71) and `adaptive_bitrate_live.py`,
`decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`,
`C3_F1_RECOVERY_RESTART_LADDER_2026-09-25.md`, the recovery state machine
(`client_output_silence`, its thresholds and backoff), `TOOLS.md`.

## 1. Score night 1 (read-only, first)

Against the night's pre-registration, row by row (F1a-d, F2a, F3a-b,
Ka-c, the all-sessions rows), from the run dir only; recompute the
figures above; every refused row with its guard; the recovery-log cycles
per session with their triggers and gaps; the close-out rows per session
(reported). Classification per the pre-registration: **WORKS UNDER LOSS**
or the rows that did not hold. Expected (confirm or correct): F1a NOT
MET (no decrease), F1b/F1d NOT APPLICABLE, F1c MET, F2a MET, F3a MET,
F3b NOT TESTED (the precondition, reaching 5000, was never met), Ka-c
MET. Write `evidence/C3_L4_NFT_NIGHT1_2026-09-29.md`; copy the run dir
into `evidence/c3_l4_nft_night1_2026-09-29/` (redacted; manifest).

## 2. The two rules — LIVE policy only (the shadow stays unchanged)

**(a) Capacity trigger** — class FALLBACK, reason `capacity`, target 5000
(the mapping table's FALLBACK target): over the last 5 fresh evaluated
reports, **fps < 50 on all 5 and `lost_packets_delta` ≥ 50 on ≥ 3 of 5**.
Same blackout, hold-downs, rate limit, oscillation guard and guards as
every FALLBACK. A stale report or a missing loss delta does not count
toward the ≥ 3. `lost_packets_delta` must be the per-report delta of the
client's post-FEC lost video packets — state which counter it is and
whether an SSRC change or a sequence resync can inflate it (the 3-report
blackout covers the resync; say whether that is enough).

**(b) Recovery-escalation backstop** — class FALLBACK, reason
`recovery_escalation`, target 5000: when recovery has **restarted the
encoder twice at the same level within 180 s** (count `encoder_restart`
events, not `desync_pause` alone), the controller, **after** recovery is
back to PLAYING and the 3-report blackout has passed, makes one FALLBACK
to 5000 if the level is above 5000 (else `at_floor`, logged). All guards,
hold-downs and the rate limit apply. Recovery itself is **unchanged**
(C3-F1 stays level-preserving; the controller moves the level, recovery
never does). Say where the controller reads recovery's events from and
how the two stay serialized.

Everything else in `LivePolicy` is unchanged (the blend's increase rule,
blackout 3, hold-downs, rate limit 4/10 min, oscillation guard, age and
recovery guards, the disable route). The decision record gets both rules
appended as the user's decision of 2026-09-29.

## 3. Tests and replays — before any session

- Synthetic tests for both rules: fires at exactly 5/5 fps < 50 with
  3/5 loss ≥ 50; not at 4/5 fps or 2/5 loss; not on loss alone (fps ≥ 50
  with any loss); not on stale reports; not while recovery is not
  PLAYING; the backstop fires once after the second restart within 180 s
  and not after two restarts 181 s apart or at different levels; neither
  fires during a blackout or hold-down; the rate limit still binds.
- The L1/L2 live suites and the shadow suite pass; parity (the shadow
  night through live) still zero actions.
- **Night 1's own samples replayed** through the new live policy: the
  would-fire list per session — expected a capacity FALLBACK in F1 about
  14 s after the cap and in K about 20 s after (K then disabled → would
  act only), nothing in the baselines, after removal, or in F2; then, for
  F1, what the blend's climb would have done under the cap (state it as
  a prediction, not a result).
- **Every recorded series** through the new live policy (the C4-D1 and
  CTRL-L1 heartbeats with the loss-counter proxy, the S1 shadow night,
  L1's and L2's sessions, the C3.L3a sessions, C5-M1's 720p B holds):
  the would-fire list with each firing's cause. **Stop rule**: if either
  new rule fires on a clean-link session outside a deliberate fault or a
  recorded link drop, stop before any session, record it with the
  samples, and leave the rules as approved — the user decides; do not
  retune.

## 4. Session — silent live hold

30 minutes attract mode, live mode, clean link, T2 on. Pre-registered:
**SILENT** if zero transitions and the close-out rows met; otherwise what
fired and why (from the sample rows). Flag unset and absent afterwards.

## 5. The harness for night 2

- `--only F1,F3` (any subset of F1, F2, F3, K) runs just those parts;
  preflight, setup, teardown and the always-clear paths unchanged.
- The **night-2 pre-registration** (`c3_l4_nft_night2_preregistration.txt`),
  written before the night from night 1's rules with the new triggers:
  F1a the capacity FALLBACK 7000 → 5000 within 60 s of the cap, one
  transition; F1b the blend's climb under the cap (5500 fits; 6000 does
  not → capacity FALLBACK back to 5000 after the reversal hold-down; the
  next increase becomes HOLD `oscillation`), or "climbed to <rung> and
  stayed" if the calibrated cap lets 6000 through; F1c rate limit never,
  no ramp; F1d after removal as before; the backstop row — expected not
  to fire because the capacity trigger acts first, recorded either way;
  recovery cycles under the cap reported (expected ≤ 1); F3a/F3b as
  night 1 (now reachable: the cap brings the stream to 5000 first).
- Fake-sudo tests of `--only F1,F3` (a `--fast` run and one forced abort);
  the real sudo path only on the user's night.
- **The user's hand steps** for night 2, for one PowerShell SSH window,
  exactly as L2B.4 but with `--only F1,F3` (about 45 minutes).

## Record and memory

`evidence/C3_L4_NFT_NIGHT1_2026-09-29.md` (§1);
`evidence/C3_L4_N1_CAPACITY_TRIGGER_2026-09-29.md` (the rules as built,
tests, replays with would-fire lists, the silent hold, the harness change,
night 2's pre-registration and hand steps); evidence dirs with manifests;
`patches/C3-L4-N1_*.md`; `PATCH_INDEX.md`; the decision record (append);
`architecture/ADAPTIVE_BITRATE.md` (live triggers as built);
`docs/ROADMAP.md` C3; `CURRENT.md` (Next Action 1: the user's night 2);
`investigations/ACTIVE.md`; `TOOLS.md`; the daily file;
`evidence/RUNTIME_VALIDATION.md`. Adopted profile and APK throughout; the
flags unset and absent at the end; Code never runs `nft` or real `sudo`.
No addresses. Nothing adopted. Nothing committed.
