---
memory_schema: 1
as_of: 2026-10-06
baseline_commit: d9fdbdd
---

# E3-S5 — the audio sender's cost: one timed wait per packet instead of polling

**Classification:**

- **REJECTED by the pre-registered bar**, on clause (c) in flagged run 1
  only. Its video loss was 106.5/min, against a limit of 3 × the control's
  29.6 = 88.9.
- Flagged run 2 met every clause (loss 22.9/min). Clauses (a), (b), (d)
  and the comparability clause (e) hold in both runs.
- **The cost cut is large and clean:**
  - the audio sender went from 13.1 % to **2.5 %** of a core;
  - the companion from 24.8 % to **14.6 %**;
  - socket power fell 1-2 W.
- Whether run 1's extra loss is the change or the link cannot be told from
  two runs. The bar asks for both, so the verdict is REJECTED.
- One change behind `PRIVYHUB_AUDIO_SENDER_PACING=frame`. **NOT ADOPTED;
  nothing committed.** The flag is absent at the end; E2's final state is
  restored.

**Context:**

- Task: `handoffs/E3-S5_AUDIO_SENDER_COST_TASK.md`, queue item 5 (the last).
- Baseline commit: `d9fdbdd`.
- Files: `e3_s5_2026-10-06/`.
- E3-S1..S4's flags are absent (no compounding).
- Timeline (UTC, 2026-10-06):

  | time | what |
  | --- | --- |
  | 06:41 | preconditions held (`precondition.json`) |
  | 06:41-06:46 | the probe |
  | 06:46-06:51 | the change and a flagged smoke (not data) |
  | **06:52:05** | **pre-registration hashed** (`3a101438…83a1`) |
  | 06:52-08:05:02 | the control, then 2 flagged runs, all OK first time |

## 1. The probe (`probe.md`)

| the SCHED_RR audio sender | today | with the flag (smoke) |
| --- | --- | --- |
| CPU, % of a core | 13.7 | 2.25 |
| voluntary context switches / s | 17,167 | 277 |
| **wake-ups per original packet** (200/s) | **85.8** | **1.39** |

- 85.8 is far above 1.5, so the hypothesis holds and the task proceeds.
- The 5-ms pacer waits 1 ms at a time until 1.5 ms before the deadline,
  then `sched_yield`s until 0.25 ms before, then spins.

## 2. The change (`patches/E3-S5_AUDIO_SENDER_PACING.md`)

- `companion/native_session_io.py` (+11 lines):
  - the sender reads the flag once when it starts;
  - with `=frame`, `_linux_wait_until` does **one** `Event.wait` to the
    packet's deadline (re-armed if early).
- Packetization (5 ms, 200/s + 200 duplicates), redundancy 2/4,
  `SCHED_RR`/1 and the relay are unchanged.
- Absent = today's wait.
- Diff: `e3_s5_audio_sender_pacing.diff`.

## 3. The runs and the bar

From `e3_s5_table.md`; the verdict is in `e3_s5_verdict.json`
(`e3_s5_analysis.py`).

| | control (no flag) | flag r1 | flag r2 | E2 PS1-STREAM |
| --- | --- | --- | --- | --- |
| **audio sender thread, % of a core** | 13.1 | **2.5** | **2.5** | 12.9 |
| **companion CPU, % of a core** | 24.8 | **14.6** | **14.7** | 24.3 |
| relay thread % | 7.7 | 7.7 | 7.9 | 7.8 |
| host CPU mean % | 10.6 | 10.4 | 12.0 | 11.7 |
| socket W | 20.9 | 18.6 | 19.9 | 20.4 |
| audio underruns (window) | 14 | 9 | 15 | 11 |
| rendered fps | 59.94 | 59.77 | 59.91 | 59.81 |
| RetroArch fps | 60.0 | 60.0 | 60.0 | 60.0 |
| **video loss/min** | 29.6 | **106.5** | 22.9 | 32.3 |
| minutes with > 100 lost (of 20) | 1 | **7** | 1 | — |
| spikes ≥ 20 ms / min (session) | 36.8 | 35.5 | 41.1 | 60 |
| stale drops / min | 0.74 | 0.65 | 0.69 | — |
| max output gap ms (report; C2) | 189; 65 | 370; 71 | 176; 72 | —; 280 |
| C2 receive → decode median ms | 9 | 9 | 9 | 9 |

| clause | needed | flag r1 | flag r2 |
| --- | --- | --- | --- |
| a. sender ≤ 4 % and companion ≤ 17 % | | 2.5 / 14.6 ✓ | 2.5 / 14.7 ✓ |
| b. underruns ≤ control + 5 (19) and ≤ 20 | | 9 ✓ | 15 ✓ |
| c. rendered ≥ 59.5; RetroArch 60 ± 0.5; loss ≤ 3 × control (88.9) | | 59.77, 60.0, **106.5 ✗** | 59.91, 60.0, 22.9 ✓ |
| d. D-BASE: spikes < 200/min, stale < 20/min (loss < 10 not gated: the control's 29.6 fails it itself; reported) | | ✓ | ✓ |
| e. control comparable (11.69 ± 2; 59.81 ± 0.5) | 10.61; 59.94 ✓ | | |

**Verdict: REJECTED** (clause c, run 1).

**Read beside the bar** (`loss_per_minute.txt`):

- Run 1's loss came in **bursts**: 7 of 20 minutes had more than 100
  lost packets, against 1 in the control and 1 in run 2.
- Between the bursts its loss (median 28/min) is like run 2's (18) and
  the control's (10).
- The same-night link was bursty earlier (E3-S1's control lost 223/min at
  03:20-03:43).
- Two flagged runs, one clean and one bursty, cannot separate a link
  episode from an effect of the change on burst timing. The change does
  alter when the 400 audio datagrams per second leave.
- The D-BASE loss row (< 10/min) was not met by tonight's control either,
  which is the reason it is reported and not gated.

**If the user wants it decided:** a third flagged run and a second
control on another night would. That is a new pre-registration and the
user's call. The bar is not changed here.

## 4. What the user would be adopting, and the revert

- **Adoption, if wanted despite the verdict:** one drop-in line,
  `Environment=PRIVYHUB_AUDIO_SENDER_PACING=frame`. It saves ~10 % of a
  core and ~1-2 W while streaming. It carries one run's unexplained loss
  bursts.
- **Revert:** delete the line, `daemon-reload`, restart.

## 5. State at the end; files

- **Final state** (`runs/final_state.json`, 08:05:02Z):
  - manager none; environ exactly the live default;
  - the e3 drop-in absent;
  - no game, RetroArch or encoder;
  - the PS1 files identical; **APK CONFIRMED**.
- The probe and the smoke each tore down the same way (`probe_run.json`,
  `smoke_flag_run.json`).
- No `nft`, no `sudo`, the Opal untouched.
- Files (`e3_s5_2026-10-06/`):
  - `precondition.json`, `probe.md`, `e3_s5_probe.py`;
  - `probe_threads.json`, `probe_run.json`, `smoke_flag_threads.json`,
    `smoke_flag_run.json`;
  - the pre-registration and its `.sha256`; the diff;
  - `runs/` (3 runs, `manifest.sha256`, `--check` OK);
  - `e3_s5_analysis.py`, `e3_s5_table.md/.json`, `e3_s5_verdict.json`,
    `loss_per_minute.txt`, `redact_check.txt`.
- Git status: `logs/e3_s5_git_status.txt`.
