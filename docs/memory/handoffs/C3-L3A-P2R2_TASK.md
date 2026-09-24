---
memory_schema: 1
as_of: 2026-09-24
status: TASK HANDOFF — C3.L3a Part 2, revision 2: record the 2026-09-24 smoke session (the first run of the fixed probe on the adopted build — settling measured, transition cost measured, picture judged), fix one report defect it exposed (Phase B rows anchored on fire + offset instead of the matched SSRC change), keep the smoke out of the pooled runs; tools + documentation only, no companion / client / profile change, no session run; authorized by the user 2026-09-24
---

# C3-L3A-P2R2 — the smoke session, recorded; one report defect fixed

**Why.** The user ran the fixed probe once on the adopted build as a smoke
session (`--traversals 2 --dwell-min 40 --dwell-max 50`, with Phase B) and
finalized it. Run `20260924_000330`, state schema v2, decoder session
`logs/games/decoder_sessions/native_decoder_20260924_041256_754.json`
(received 04:12:56Z, 479.0 s, client profiler 0.12.3, 8 SSRC changes).
Outputs: `logs/streaming/c3_l3a_runs/20260924_000330.{json,txt}`, the run
log `logs/streaming/c3_l3a_smoke_20260924_000330.log`, the finalize log
`logs/streaming/c3_l3a_smoke_finalize.log`, and the state file
`logs/streaming/c3_l3a_gameplay_acceptance_state.json` (now this run's;
the 2026-09-20 state survives only as the byte copy in
`evidence/c3_l3a_p2r1_2026-09-23/`). `logs/` is gitignored, so nothing of
this survives unless it is recorded. Record it. Cowork verified the
finalize against the raw state and decoder files; the numbers below are
confirmed unless marked otherwise.

Read first: `evidence/C3_L3A_P2R1_PROBE_DEFECTS_AND_RESCORE_2026-09-23.md`
(its rerun pre-registration), the run's text report, `CURRENT.md`.

**Scope.** Change only `tools/probe_c3_l3a_gameplay_acceptance.py` (one
fix, below). No companion, client, profile or route change; nothing in the
environment; do not start a stream or session; do not restart the companion.
Copy the state file, decoder session, run outputs and both logs into the
evidence directory byte for byte; never modify them.

## The fix — Phase B rows anchor on the wrong point

The per-transition decoder view anchors each transition's 1 s window on
the matched `ssrc_change` for Phase A but, for a v2 state, on
`fired_at_s + offset` for the parks and the restore. The 6000 park's SSRC
change came **0.227 s before** that point, so its row prints **72 ms**
where the largest gap inside `[ssrc, ssrc + 1 s]` is **211 ms** (at
ssrc + 41 ms; it is the session's `max_output_gap_ms`), and the 5500 park
prints "–" where the true value is **166 ms**. Anchor every row —
Phase A, parks, restore — on the matched `ssrc_change` (the fire time is
reported beside it with its residual, as now), and say so in the report
text. Re-run `--finalize --state <the smoke state> --decoder <the file
above>` after the fix and confirm the eight rows read **125 / 198 / 154 /
187 / 211 / 166 / 203 / 189 ms**, every one with `codec_ms` ≤ 12. Also
re-run it on the 2026-09-20 copy in `evidence/c3_l3a_p2r1_2026-09-23/`
and confirm that record's per-transition table is unchanged (its Phase B
windows already started at the SSRC change).

## Keep the smoke out of the pool

The pre-registration is 10 traversals at dwell 55-90 s, pooled. The smoke
ran 2 traversals at 40-50 s. Move `c3_l3a_runs/20260924_000330.{json,txt}`
(regenerated after the fix) into the evidence directory and out of
`logs/streaming/c3_l3a_runs/`, so `--aggregate` pools only pre-registered
sessions; leave the 2026-09-20 files where the P2R1 task left them
(`--aggregate` already skips pre-v2 runs by name — confirm it still does
and that after the move it reports 0 poolable runs, or say what it does).

## What the smoke measured — write it down as a result

- **Telemetry settling, measured for the first time**: 2 of 2 sequences,
  **2.006 s and 1.504 s**, two distinct snapshots at a 2,007 ms cadence
  (`sample_interval_ms` 2000; budget 6 intervals). The first fresh report
  after a transition already reads 59.85 fps at the new bitrate,
  `waiting_for_idr` false, queue depth 0, output gap ≤ 21 ms. Resolution is
  one client interval, so state it as "settled within one to two client
  reports (≤ ~4 s)", not as a sub-second number.
