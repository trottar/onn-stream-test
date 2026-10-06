---
memory_schema: 1
as_of: 2026-10-06
baseline_commit: d9fdbdd
---

# E3-S1 — the EPG grab's start-up vs the live stream: the grabber at the lowest priority

**Classification:**

- **INCONCLUSIVE by the pre-registered bar.** The same-night control
  fell outside E1's band of E2's PS1-STREAM by 0.012 fps, which is the
  bar's comparability clause (e).
- **Independently, the hypothesis is not supported.** With the flag,
  E1-CONC's loss, rendered fps and resyncs miss (a)-(c) by one to two
  orders of magnitude. Each grab's loss peak is still there, at the same
  offset, although the busiest core's peak fell by half.
- One change behind `PRIVYHUB_EPG_GRAB_PRIORITY=idle`. **NOT ADOPTED;
  nothing committed.** The flag is absent at the end; E2's final state
  is restored.

**Context:**

- Task: `handoffs/E3-S1_EPG_GRAB_PRIORITY_TASK.md`, queue item 1 of
  `handoffs/QUEUE_2026-10-06.md`.
- **Baseline commit: `d9fdbdd`**, the user's E2-S1 commit.
- Files: `e3_s1_2026-10-06/`.
- Timeline (UTC, 2026-10-06):

  | time | what |
  | --- | --- |
  | 03:13 | preconditions: E2's final state held (manager none; environ exactly `…MODE=live`; no game; PS1 files identical; APK `de072762…835e` CONFIRMED; no flags) |
  | 03:16 | the probe (stream idle) |
  | 03:17 | the change; a flag smoke (not data); the drop-in removed |
  | **03:18:38** | **pre-registration hashed** (`40706bbf…b4c1`). Its first line says "~03:35Z", an estimate written before hashing; the hash time is the true one. |
  | 03:18:46-04:54:54 | the four runs, in the pre-registered order; every run OK on its first attempt |

## 1. The probe (`e3_s1_2026-10-06/probe.md`)

- **The chain is five processes, not two:** the companion runs
  `npm run grab --`, which runs `sh -c`, then `node … tsx grab.ts`, then
  `node --require preflight.cjs …` (the grabber).
- **One forced refresh can spawn that chain up to three times**, once
  per source attempt. The probe's channel ran it twice: its first site
  returned 0 programmes.
- **~97 % of the first 3 s of CPU is the node grabber** (3.1-3.5 CPU-s
  per attempt, ~600 MB peak RSS). Most of it is spent before its first
  TCP socket: 3.29 of 3.53 CPU-s.
- As spawned today, every process is SCHED_OTHER, nice 0, with the
  default I/O class.

## 2. The change (`patches/E3-S1_EPG_GRAB_PRIORITY.md`)

- `companion/plugins/epg.py`, `_grab_from_candidate`: with the flag, the
  grab's argv is prefixed with `chrt -i 0` → `nice -n 19` →
  `ionice -c 3`.
- The whole tree then runs SCHED_IDLE, nice 19, idle I/O. The flagged
  runs' sampler saw policy 5 on every EPG thread sample (36,601-37,094
  per run).
- Absent = today's argv, byte for byte.
- Diff: `e3_s1_epg_grab_priority.diff` (`b8b706a7…4f09`).

## 3. The runs and the bar

`e3_s1_2026-10-06/e3_s1_table.md` holds every E2 row for the four runs
and E2's four comparable runs. `e3_s1_verdict.json` comes from
`e3_s1_analysis.py`.

| | control PS1-STREAM (no flag) | CONC r1 (flag) | CONC r2 (flag) | META (flag) | E2 PS1-STREAM | E2 CONC r1 / r2 | E2 META |
| --- | --- | --- | --- | --- | --- | --- | --- |
| host CPU mean % | 11.8 | 19.7 | 20.4 | 10.2 | 11.7 | 20.5 / 21.9 | 9.8 |
| busiest-core-per-second p95 % | 35.6 | **53.0** | **53.9** | 63.0 | 38.5 | 97 / 96 | 96 |
| PSI cpu some ms/s | 11.8 | 21.8 | 22.1 | 6.1 | 10.1 | 11.4 / 13.9 | 1.8 |
| rendered fps | **59.30** | 54.0 | 55.0 | — | 59.81 | 56.5 / 56.6 | — |
| video loss/min | **223** | 2,605 | 2,046 | — | 32 | 1,622 / 1,602 | — |
| resyncs | 7 | 177 | 137 | — | 0 | 199 / 204 | — |
| audio underruns | 22 | 411 | 542 | — | 11 | 448 / 312 | — |
| C2 max output gap ms | 271 | 390 | 416 | — | 280 | 473 / 421 | — |
| grabs ok/failed, median s | — | 200/0, 5.95 | 203/0, 6.04 | 232/0, 5.26 | — | 208/0, 5.9; 214/0, 5.8 | 228/0, 5.2 |
| EPG child CPU % / PSS MB | — | 74 / 482 | 78 / 481 | 72 / 487 | — | 79 / 484, 82 / 478 | 67 / 486 |

