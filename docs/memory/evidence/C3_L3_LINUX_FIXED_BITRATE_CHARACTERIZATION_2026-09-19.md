# C3.L3: Linux Fixed-Bitrate Characterization — First Runtime Run

Date: 2026-09-19
Prerequisite: `patches/C3-L3_LINUX_FIXED_BITRATE_PORT.md` (installed same day).

**Correction notice (2026-09-19, `C3-L3R1`).** The "Third run" section below
originally declared the 6000 kbps result invalid and asked for a rerun. The
rerun had in fact already been taken before that text was written, and its
result was sitting in `logs/streaming/c3_fixed_6000_characterization.json`.
The section is corrected in place and the corrected three-run reading is at
the end of this file. The run-3 first-attempt matching bug was real; the
decoder-session file it was blamed on was misidentified. Record:
`patches/C3-L3R1_CHARACTERIZATION_CORRECTION.md`.

## What this run answers

Whether the ported Linux fixed-bitrate cycle works at all: trigger, RTP
resume, telemetry sampling, and finalize against real decoder-session
evidence, at each of 5000/5500/6000 kbps.

It does **not** yet answer the bitrate-vs-quality envelope question C3.L3
exists to establish — see "Confound" below.

## Cycle-level result (all three bitrates)

Every trigger returned `*_RUNTIME_SAMPLE_CAPTURED` and every finalize
returned `*_EVIDENCE_CAPTURED_WITH_FINDINGS`. At each bitrate:

- `post_status_bitrate_kbps` matched the target exactly; `post_status_reference_bitrate_kbps` stayed 7000.
- `cycle_fec_send_errors_delta`, `cycle_audio_send_errors_delta`,
  `cycle_controller_bad_packets_delta`: **0 at all three bitrates.**
- `waiting_for_idr` returned to `False` in the post-cycle telemetry window at
  all three.

The restart mechanism itself — the actual C3.L3 deliverable — is
**COMPLETE / RUNTIME VALIDATED**.

| | 5000 kbps | 5500 kbps | 6000 kbps |
|---|---|---|---|
| `host_first_rtp_resume_ms` | 519.4 | 667.1 | 517.5 |
| `receiver_recent_mbps` (min/median/max) | 2.73 / 5.27 / 5.89 | 5.30 / 6.59 / 8.94 | 4.98 / 5.89 / 7.78 |
| `receiver_recent_fps` (min/median/max) | 41.8 / 59.8 / 75.5 | 57.9 / 59.9 / 79.8 | 57.8 / 59.8 / 75.8 |
| `output_gap_ms` (min/median/max, post-cycle sampling window) | 3 / 13 / 26 | 3 / 14.5 / 23 | 2 / 7 / 24 |

## Whole-session decoder/audio evidence (finalize)

| | 5000 kbps | 5500 kbps | 6000 kbps |
|---|---|---|---|
| `session_duration_ms` | 57,181 | 22,510 | 21,088 |
| `sequence_resyncs` | 3 | 1 | 2 |
| `ssrc_changes` | 1 | 1 | 1 |
| `lost_packets` | 176 | 13 | 12 |
| `fec_recovered_packets` | 0 | 1 | 0 |
| `fec_unrecoverable_groups` | 0 | 0 | 1 |
| `decoder_rendered_frames` | 3,129 | 1,251 | 1,167 |
| `decoder_dropped_frames` | 25 | 9 | 8 |
| `decoder_queue_overflow_drops` | 25 | 9 | 8 |
| `decoder_max_output_gap_ms` | 367 | 219 | 331 |
| `decoder_max_rx_to_decode_ms` | 376 | 228 | 340 |
| `audio_underruns` | 138 | 134 | 113 |

Normalized to a common 10-second window (raw count ÷ duration_s × 10), to
separate a genuine bitrate effect from the fact that the three sessions ran
very different lengths:

| per 10s | 5000 kbps | 5500 kbps | 6000 kbps |
|---|---|---|---|
| `sequence_resyncs` | 0.52 | 0.44 | 0.95 |
| `lost_packets` | 30.8 | 5.8 | 5.7 |
| `decoder_dropped_frames` | 4.4 | 4.0 | 3.8 |
| `decoder_queue_overflow_drops` | 4.4 | 4.0 | 3.8 |

