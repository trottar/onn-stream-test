---
memory_schema: 1
as_of: 2026-09-28
status: TASK HANDOFF — C3-L3A-R4: record rerun session 4 (run 20260928_122028) from the files on disk, the pooled four-session table, and the user's gate reading (given 2026-09-28: C3.L4 authorized for one restart per adaptation event; ramps excluded); record the user's D7 hands-on rows, the FEC decision and the CL-B1 adoption call; no code change, no session, no companion restart; authorized by the user 2026-09-28
---

# C3-L3A-R4 — session 4, the pooled table, and the gate reading

**Why.** Session 4 ran 2026-09-28 (probe run `20260928_122028`; the user
ran `--finalize` and `--aggregate` themselves). Four pre-registered
sessions are pooled. The user has read the table and given the gate
reading below. Nothing of this is in `docs/memory/` yet. This task
records it; it changes no code and runs no session.

Read first: `C3_L3A_R3_SESSION3_2026-09-24.md` (the record shape to
repeat), `C3_L3A_P2R3_POOLING_RULE_2026-09-24.md`,
`decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`,
`architecture/ADAPTIVE_BITRATE.md` (the C3.L4 shadow section),
`C3_L4_S1_SHADOW_CONTROLLER_2026-09-24.md`, `D7_R1_LINUX_REGRESSION_2026-09-25.md`
(the NEEDS USER list and the D8 table), `decisions/C4_ADAPTIVE_FEC_2026-09-24.md`,
`CL_B1_DECODER_REPORT_BODY_2026-09-25.md`, `docs/ROADMAP.md` §C3-C7 and §D7-D8.

## Inputs on disk (read, verify, copy — never regenerate)

- `logs/streaming/c3_l3a_session_20260928_122015.log` (preflight refused:
  stream not active — the game was still on its frozen preview; the user
  pressed RESUME PLAYING and started again) and
  `c3_l3a_session_20260928_122028.log` (the run: 27 marks in Phase A).
- `logs/streaming/c3_l3a_runs/states/20260928_122028_state.json` and
  `c3_l3a_gameplay_acceptance_state.json` (identical run; say so by hash).
- `logs/streaming/c3_l3a_finalize_20260928_123719.log`,
  `c3_l3a_gameplay_acceptance.{txt,json}` (session 4's own report; decoder
  session `native_decoder_20260928_163654_864.json`, auto-selected, 24 of
  24 SSRC changes).
- `logs/streaming/c3_l3a_aggregate.{txt,json}` and
  `c3_l3a_aggregate_stdout.log` (four runs POOLED, none skipped).
- `logs/games/decoder_sessions/native_decoder_20260928_163654_864.json`.
- The companion journal for the session window (redacted).

Verify before recording: 24 = 20 + 3 + 1 SSRC changes; clock alignment
OK (spread 0.408 s); settling 10 of 10 (1.0-4.0 s); lifecycle deltas 0/0/0;
report stored with 0 `WARNING decoder-session-log`; the pooled counts
recomputed from the four run files match `c3_l3a_aggregate.json`.

## Session 4, what to say

- Detection at W 5.0: jump 1/5 (1 mark vs 1.09 chance), ramp 4/5 (9 marks
  vs 2.88), decoys 0/10 jump-matched and 4/10 ramp-matched (5 vs 5.75).
  Ramp marks 1.78-5.86 s behind their fires — the reaction lag seen before.
- 17 of 27 marks fall in no sequence window, 30-60 s from any fire. This
  session carried more transport loss than sessions 1-3 (post-FEC
  10.02/min, 42 unrecoverable groups, controller lost ≈ 3,115 over
  16.6 min against ≈ 5.6/min in session 3): state the numbers and say the
  out-of-window marks are consistent with transport hitches, not
  transitions, and count neither for nor against the gate. Do not
  attribute a single mark to a specific loss event unless the decoder ring
  shows one inside its lag window (the ring is saturated from probe 257.7 s;
  say what is covered).
- Picture, as typed: 6000 defaulted (bare Enter; the prompt's default is
  N), 5500 y/7, 5000 y/7.
