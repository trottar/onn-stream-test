---
memory_schema: 1
as_of: 2026-09-25
status: C3-L4-S1 DONE — the shadow controller is built (companion/adaptive_bitrate.py, flag PRIVYHUB_ADAPTIVE_BITRATE_MODE default off, `shadow` only, no acting mode, no actuator import); 21/21 unit tests pass; flag-off leaves native-stream-status unchanged but for `adaptive_bitrate: {mode: off, acted: false}`; the night (H1 cold 20 min, H2 warm 20, H3 warm 60, H4 warm 20) was HEALTHY by the close-out rows in all four holds and the shadow was SILENT — 0 FALLBACK, 0 ROUTINE, 0 INCREASE over 3,598 evaluated reports, 0 TELEMETRY_STALE, acted false everywhere; flag unset at the end and confirmed absent from the manager and the companion's environ; C3.L4 stays BLOCKED for live use
---

# C3-L4-S1 — the shadow controller

Task: `handoffs/C3-L4-S1_SHADOW_CONTROLLER_TASK.md` (weekend queue item 4,
authorized by the user 2026-09-24). Design:
`architecture/ADAPTIVE_BITRATE.md` §"C3.L4 shadow controller — S1", written
before the code. Patch: `patches/C3-L4-S1_SHADOW_CONTROLLER.md`. Evidence:
`c3_l4_s1_2026-09-24/` (manifest `sha256_manifest.txt`).

## The answer to `C3-L2`, in one paragraph

`video_only_restart` is authorized for fallback and recovery. It is not
authorized for automatic adaptation during play. So the controller has two
trigger classes:

- **FALLBACK**: the stream is already failing by the close-out's own rows.
  It is the only class that could ever become an acting path.
- **ROUTINE**: pressure short of failure. It is logged only, on its own
  track, and never moves the controller's virtual level.

**ROUTINE acting is gated on the user's `C3.L3a` reading and is not built.**
A decrease is one transition (FALLBACK to the 5000 floor); an increase is
one rung after 90 clean reports.

## Constants and their sources

They are as pre-registered in the task: the architecture section's table.

- ladder 5000 / 5500 / 6000 / 7000;
- blackout 3 reports;
- hold-down 30 reports (same direction) / 60 reports (reversal);
- FALLBACK: fps < 50 on 5/5 and (queue ≥ 2 on ≥ 3/5 or gap > 250 on
  ≥ 2/5);
- ROUTINE: fps < 57 on ≥ 4/5 and queue ≥ 1 on ≥ 3/5;
- increase after 90 clean reports (fps ≥ 59, queue 0, gap ≤ 150);
- oscillation: the third direction change in 10 min;
- stale: 3 reports without a distinct snapshot.

## One interaction, found by the unit tests and recorded, not retuned

On any queue-driven failure onset, ROUTINE's 4-of-5 is met **one report
before** FALLBACK's 5-of-5. If ROUTINE moved the virtual level, its blackout
and hold-down would mask the FALLBACK that follows.

So ROUTINE is counted on its own track: once per 30 reports while its
evidence persists, and never moving the acting track. A real failure
therefore logs one ROUTINE line, then the FALLBACK. The test
`test_fallback_one_decrease_then_blackout_then_hold_down` states this.

## Unit tests — 21 / 21 OK

Run with `python3 -m unittest tools/test_adaptive_bitrate_shadow.py -v`
(output in `unit_tests.txt`). They ran before the companion was restarted
with the flag. Each test names its rule:

**The task's seven:**

- 1,000 clean reports draw no decision.
- A FALLBACK pattern draws exactly one FALLBACK would-decrease (7000 →
  5000); the blackout covers 3 reports; nothing more at the floor or in
  hold-down.
- A ROUTINE pattern draws one ROUTINE would-decrease (7000 → 6000, not
  FALLBACK).
- Recovery draws one would-increase after exactly 90 clean reports, and
  not at 89.
- An alternating pattern ends in an `oscillation` HOLD on the third
  reversal, for the rest of the session.
- Stale or unavailable telemetry reads `TELEMETRY_STALE`, with no decision.
- The settling signature (one report at 45 fps, and three at 48, then
  clean) draws no decision.

**And beside them:**

- transport gaps of 100-200 ms;
- FALLBACK by output gap;
- the 60-report reversal hold-down;
- ROUTINE once per 30 reports, never moving the level;
- one unclean report restarts the clean count;
- 3 non-distinct snapshots read stale;
- `waiting_for_idr` is never evidence;
- loss or FEC recovery alone is never evidence;
- a new session resets;
- the default is off;
- only `off` and `shadow` are accepted (any other value reads off,
  flagged);
- off writes nothing;
- shadow logs decisions, not reports, with `acted: false`;
- no actuator reference in the module.

**Flag off, at runtime.** After a restart through the unit, with no
`PRIVYHUB_*`, `native-stream-status` gained exactly one key: `adaptive_bitrate:
{schema, mode: off, acted: false}`. The profile is adopted
(`status_flag_off.json`).

## The night

Harness: `c3_l4_s1_night.sh` and `c3_l4_s1_run.sh`, derived from
`c3_l3a_s1_run.sh`.

- **The flag.** `PRIVYHUB_ADAPTIVE_BITRATE_MODE=shadow` was the only
  `PRIVYHUB_*` allowed, and it was required. Before each launch the run
  confirmed it in the manager and the companion's environ, and confirmed
  `adaptive_bitrate.mode = shadow` plus the adopted profile.
- **The holds.** Plain attract-mode holds with zero input, the PS1
  reference title, and `T2` at 10 s.
- **Cold gate.** H1 started 42 min after the last `session_ended`.

