---
memory_schema: 1
as_of: 2026-09-24
status: TASK HANDOFF — C3.L3a rerun session 3 of 4 (run 20260924_151953, 9 marks, report STORED under the raised cap): record it, mark the cap RUNTIME VALIDATED, write the interim pooled table (3 sessions, no verdict); docs only; authorized by the user 2026-09-24
---

# C3-L3A-R3 — rerun session 3, recorded; the cap validated at runtime

**What happened.** Run **`20260924_151953`**, Phase A 775.723 s, 20
transitions, 10 decoys, **9 marks**, not aborted; state copy
`logs/streaming/c3_l3a_runs/states/20260924_151953_state.json`; session
and finalize logs under `logs/streaming/` (the `c3_l3a_session_20260924_15…`
and `c3_l3a_finalize_20260924_15…` files). **The client's report was
stored**: `native_decoder_20260924_193658_993.json` (19:36:58Z,
1,035,174 ms, 24 SSRC changes = 24 expected) — the first 24-transition
session stored since `C3-L3A-R2B` raised the cap (32,057-char reports
were refused before). Phase B answered: 6000 **n / 8**, 5500 **y / 8**,
5000 **y / 8** on the anchored scale (the 6000 "n" beside an 8 is recorded
as typed; the user has not commented). The user has not stated the title.

**Scope.** Documentation only. No probe, companion, client, profile or
environment change; no session; nothing modified under `logs/`.

## Record — `evidence/C3_L3A_R3_SESSION3_2026-09-24.md`

From `c3_l3a_runs/20260924_151953.{json,txt}` and the decoder report:

- Detection at all three windows; at W 5.0: jump 1/5 (1 mark, 31.5 s;
  chance-expected 0.37), ramp 2/5 (2 marks, 82.6 s; 0.96), decoy
  jump-matched 1/10 (0.58), decoy ramp-matched 3/10 (1.91), 6 marks in no
  sequence window; chance rate 0.0116/s. Mark lags: the two ramp marks at
  1.58 and 2.11 s after a rung (the reaction pattern of sessions 1-2); the
  jump mark at **0.51 s** after the fire and the jump-matched decoy mark at
  **0.20 s** after the decoy are both shorter than any reaction lag seen
  (1.44 s minimum across 22 marks in sessions 1-2) — say so, attribute
  neither. Per-mark decoder check as in R1/R2B (`mark_check.py`),
  noting the slow-event buffer saturated again (128 of 128; marked ring
  from probe 352.0 s) so marks before that are checkable only through the
  top-gap list.
- Alignment: 20 pairs, offset 12.62 s, spread 0.404 s, max residual
  0.255 s. Per-transition table (12 covered: gaps 135-194 ms, codec 7-13;
  one "65 partial"); `jump_packets` 0 on all 24; first IDR 14-63 ms. The
  session's `max_output_gap_ms` **564** — locate it on the decoder axis
  (probe time, nearest fire or decoy, the slow event's `codec_ms`) and say
  what it was; it is the largest gap seen in any rerun session.
- Close-out rows: 17.25 min, spikes 39.18/min, fps 59.72, stale 1.22/min,
  video loss post-FEC 4.29/min (74 lost, 15 unrecoverable groups), max gap
  564; beside C / W. Settling 10/10 (1.0-4.0 s); lifecycle 0/0/0;
  controller `lost_packets` from `conditions_before/after` per minute
  (add to the `KNOWN_ISSUES.md` controller item's table: session 1 ~225,
  session 2 ~3.8, session 3 = ?).
- **Cap RUNTIME VALIDATED**: the 24-change report was stored; give its
  compact size and headroom under 48,000 (as `report_check.py` measured
  the earlier ones); update `evidence/RUNTIME_VALIDATION.md` and the
  `KNOWN_ISSUES.md` cap item (mitigated and validated; body-POST follow-up
  still open).
- **Interim pooled table, 3 sessions, W 5.0, no verdict** (run
  `--aggregate`; it pools three): jump **5/15** marked (5 marks, 93.8 s
  exposure, chance-expected 2.12), ramp **11/15** (20 marks, 248.7 s, 5.64),
  decoy jump-matched **4/30** (4, 150.0 s, 3.39), decoy ramp-matched
  **9/30** (9, 496.2 s, 11.24). Also the 2.5 and 8.0 rows as printed.
  State the pre-registered bar (≥ 20 per shape, 4 sessions) is not yet
  reached and that the reading is the user's. Phase B pooled: sessions 1-2
  defaulted (user's stated 6-7 for session 1), session 3 as typed.
- Per-session pattern, as facts: marks behind a measured restart gap —
  session 1: 11, session 2: 10, session 3: 2; total marks 19 / 26 / 9;
  titles: Crash Bandicoot / not stated / not stated.

## Memory

Evidence under `evidence/c3_l3a_r3_2026-09-24/` (byte copies of the state,
the decoder report, the logs, the run files, the aggregate outputs,
`mark_check.{py,txt}`, manifest). `investigations/ACTIVE.md` §C3.L3a,
`CURRENT.md` (session 4 awaiting the user; the interim table in one line;
`python3 tools/check_memory_health.py` healthy), `2026-09-24.md`,
`handoffs/CURRENT_HANDOFF.md` one line. No addresses or device identifiers.
Nothing committed.
