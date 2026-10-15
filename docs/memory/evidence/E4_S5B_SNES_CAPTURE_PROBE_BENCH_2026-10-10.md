---
memory_schema: 1
as_of: 2026-10-10
baseline_commit: 7331184 (plus the uncommitted E4-S1..S5 work)
---

# E4-S5B — the SNES capture fix on bad probes (a bench)

**Classification: INCONCLUSIVE (the mechanism did not reproduce in arm
A), by the pre-registered reading.** Every other clause held. Not adopted
(nothing is); the flag is absent.

| clause (pre-registration §2-§4) | result |
| --- | --- |
| sampled enough (arm B ≥ 3 bad probes) | **holds**: 4 of 24 (59 ×1, 59.94 ×3); no extension needed |
| **the fix works in B** (every bad probe outputs 60, drops ≤ 2) | **holds**: 4 / 4 output 60, 0 drops |
| the mechanism reproduces in A (bad probe → output = tbr, drops ≈ (60 − tbr) × 60 ± 20 %) | **does not hold**: 1 bad probe in 24 (59.94); output 59.94 = tbr ✓, but **0 drops** against 3.6 ± 0.7 |
| the live session host-clean | **holds**: RetroArch 59.999; host 10.11 % − the bench's 1.52 % = 8.60 (7.4 ± 2) |
| PS1-STREAM with the flag (§4) | **PASS**: capture 59.991, dup+drop 0.10/min, RetroArch 59.999, host 12.11 % (10.9 ± 2) |

**Why A showed no drops — the bench's sink, found after the data** (a
diagnostic; it changes no verdict).

- The bench writes to `-f null`. With no output `-r`, ffmpeg's default
  frame-rate mode is pass-through for the null muxer, so frames are
  neither dropped nor duplicated whatever rate the stream declares.
- For the companion's rtp muxer the default is constant frame rate, and the
  surplus frames are dropped. That is E4-S5's mechanism.