- **Transition cost on the adopted build**: every one of the 8 SSRC changes
  aligned with a fire (Phase A offset 13.842 s, spread 0.152 s, max
  residual 0.122 s); `jump_packets` 0 on all 8; first IDR 1-35 ms; largest
  output gap in the second after each 125-211 ms (the eight values above)
  with `codec_ms` 7-12. On 2026-09-20 the same gap was 160-240 ms with
  190-260 ms of codec hold; now it is the restart's own RTP silence
  (`rtp_silence_after_spawn_ms` 152-153 on all four Phase-A cycles, spawn
  266-416 ms, first RTP resume 419-569 ms, host verified 1,172-1,323 ms).
  That silence is the floor of `video_only_restart` — say so, as a fact
  about the actuator, not a claim about perception.
- **Marks: 0** in 103.5 s of Phase A (1 jump, 1 ramp, 2 decoys). At n = 1
  per shape this is one observation, not a rate; do not compute a detection
  rate from it. Decoy slack 6.2 s at W 8 — the new placement rule held.
- **Picture, announced (Phase B)**: 6000 / 5500 / 5000 all **acceptable,
  rated 9 / 9 / 9** on the anchored 1-10 scale. Beside it the 2026-09-20
  answers on the unhealthy pre-cap stream (no / no / no, 5 / 3 / 2 of 10):
  the rungs were never the problem; the stream was. Record that the 5000-7000
  ladder stands for the rerun.
- **Lifecycle**: 0 FEC / 0 audio / 0 controller deltas over 4 transitions;
  audio underruns 9 for the session, audio lost 0, prolonged starvation 2.
- **Close-out rows for the session, context not a gate**: 7.98 min with 8
  deliberate restarts — spikes 40.46/min, rendered fps 59.77, stale drops
  2.38/min, video loss post-FEC 1.38/min (11 lost, 10 FEC-recovered, 2
  unrecoverable groups), max output gap 211 ms (a transition). Beside the
  close-out's 32.8 / 26.0, 59.90 / 59.91, 1.14 / 0.80, 8.67 / 8.40, 163 /
  110. Every numeric-target row inside its target; the baseline stays met.
- **The user's words, recorded verbatim as stated 2026-09-24, not a gate**:
  they did not even notice anything happening; it played incredibly; visual
  quality was maybe a little lower sometimes but they could not tell at 720p
  playing these older games; the title was The Emperor's New Groove (PS1),
  which often had performance issues.
- **What went wrong operationally**: the first "finalize" attempt was the
  run command typed again; the probe's preflight refused it (stream not
  active, telemetry not fresh) and wrote nothing — the preflight worked as
  intended. The real finalize ran 6 minutes later and auto-selected the
  decoder session (earliest of 1 candidate with `ssrc_changes` ≥ 8).

## What it does not establish

Nothing about the gate: one jump, one ramp, zero marks is not a detection
rate, and the pre-registered reading needs ≥ 20 per shape pooled. Nothing
about behaviour under real network pressure — every transition fired from
a schedule. Say both.

## Record and memory

`evidence/C3_L3A_P2R2_SMOKE_SESSION_2026-09-24.md` with the sections above,
the corrected per-transition table, and the state of the rerun
pre-registration (unchanged: 10 traversals, dwell 55-90, W 5.0 primary,
≥ 4 sessions to ≥ 20 per shape — the user runs them; nothing runs without
them). Evidence under `evidence/c3_l3a_p2r2_2026-09-24/`: byte copies of
the state file, the decoder session, both logs, the as-finalized run
outputs (before the fix, from `c3_l3a_runs/`) and the regenerated ones
after it, `sha256sum` manifest of every file. `patches/C3-L3A-P2R2_*.md`
with per-file SHA-256 before and after; regenerate `patches/PATCH_INDEX.md`.
Update `investigations/ACTIVE.md` §C3.L3a (settling and transition cost
now measured; ladder stands), `CURRENT.md` (Current Work Item stays the
rerun, awaiting the user; add the smoke's two measured numbers to Verified
State in one line; `python3 tools/check_memory_health.py` healthy),
`2026-09-24.md` (new daily file), `handoffs/CURRENT_HANDOFF.md` one line,
`evidence/RUNTIME_VALIDATION.md` (the probe's settling and alignment paths
are now RUNTIME VALIDATED on one session). `C3.L4` stays BLOCKED on the
gate. No addresses or device identifiers in any file. Nothing committed.