| hold | window (UTC) | spikes/min | fps | stale/min | video loss/min | audio underruns/min | max gap ms | onn °C (warm share) | health | reports evaluated | FALLBACK / ROUTINE / up | STALE |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | ---: |
| H1 cold, 20 min | 22:05-22:25 | 31.5 | 59.93 | 0.94 | 9.17 | 0.40 | 175 | 61.6-69.9 (58 %) | HEALTHY | 602 | **0 / 0 / 0** | 0 |
| H2 warm, 20 min | 22:26-22:46 | 24.4 | 59.91 | 0.84 | 8.80 | 0.75 | 123 | 67.4-70.0 (99 %) | HEALTHY | 600 | **0 / 0 / 0** | 0 |
| H3 warm, 60 min | 22:47-23:47 | 27.4 | 59.94 | 0.32 | 7.70 | 0.65 | 199 | 67.5-70.1 (100 %) | HEALTHY | 1,796 | **0 / 0 / 0** | 0 |
| H4 warm, 20 min | 23:48-00:08 | 29.2 | 59.91 | 0.70 | 8.99 | 0.60 | 153 | 68.0-70.1 (100 %) | HEALTHY | 600 | **0 / 0 / 0** | 0 |

The rows are scored as the close-out defines them, by `c3_l4_s1_analyze.py`
→ `c3_l4_s1_analysis.txt`. The max gap stayed within the verdict bound
(≤ 250) in every hold.

**Reading (pre-registered): SILENT.** All four holds were healthy. There
were 0 FALLBACK and 0 ROUTINE would-acts across all four, and 0
`TELEMETRY_STALE` entries. `acted` was false on every line and in every
status.

**What the shadow saw.** These figures come from the samples carried on
the 1,048 logged lines. They are not every report; only reports that
changed state or reason are logged.

- **fps.** It went below 57 on 183 logged samples, and below 50 on 7:
  - four were each session's first report, 0 fps at ~0.6 s elapsed (three
    of them with `waiting_for_idr`, ignored);
  - three were single reports at 42-50 fps mid-hold.
- **Queue depth.** At most 2, and ≥ 1 on 75 logged samples.
- **Output gap.** At most 76 ms on the logged samples; never over 150.
- **FALLBACK was never approached.** Its 5-of-5 needs five consecutive
  reports under 50.
- **ROUTINE was never met.** Its 4-of-5 under 57 together with queue ≥ 1
  on 3 of 5 never occurred.

**Teardown.** The night ended at 00:09:48Z.

- The flag was unset.
- The companion was restarted through its unit. The new MainPID owns
  8765, and `PRIVYHUB_*` reads 0 in both the manager and its environ.
- `adaptive_bitrate` reads `mode: off`.
- The profile is adopted (cap 90,000 profile, cushion 12/17, redundancy
  2/4, `any_override` false), at 7000 kbps.
- No game is active, and the launcher shows no NOW PLAYING banner.

## Findings to carry forward

1. **The decision log is chattier than intended.** It writes a line on
   every *reason* change inside a state as well as on a state change. As
   fps wanders 57-62, `REFERENCE/clean`, `REFERENCE/no_evidence` and
   `PRESSURE/pressure_sample` alternate. That came to 1,048 lines for
   3,598 reports (~29 %).
   - It is bounded by the rotation (~0.4 MB for the night).
   - It is not a defect of the policy, and it was not changed mid-night.
   - A follow-up: log state changes and decisions only.
2. **Session start.** The first client report of a session reads 0 fps.
   Once (H4) it came without `waiting_for_idr` and was evaluated as a
   pressure sample. A single report cannot trigger anything, but a live
   mode should treat the session's first reports like a blackout.
3. **The night was healthy and cool on the controller path.** Tonight's
   `CTRL-L1` holds, earlier on the same path, missed the video-loss row
   (14-24/min). These four did not (7.7-9.2).

## What a live mode would still need

- **The user's reading of the `C3.L3a` gate.** Session 4 is still to come.
  ROUTINE acting depends on that reading.
- **A fault-injection night**, so that FALLBACK and RECOVERY are exercised
  on a genuinely failing stream. That uses the user's `nft`, not Code's.
- **The two findings above.**
- **An actuator path with `ACTUATOR_FAILED` handling.** None exists in this
  build.

**`C3.L4` stays BLOCKED for live use.**

## Files (`c3_l4_s1_2026-09-24/`)

- **Code**: `adaptive_bitrate.py` and `test_adaptive_bitrate_shadow.py`
  (copies); `companion_patch.diff`; `pre_patch_sha256.txt` and
  `post_patch_sha256.txt`.
- **Validation**: `unit_tests.txt` and `status_flag_off.json`.
- **Night**: `c3_l4_s1_night.sh` and its log, `c3_l4_s1_run.sh`,
  `t2_sample.py`, and `t2_samples.jsonl` with the sampler log.
- **Shadow log**: `shadow_log.jsonl`, the night's slice of
  `logs/games/adaptive_bitrate_shadow.jsonl`.
- **Scoring**: `c3_l4_s1_analyze.py` and `c3_l4_s1_analysis.txt`.
- **`runs/`**: per hold, the `armcheck_*`, `status_end_*` (with the
  shadow's counters), `status_*`, `report_*`, `heartbeat_*`, `frames_*`
  and `alpha_*` files, the journal `companion_*.log`, `encoder_cmd_*` and
  `adb_during_hold_*` (36-113 foreign adb processes, the `T2` sampler's);
  plus `index.txt`.

`h2_prep_redact.py` was applied to every text file except the decoder-
report byte copies, and `--check` reports 0 residual matches. The report
copies carry the one known false positive, the core version string. No
address, MAC or device identifier remains in any file.