## Confound

The three sessions were not matched in duration: 57.2s at 5000 kbps versus
22.5s and 21.1s at 5500 and 6000. `decoder_max_output_gap_ms` (367 / 219 /
331) and raw resync/loss counts are **not a fair bitrate comparison** as
captured — a longer session has more opportunity to accumulate resyncs,
drops, and a worst-case gap regardless of bitrate.

Normalizing per 10 seconds narrows but does not remove the picture:
`decoder_dropped_frames` and `decoder_queue_overflow_drops` per 10s are
close across all three (~3.8-4.4), suggesting the frame-drop rate may be
close to bitrate-independent in this data — but `lost_packets` per 10s is
5-6x higher at 5000 kbps than at 5500/6000 (30.8 vs 5.8/5.7), which runs
opposite the naive expectation that a lower bitrate stresses the network
less. This is reported as a raw, unexplained observation, not a conclusion:
it could be a genuine bitrate/GOP-refresh interaction, a session-specific
network event unrelated to bitrate, or an artifact of the small sample
count. It has not been investigated further.

## What this does and does not establish

Established: the Linux fixed-bitrate cycle works end to end at all three
characterization bitrates with zero cycle-level (FEC/audio/controller)
errors, matching the standard this project already requires of the
`C3.L1`/`C3.L1R1` mechanism it is built on.

Not established: which of 5000/5500/6000 kbps has the better operating
envelope. That requires a rerun with matched, controlled session durations
per bitrate.

## Raw data

Full trigger and finalize output (JSON) for each bitrate, as written by the
probe scripts themselves:

- `logs/streaming/c3_fixed_5000_characterization.json`
- `logs/streaming/c3_fixed_5500_characterization.json`
- `logs/streaming/c3_fixed_6000_characterization.json`

(Each path holds only the most recent run's result — the path is fixed, not
timestamped. This evidence file is the durable record of this specific run;
a future rerun will overwrite those JSON files.)


---

## Second run — matched durations (same day)

Rerun with deliberately matched, longer play windows per bitrate, to reduce
the duration confound above: 71.3s / 67.4s / 77.2s at 5000/5500/6000 (within
~15% of each other, versus up to 2.7x apart in run 1).

Cycle-level result: identical pattern to run 1 — all three triggered and
finalized cleanly, zero `cycle_fec_send_errors_delta` /
`cycle_audio_send_errors_delta` / `cycle_controller_bad_packets_delta` at any
bitrate.

| | 5000 kbps | 5500 kbps | 6000 kbps |
|---|---|---|---|
| `session_duration_ms` | 71,257 | 67,360 | 77,162 |
| `sequence_resyncs` | 1 | 1 | 1 |
| `ssrc_changes` | 1 | 0 | 1 |
| `packets_dropped_waiting_for_idr` | 0 | 52 | 0 |
| `resync_to_idr_ms` | 40 | **417** | 59 |
| `lost_packets` | 94 | **425** | 2 |
| `fec_recovered_packets` | 6 | 8 | 5 |
| `fec_unrecoverable_groups` | 1 | 2 | 1 |
| `decoder_rendered_frames` | 4,025 | 3,687 | 4,359 |
| `decoder_dropped_frames` | 33 | 36 | 18 |
| `decoder_queue_overflow_drops` | 33 | 36 | 18 |
| `decoder_max_output_gap_ms` | 292 | **584** | 291 |
| `decoder_max_rx_to_decode_ms` | 303 | 594 | 306 |
| `audio_underruns` | 117 | 95 | 129 |

### Run 1 vs. run 2, side by side

| `decoder_max_output_gap_ms` | run 1 (uncontrolled) | run 2 (matched) |
|---|---|---|
| 5000 kbps | 367 | 292 |
| 5500 kbps | 219 | **584** |
| 6000 kbps | 331 | 291 |