**The bar** (pre-registered §2):

| clause | needed | got | holds |
| --- | --- | --- | --- |
| a. CONC loss/min | ≤ 100 and ≤ 3 × control (668), both runs | 2,605 / 2,046 | **no** |
| b. CONC rendered fps | ≥ 59.5, both runs | 54.0 / 55.0 | **no** |
| c. CONC resyncs | ≤ 10 per run | 177 / 137 | **no** |
| d. grabs | failed 0; ok ≥ 205 META, ≥ 187 CONC; median ≤ 7.8 / 8.8 s | 232/0, 5.26; 200/0, 5.95; 203/0, 6.04 | yes |
| e. control comparable | host CPU 11.7 ± 2; rendered 59.81 ± 0.5 | 11.8; **59.30** (Δ 0.51) | **no** |

**Verdict: INCONCLUSIVE.** The rule is that (e) failing makes the task
INCONCLUSIVE, whatever (a)-(d) say. Tonight's link was worse than E2's:
the control lost 223 packets/min against 32.

**Read beside the bar:** (a)-(c) would fail on any comparable night.

- The flagged CONC loss is 9-12 × tonight's control, against a limit of
  3 ×.
- Its rendered fps is 4.3-5.3 below the control.

The priority change did not bring E1-CONC toward E1-PS1-STREAM.

## 4. The aligned frame (reported, not gated)

This is `e2_analysis.py`'s CONC section, unchanged, pointed at the
flagged runs (`aligned_ctl/` against tonight's control,
`aligned_e2/` against E2's).

Mean across ~200 grabs per run, by second after the grab's start:

| s after grab start | 0 | 1 | 2 | 3 | 4 | 5 | 6-10 | control baseline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| busiest core % r1 (flag) | 29 | 47 | 39 | 39 | 32 | 34 | 23-26 | 25.7 (sd 4.5) |
| busiest core % r2 (flag) | 32 | 46 | 40 | 37 | 33 | 34 | 25-30 | |
| *E2, no flag, r1* | *40* | *57* | *78* | *60* | *52* | *54* | *30-34* | *26.8* |
| lost packets/s r1 (flag) | 44 | **65** | 55 | 31 | 32 | 32 | 14-51 | 3.4 (sd 30) |
| lost packets/s r2 (flag) | 38 | **56** | 48 | 26 | 24 | 23 | 1-28 | |
| *E2, no flag, r1* | *34* | *65* | *43* | *6* | *10* | *7* | *19-23* | *0.55* |
| relay thread CPU % r1 (flag) | 7.0 | 6.4 | 7.7 | 7.5 | 7.1 | 7.2 | 6.8-7.1 | 7.8 |
| encoder dup+drop/s, eno1 tx drops/s | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

- **The flag did what it was meant to do to the CPU.**
  - The busiest core's peak 1-2 s after a grab starts fell from 73-78 %
    to 46-47 %.
  - The window's busiest-core-per-second p95 fell from 96-97 to 53-54.
  - PSI cpu rose (22 vs 11-14 ms/s): the grabber now waits rather than
    competes.
- **The loss did not follow.** It still peaks 1 s after each grab starts,
  at the same height as in E2 (56-65 packets/s).
- No host-side drop appears, the relay thread is flat, and the encoder
  shows no dup/drop.
- **So the loss at the grab's start is not explained by CPU competition
  on the host.** Some other effect of the grab's start coincides with it.
  Candidates the 1-s data cannot separate:
  - the grabber's own network traffic on the same router, a DNS/TLS
    burst;
  - something in the companion's process at the grab's start, e.g. the
    25.6 MB guide-metadata JSON parse holding the GIL. **This is a new
    hypothesis, not tested here.** It is consistent with E3-S2's probe
    target.

## 5. What the user would be adopting, and the revert

- **Adoption, if the user wanted it despite the verdict:** one line in
  the unit's drop-in,
  `Environment=PRIVYHUB_EPG_GRAB_PRIORITY=idle`. **Not recommended on
  this evidence.**
- **Revert:** delete the line, `systemctl --user daemon-reload`, restart
  the unit. The code path is dormant when the flag is absent.

## 6. State at the end; files

- **Final state** (`runs/final_state.json`, 04:54:54Z):
  - manager `PRIVYHUB_*` none;
  - environ exactly `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`;
  - the e3 drop-in absent;
  - no game, RetroArch or encoder;
  - the PS1 files identical;
  - **APK CONFIRMED**.
- Every flagged run's teardown removed the drop-in and checked the
  environ.
- No `nft`, no `sudo`, the Opal untouched.
- Files (`e3_s1_2026-10-06/`):
  - `probe.md` and `probe/`;
  - `e3_s1_preregistration.txt` and `.sha256`;
  - `e3_s1_epg_grab_priority.diff`;
  - `runs/` (4 runs, `manifest.sha256`, `--check`);
  - `e3_s1_analysis.py`, `e3_s1_table.md/.json`, `e3_s1_verdict.json`,
    `aligned_ctl/`, `aligned_e2/`;
  - `redact_check.txt`.
- Git status: `logs/e3_s1_git_status.txt`.