- Close-out rows beside the session (context, not a gate; 24 deliberate
  restarts): spikes 41.0/min, rendered fps 59.66, stale 1.21/min, video
  lost 10.02/min, max gap 426 ms (the 5000 park's first IDR at 240 ms, the
  same shape as session 3's restore).

## The pooled table (four sessions, W 5.0, Phase A 3,157 s, 81 marks)

| class | marked | marks | chance-expected |
| --- | --- | --- | --- |
| jump | 6 / 20 | 6 | 3.21 |
| ramp | 15 / 20 | 29 | 8.52 |
| decoy, jump-matched | 4 / 40 | 4 | 5.13 |
| decoy, ramp-matched | 13 / 40 | 14 | 16.99 |

Also at W 2.5 and 8.0 from the aggregate. Picture pooled: 5500 and 5000
acceptable at 7-8 in the two sessions rated (9/9/9 on the smoke session);
6000 rated 8 once, otherwise defaulted; sessions 1-2 defaulted by
accidental Enter (the user's stated rating 6-7, levels not distinguished).

## The gate reading — the user's, 2026-09-28, recorded verbatim as agreed

> A single unannounced encoder restart during play is not reliably noticed
> and the destination levels look fine, so C3.L4 is authorized for one
> restart per adaptation event — the controller goes straight to its
> target level in a single transition, with the existing hold-downs. Three
> restarts four seconds apart (a ramp) are noticed, so the ramp shape is
> excluded from live adaptation; the ladder stays for choosing the target,
> not for stepping through it. Cost per event stays ~190 ms of output gap.

Write it as `decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`: the table
it rests on, the four records, the reading, and what it does **not**
authorize (a ramp; sampling inside the settling window; any live run
before a fault-injection night with the user's `nft`, which is the next
C3.L4 task, not this one). `C3.L4` classification: **AUTHORIZED, single
transition per event; live build pending**. `architecture/ADAPTIVE_BITRATE.md`
gains the constraint (one transition per event, minimum spacing = the
existing hold-downs, no ramps) in the live-mode section, marked as a
decision, with no code change here.

## The other three records

1. **D7's hands-on rows** (`D7_R1_LINUX_REGRESSION_2026-09-25.md`, a new
   section "R3 — the user's rows, 2026-09-28"): the user did the six-step
   list with Tekken 3 and reported, verbatim: *"everything ran fine with
   no issues to any questions (maybe the smallest of screen artifacts in
   the beginning)"*. Controller feel, picture/sound, BACK/RESUME, save/load
   through the TV: reported fine, the user's words, not a gate. The early
   artifacts: note they match the first-IDR resync after launch already
   characterized (`C3_L2A_E2`, `D_BASE_R3C`); no issue opened. D8's table:
   the pending rows now read "the user's rows: reported fine 2026-09-28".
   `docs/ROADMAP.md` D7: complete on the adopted build (9 scripted PASS,
   1 cited, hands-on reported).
2. **FEC** (`decisions/C4_ADAPTIVE_FEC_2026-09-24.md`, append): the user's
   call 2026-09-28: agreed, no adoption; `xor8_1` 8+1 stays; the 8+2 arm
   remains in the tree behind `PRIVYHUB_FEC_SCHEME`, dormant. C4 closed
   for Phase C on that decision.
3. **CL-B1 adoption** (the CL-B1 record, append): the user's call
   2026-09-28: bundle — the body-POST client change ships in whichever APK
   is next adopted (the C5 arm if it needs a client change, else the C3.L4
   live build). Until then the onn carries `f31b1c18…8ae7`.

## Record and memory

`evidence/C3_L3A_R4_SESSION4_2026-09-28.md` (session 4 as above, the
pooled table, the reading, pointer to the decision); evidence dir
`c3_l3a_r4_2026-09-28/` with copies of every input above (state, reports,
aggregate, decoder session, session and finalize logs, redacted journal),
manifest; the decision record; the three appends; `docs/ROADMAP.md` (C3
line: L3a complete, L4 authorized, live build pending; C4 closed; D7
complete); `docs/PROJECT_STATUS.md`; `CURRENT.md`; `investigations/ACTIVE.md`
(C3.L3a closed; C3.L4 live is the open item); the daily file
`docs/memory/2026-09-28.md`; `evidence/RUNTIME_VALIDATION.md` (session 4:
the R2B cap and the CL-B1 companion route on the adopted APK, runtime
validated again). Baseline commit is now `f01c3b2` — `CURRENT.md`'s
`baseline_commit` and the handoff's "nothing committed since" line say so.
No addresses. Nothing committed. `check_memory_health.py` healthy.