5000 and 6000 kbps landed in the same rough band in both runs (292-367 ms
and 291-331 ms respectively). 5500 kbps **inverted**: best of the three in
run 1, worst by a wide margin in run 2. The run-2 5500 kbps session had one
materially different event the other five bitrate/run combinations did not:
a 417 ms resync-to-IDR recovery with 52 packets dropped waiting for IDR
(versus 40-59 ms and 0 packets at every other bitrate/run), and
`lost_packets` more than 4x any other session in that run (425, against 94
at 5000 kbps and 2 at 6000 kbps).

### Reading

At n=2 samples per bitrate, this is evidence of **high run-to-run variance,
not yet a demonstrated bitrate effect**. The two most likely explanations —
not distinguished by this data:

1. 5500 kbps has a genuine, reproducible weakness (an encoder/GOP-refresh
   interaction, a marginal point in the VAAPI rate-control curve, or similar)
   that happened to also look fine in run 1 by chance.
2. Run 2's 5500 kbps session hit an episodic event (a single costly resync,
   possibly network- or scheduling-related, unrelated to the bitrate itself)
   that dominates that session's whole-session totals; 5000 and 6000 simply
   didn't have a comparable event in either run.

Explanation 2 is favored by how concentrated the damage is: nearly all of
5500 kbps run 2's bad numbers trace to that one resync event, and the
post-cycle sampling window right after the trigger (which predates any
mid-session resync) looked unremarkable at 5500 kbps in both runs. But this
is not established — it needs at least one more matched-duration run per
bitrate to tell episodic noise apart from a real characteristic.

### Updated raw data

- `logs/streaming/c3_fixed_5000_characterization.json`
- `logs/streaming/c3_fixed_5500_characterization.json`
- `logs/streaming/c3_fixed_6000_characterization.json`

(Same fixed paths as run 1 — each now holds run 2's result, overwriting
run 1's. The tables above are this file's durable record of both runs.)

---

## Third run — matched durations

Same matched-duration protocol as run 2: 72.5s / 66.6s at 5000/5500, and
64.8s at 6000 after one discarded first attempt (below). Cycle-level result
unchanged: every trigger and finalize succeeded, zero cycle-level
FEC/audio/controller errors.

### The 6000 kbps first attempt was discarded

The first `tools/probe_c3_fixed_6000_characterization.py --finalize` of this
run, executed immediately after the 5500 kbps finalize, returned
measurements byte-identical to the 5500 kbps result — `session_duration_ms`
(66,638), every decoder and controller count, `sequence_resyncs`,
`ssrc_changes` — apart from `target_bitrate_kbps` itself, with several audio
fields present in the 5500 result missing from it. It matched the 5500
kbps run's decoder-session file
(`logs/games/decoder_sessions/native_decoder_20260919_055703_163.json`,
duration 66,638 ms, `decoder_max_output_gap_ms` 335 — the 5500 kbps
numbers exactly). That attempt was discarded. The defect is logged in
`docs/KNOWN_ISSUES.md` as `PRIVYHUB_C3_L3_FINALIZE_MATCH_BUG`; it is a
probe-script matching defect, not a C3.L3 port defect — the companion-side
Linux cycle in `companion/diagnostics/c3_linux_actuator_probe.py` is not
implicated.

**Correction.** The original text of this section named
`native_decoder_20260919_055703_163.json` as "a fresh decoder-session file
consistent with a real, separate 6000 kbps play session ... written 18.8s
before the 6000 finalize ran". That was wrong on both counts. It is the
5500 kbps session, and it was written 391 s — not 18.8 s — before the
6000 kbps finalize. It is the file the buggy attempt wrongly picked up, not
the file it should have picked up.

### The 6000 kbps rerun is valid and is used below

The rerun was taken the same session and matched the correct
decoder-session file. `logs/streaming/c3_fixed_6000_characterization.json`
records `payload.decoder_session_log =
logs/games/decoder_sessions/native_decoder_20260919_060325_369.json`, a
distinct session of 64,840 ms written 9.4 s before that finalize, whose
figures are unlike the 5500 kbps session's in every field. The finalize
matching worked on this attempt.