- `vsync_check2.sh` shows this on a synthetic source that declares R while
  its frames arrive at 60/s (60 s, no window, no device, no network):

  | declared rate (= the probe) | `-f null`, default mode (the bench) | constant rate (the companion's rtp) | constant rate with `-r 60` (the fix) |
  | --- | --- | --- | --- |
  | 59 | 0 drops | **58 drops** | 0 drops |
  | 59.94 | 0 drops | **2 drops** | 0 drops |
  | 60 | 0 | 0 | 0 |

- **So the bench could show the output rate under a bad probe (B: 60;
  A: the probe's), but not the drops in either arm.** The reading rule's
  drop clauses assumed the companion's sink. B's "drops ≤ 2" therefore
  held vacuously.
- What B does show is still the fix's mechanism: under a 59 or 59.94 probe
  the encoder's output rate is 60. Constant-rate output at 60 does not
  drop (the table's last column).
- (`vsync_check.sh`, the first form, set an explicit `-r` in every case.
  That is the fix's case, and it forces constant-rate output into
  `-f null` too. It is kept as run.)

**The fault, live, beside the bench.** The companion's own stream (no
flag, rtp) made 11 encoder starts during the live session (live-ladder
restarts):

- 9 probed 60; 1 probed 59.94 (the first) and 1 probed 59;
- each output its probe;
- its capture over the 75-min window was **59.944 fps** with **2.25
  dup+drop/min**.

That is E4-S5's mechanism on the real sink. It was reported here, not
gated.

**Context:**

- Task: `handoffs/E4-S5B_SNES_CAPTURE_PROBE_BENCH_TASK.md`, under
  `QUEUE_2026-10-10B.md` (queue item 2).
- **Baseline: `7331184` plus the uncommitted E4-S1..S5 work**, untouched;
  E4-S3B's files and runner patch beside it.
- Files: `e4_s5b_2026-10-10/`.
- **Timeline (UTC, 10-10):**

  | time | what |
  | --- | --- |
  | **09:12:44** | **pre-registration hashed** (`0778fe12…a5f6`) |
  | 09:12-10:32 | the live SNES-STREAM (window 09:16:46 + 4500 s) |
  | 09:16-10:09 | the bench: a 5-s check, then 48 sessions A B A B … |
  | 10:32-10:56 | PS1-STREAM with the flag |
  | 10:56-10:57 | `vsync_check.sh`, `vsync_check2.sh` (after the runs) |

## 1. The bench

`e4_s5b_bench.py`:

- **How each command was built:**
  - It is the companion's own `_build_linux_ffmpeg_command`, on an instance
    holding only the adopted profile.
  - The flag was set (B) or unset (A) in the bench's environment at
    build time.
  - The built command was hashed with the window masked: one hash per
    arm. Only B carries `-r 60`.
- **The only change to the command** is the sink: `-payload_type 96 -f rtp
  <the local FEC relay port>` became `-t 60 -f null -`.
- **The window:** the live RetroArch window, its id read from the
  companion's encoder in `/proc` and never written.
- **The check session** (5 s, A) parsed (probe 60, 300 frames). Then came
  the 48 counted sessions: all rc 0, 3,600 frames each, about 60.15 s
  wall time each.

| arm | sessions | bad probes | tbr | output fps | drops at a 60 probe | dups |
| --- | --- | --- | --- | --- | --- | --- |
| A (no flag) | 24 | 1 (4 %) | 60 ×23, 59.94 ×1 | = tbr | 0 | 0 |
| B (flag) | 24 | **4 (17 %)** | 60 ×20, 59.94 ×3, 59 ×1 | **60 ×24** | 0 | 0 |

- **Bad-probe rate:**
  - tonight: 5 of 48 bench probes, plus 2 of the companion's 11 → 7 of 59
    (12 %);
  - E4-S5's 21 earlier SNES probes: 8 not 60.
- **The bench's own cost:**
  - each session took ~15.6 CPU-seconds (~26 % of a core) plus a VAAPI
    encode;
  - over the window that is 1.38 % of the host, plus Xorg's extra 0.14 %
    for the second x11grab.

## 2. The live session and the PS1 run

| run | RetroArch | host CPU | capture / dup+drop per min | rendered | loss/min | resyncs |
| --- | --- | --- | --- | --- | --- | --- |
| SNES-STREAM, live (no flag), 75 min | 59.999 | 10.11 (8.60 net of the bench) | 59.944 / 2.25 (the fault, live) | 58.34 | 539 | — |
| PS1-STREAM with the flag, 20 min | 59.999 | 12.11 | **59.991 / 0.10** | 59.85 | 39 | 0 |

- **PS1:** its encoder probed `1000k` → output 60, with `-r 60` in the
  command. The flag changes nothing for PS1, as expected.
- The link: rendered and loss were reported, not gated. The loss was 539 and
  39 per minute: the bad night continues, easing by 10:30.

## 3. What would settle it; the adoption line (not written)

- **Not ACCEPTED, so the adoption line is not written**, as the
  pre-registration says. It would have been:
  - a drop-in `snes-capture.conf` with
    `Environment=PRIVYHUB_SNES_CAPTURE_FIX=output_rate`;
  - its revert, deleting the drop-in.
- **A bench that can settle it** keeps the companion's sink semantics. Two
  ways:
  - `-fps_mode cfr` on the null sink, the mode the rtp muxer gets by
    default;
  - or an rtp sink to a local port nothing listens on.
  - That is one argument, so the command would no longer be the companion's
    byte for byte.
- On tonight's rates, 24 sessions per arm would give about four bad probes
  per arm.
- The live-companion evidence above, and the synthetic table, already
  point the same way as E4-S5: a bad probe drops on rtp, and `-r 60`
  removes the drops. The user decides whether that is enough.

## 4. State at the end; files

- **Final state** (`state_at_end.json`, 10:57Z):
  - the four adopted lines; no `e3_flag.conf`, no `e4_constraint.conf`;
  - no game; the PS1 files identical; **APK CONFIRMED**.
- The flag was in `e3_flag.conf` for the PS1 run only (removed at its
  teardown, `flags_absent` true), and in the bench process's environment
  at build time only.
- No sudo, no nft, the Opal untouched; nothing fetched; no data deleted.
  The window id was never written. E4-S5's sidecar was not used.
- **Files** (`e4_s5b_2026-10-10/`):
  - `precondition.json`, `git_status_at_start.txt`,
    `tools_at_preregistration_sha256.txt`;
  - the pre-registration + `.sha256` + `preregistration_hashed_at.txt`
    (`.prereg_draft_used` is its unfilled draft);
  - `e4_s5b_bench.py`, `e4_s5b_run.py`, the console logs, `bench/bench.jsonl` (with `bench/manifest.sha256` + `check.txt` OK, added 2026-10-10 15:25Z by queue C: the file had been in no manifest; `5594e66f…`);
  - `runs_bench/` and `runs_ps1/` (each with `manifest.sha256` and
    `check.txt` OK);
  - `e4_s5b_analysis.py`, `analysis_console.txt`, `e4_s5b_table.md`,
    `e4_s5b_verdict.json`, `validity.json`;
  - `vsync_check.sh` / `.txt`, `vsync_check2.sh` / `.txt`;
  - `state_at_end.json`, `redact_check.txt`.
- No tool changed: no patch record.
- Git status (cumulative): `logs/e4_s5b_git_status.txt`.
