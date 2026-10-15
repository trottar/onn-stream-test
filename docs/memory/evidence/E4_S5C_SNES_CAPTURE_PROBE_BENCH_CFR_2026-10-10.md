---
memory_schema: 1
as_of: 2026-10-10 (runs); record written 2026-10-15
baseline_commit: 7331184 (plus the uncommitted E4-S1..S5B work)
---

# E4-S5C — the SNES capture fix on bad probes, the bench with the right sink

**Classification: INCONCLUSIVE (the mechanism did not reproduce in arm A
by its pre-registered drop window).** The fix clause held. Not adopted
(nothing is); the flag is absent.

| clause (pre-registration §2-§3) | result |
| --- | --- |
| sampled enough (each arm ≥ 3 bad probes) | **holds**: A 5 of 24, B 4 of 24; no extension |
| **the fix works in B** (every bad probe outputs 60, drops ≤ 2) | **holds**: 4 / 4 output 60, **0 drops** (59 ×2, 59.94 ×2) |
| the mechanism reproduces in A (output = tbr, drops ≈ (60 − tbr) × 60 ± 20 %) | **does not hold**: 5 / 5 output = tbr; 59 → **58** drops (window 48-72 ✓); 59.94 → **2** drops ×4 (window 2.88-4.32 ✗) |
| the live session host-clean | **holds**: RetroArch 59.999; host 10.44 % − the bench's 1.54 % = 8.90 (7.4 ± 2) |

**What the 59.94 cases show.** Each one output 3,597 frames from a
60-s, 60-frame/s source, 3 short of the 3,600 that B and every good probe
produced. ffmpeg's drop counter read 2. E4-S5B's synthetic check
(`vsync_check2.sh`) read the same 2 at 59.94. So the frames are lost as
E4-S5 described, but ffmpeg's counter reads one less than the task's
(60 − tbr) × 60 formula. The window was pre-registered and was not
changed after the data. That makes the verdict INCONCLUSIVE, not ACCEPTED.

**So the bench now shows, with the companion's sink mode:**
- a bad probe drops: 58 at 59, 2-3 at 59.94;
- the flag's `-r 60` removes the drops: 0 at every bad probe;
- good probes drop nothing in either arm.

Whether that is enough to adopt is the user's decision.

**Context:**

- Task: `handoffs/E4-S5C_SNES_CAPTURE_PROBE_BENCH_CFR_TASK.md`, under
  `QUEUE_2026-10-10C.md` (queue item 1).
- Baseline: `7331184` plus the uncommitted E4-S1..S5B work, untouched.
- **Timeline (UTC, 10-10):** pre-registration hashed **15:27:14**
  (`63fafc8a…6c43`); live SNES-STREAM 15:27-16:46 (window 15:31:22 +
  4500 s); bench 15:31-16:23 (a 5-s check, then 48 sessions A B A B …).
- **The record was written on 10-15, five days late.** The session
  stalled after the runs ended and did not resume. Nothing ran in
  between. Queue item 2 (E4-S4C, the link watch) **never started**: its
  pre-registration was never hashed and no probe ran.

## 1. The bench

- `e4_s5c_bench.py` = E4-S5B's bench with one change, the sink:
  `-fps_mode cfr -t 60 -f null -`. `e4_s5c_bench_vs_e4_s5b.diff` shows
  the sink line, the docstring and the usage line.
- ffmpeg is 7.1.5, so `-fps_mode` was used, not `-vsync cfr`.
- The command was otherwise the companion's own builder; one masked hash
  per arm. Only B carries `-r 60`.
- The check session parsed (probe 60, 300 frames). All 48 sessions had
  rc 0. Every good probe gave 3,600 frames with 0 drops and 0 dups.

`e4_s5c_table.md` holds the per-session table; `e4_s5c_verdict.json`
holds the full reading.

## 2. The live session (no flag)

| RetroArch | host CPU | bench cost (ffmpeg + Xorg extra) | host − bench | companion capture / dup+drop per min | rendered | loss/min |
| --- | --- | --- | --- | --- | --- | --- |
| 59.999 | 10.44 | 1.54 (1.39 + 0.15) | 8.90 | 59.97 / 1.67 | 58.91 | 340 |

- The companion's own encoder started 6 times; 2 of the starts probed
  59.94 and output 59.94 (the fault, live).
- The link was reported, not gated: 340 loss/min.

## 3. The adoption line (not written as ACCEPTED)

The verdict is not ACCEPTED, so per the pre-registration this is not
written as an adoption. For the user's decision, it would be:

- the drop-in `~/.config/systemd/user/privyhub-companion.service.d/snes-capture.conf`
  containing `[Service]` / `Environment=PRIVYHUB_SNES_CAPTURE_FIX=output_rate`;
- then `daemon-reload` + restart;
- the state checks' adopted list gains the fifth line.

**Revert:** delete the drop-in, `daemon-reload`, restart.

## 4. State; files

- **Final state** (`state_at_end.json`): the four adopted lines; no
  `e3_flag.conf`, no `e4_constraint.conf`; no game; the PS1 files
  identical; APK CONFIRMED. The live run's teardown read `flags_absent`
  true.
- The flag was only in the bench process's environment, at build time.
- No sudo, no nft, the Opal untouched; nothing fetched or deleted; the
  window id was never written.
- **Files** (`e4_s5c_2026-10-10/`):
  - `precondition.json`, `git_status_at_start.txt`,
    `tools_at_preregistration_sha256.txt`;
  - the pre-registration + `.sha256` + `preregistration_hashed_at.txt`;
  - `e4_s5c_bench.py` + diff, `e4_s5c_run.py`, `e4_s5c_analysis.py`;
  - `bench/bench.jsonl` with `manifest.sha256` + `check.txt` OK;
  - `runs_bench/` with `manifest.sha256` + `check.txt` OK;
  - `e4_s5c_table.md`, `e4_s5c_verdict.json`, `validity.json`, the
    console logs, `state_at_end.json`, `redact_check.txt`.
- No tool changed: no patch record.
- Git status (cumulative): `logs/e4_s5c_git_status.txt`.