| | 5000 kbps | 5500 kbps | 6000 kbps (rerun) |
|---|---|---|---|
| `session_duration_ms` | 72,503 | 66,638 | 64,840 |
| `sequence_resyncs` | 1 | 2 | 1 |
| `ssrc_changes` | 1 | 1 | 1 |
| `packets_dropped_waiting_for_idr` | 0 | 130 | 0 |
| `resync_to_idr_ms` | 16 | 20 | 26 |
| `lost_packets` | 25 | 40 | 26 |
| `fec_recovered_packets` | 9 | 9 | 2 |
| `fec_unrecoverable_groups` | 2 | 0 | 0 |
| `decoder_rendered_frames` | 4,115 | 3,724 | 3,651 |
| `decoder_dropped_frames` | 22 | 37 | 19 |
| `decoder_queue_overflow_drops` | 22 | 37 | 19 |
| `decoder_max_output_gap_ms` | 242 | 335 | 307 |
| `decoder_max_rx_to_decode_ms` | 264 | 346 | 316 |
| `audio_underruns` | 114 | 101 | 122 |

### All three runs, `decoder_max_output_gap_ms`

| | run 1 (uncontrolled) | run 2 (matched) | run 3 (matched) | band |
|---|---|---|---|---|
| 5000 kbps | 367 | 292 | 242 | 242-367 (125) |
| 5500 kbps | 219 | **584** | 335 | 219-584 (365) |
| 6000 kbps | 331 | 291 | 307 | **291-331 (40)** |

Three valid points at every bitrate. 6000 kbps has the narrowest spread by
a factor of three against 5000 kbps and nine against 5500 kbps, and never
produced a session worse than 331 ms. 5000 kbps trends downward run over
run but across a 125 ms band. 5500 kbps has the widest spread and the only
session worse than 400 ms recorded at any bitrate in any run.

### Reading after three runs

**6000 kbps is the most consistent of the three**, not 5000 kbps. That is
the opposite of what this file said before the rerun was read, because the
rerun was omitted and 6000 kbps was being judged on two points instead of
three.

- 6000 kbps: 291 / 331 / 307 ms. A 40 ms spread across three sessions of
  21.1s, 77.2s and 64.8s — that is, the spread survived a 3.7x range in
  session duration. No session over 331 ms. Lowest `decoder_dropped_frames`
  in runs 2 and 3 (18 and 19, against 33/22 at 5000 and 36/37 at 5500).
- 5000 kbps: 367 / 292 / 242 ms. Monotone improvement across runs, which is
  as consistent with the sessions getting luckier as with a bitrate effect.
  Band 125 ms.
- 5500 kbps: 219 / 584 / 335 ms. Produced both the single best and the
  single worst result in the whole data set. The 584 ms session is
  attributable to one 417 ms resync-to-IDR event, so 5500 kbps is not
  demonstrated to be *intrinsically* worse — but it is the only bitrate
  that has produced a session-destroying event in three tries.

At n=3 per bitrate this is a ranking, not a proof. It is enough to say that
6000 kbps has not been shown to cost anything against 5000 kbps on
worst-case stall, and has been the steadier of the two in this environment
— which is the direction that matters, since 6000 kbps is closer to the
validated 7000 kbps reference profile and a fallback ladder that does not
have to descend as far is the cheaper ladder.

Not established, and out of scope for this item: perceptual quality at each
bitrate. Every number here is transport and decoder timing. A focused
gameplay observation is still required before any bitrate is accepted as a
fallback level, and that observation is the `C3.L4` gate, unchanged by this
data.

### Run 3 raw data

- `logs/streaming/c3_fixed_5000_characterization.json`
- `logs/streaming/c3_fixed_5500_characterization.json`
- `logs/streaming/c3_fixed_6000_characterization.json` (rerun; the
  discarded first attempt was overwritten by it and does not survive on
  disk — its description above is the only record of it)
- `logs/games/decoder_sessions/native_decoder_20260919_060325_369.json` —
  the 6000 kbps rerun's decoder session.

## Privacy

No network addresses appear in this record.
