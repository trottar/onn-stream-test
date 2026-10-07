---
memory_schema: 1
as_of: 2026-10-07
baseline_commit: bf2120c
---

# E3-S5B — the audio sender's pacing, decided: five interleaved runs

**Classification:**

- **REJECTED by the pre-registered bar**, on clause (b) in one run.
  Flagged run F2 had **18** audio underruns against a limit of
  max(controls) + 5 = **16**.
- **The question this task was set, whether `=frame` makes the loss
  burstier, is answered: no.**
  - The deciding pooled-minutes clause (d) holds with room.
  - Not one minute in the five runs lost more than 100 packets.
  - E3-S5's bursty flagged run did not recur in 60 flagged minutes.
- Clauses (a), (c), (e) and comparability hold in every run.
- No new change: E3-S5's flag and code as committed. **NOT ADOPTED;
  nothing committed.** The flag is absent at the end; E2's final state
  is restored.

**Context:**

- Task: `handoffs/E3-S5B_AUDIO_SENDER_PACING_DECISIVE_TASK.md`, queue B
  item 1 (`handoffs/QUEUE_2026-10-06B.md`).
- **Baseline commit: `bf2120c`**, the user's E3-queue commit.
- Files: `e3_s5b_2026-10-06/`.
- Timeline (UTC):

  | date | time | what |
  | --- | --- | --- |
  | 10-06 | 23:23 | preconditions held (`precondition.json`) |
  | 10-06 | 23:24-23:29 | the send-timing probe |
  | 10-06 | **23:29:46** | **pre-registration hashed** (`70457905…c3003`). Its first line's "~23:31Z" was an estimate; the hash time is the true one. |
  | 10-06 → 10-07 | 23:29:52-01:31:01 | C1, F1, C2, F2, F3, each OK on its first attempt |

## 1. The probe (`probe.md`): no bunching mechanism at the sender

A measurement-only trace hook (`PRIVYHUB_AUDIO_SEND_TRACE`, off; this
task's only code) timed every `sendto` for 60 s, without and with the
flag.

| | no flag | `=frame` |
| --- | --- | --- |
| tick gap median / p99 / max ms | 4.998 / 5.19 / 5.95 | 4.999 / 5.52 / 6.63 |
| tick gap sd ms | 0.07 | 0.17 |
| gaps > 10 ms / > 20 ms | 0 / 0 | 0 / 0 |
| bunches ≥ 4 datagrams | 0 | 0 |

- **The flag widens the sub-millisecond jitter but creates no gaps and no
  bunches.**
- This was stated before the runs: the probe offers no sender-side
  mechanism for bursty loss.

## 2. The runs and the bar

From `e3_s5b_table.md`, `e3_s5b_verdict.json` and `loss_per_minute.txt`
(`e3_s5b_analysis.py`). The runs are in run order.

| | C1 | F1 | C2 | F2 | F3 |
| --- | --- | --- | --- | --- | --- |
| audio sender, % of a core | 13.1 | **2.0** | 13.0 | **2.35** | **2.0** |
| companion, % of a core | 24.6 | **13.3** | 24.5 | **14.3** | **13.4** |
| socket W | 20.8 | 18.0 | 19.6 | 18.3 | 18.8 |
| host CPU % | 10.6 | 10.2 | 10.5 | 10.9 | 10.4 |
| rendered fps | 59.93 | 59.92 | 59.96 | 59.92 | 59.93 |
| **audio underruns (window)** | 11 | 15 | 7 | **18** | 8 |
| video loss/min (window) | 9.2 | 13.5 | 12.9 | 13.8 | 12.4 |
| per-minute loss median; minutes > 100 | 8; 0 | 9.5; 0 | 3.5; 0 | 10; 0 | 10; 0 |
| spikes ≥ 20 ms/min; stale drops/min | 39; 0.69 | 36; 1.48 | 33; 0.65 | 35; 0.74 | 32; 0.74 |
| max output gap ms (report; C2) | 226; 76 | 423; 56 | 206; 66 | 349; 67 | 218; 70 |
| ladder decisions: rows, transitions | 669, 0 | 669, 0 | 651, 0 | 673, 0 | 641, 0 |

| clause | needed | got | holds |
| --- | --- | --- | --- |
| comparability | C1, C2 within 11.69 ± 2 and 59.81 ± 0.5; C1 − C2 ≤ 0.5 fps | 10.6 / 10.5; 59.93 / 59.96 | yes |
| a. sender ≤ 4 %, companion ≤ 17 % | every F | 2.0-2.35; 13.3-14.3 | yes |
| b. underruns ≤ max(C) + 5 = 16 and ≤ 20 | every F | 15 / **18** / 8 | **no (F2)** |
| c. rendered ≥ 59.5; RetroArch 60 ± 0.5 | every F | 59.92-59.93; 60.0 | yes |
| **d. pooled minutes** | median F ≤ 3 × median C; share > 100 in F ≤ C's + 0.10 | median **10 vs 5** (limit 15); share **0 vs 0** | **yes** |
| e. D-BASE spikes < 200/min, stale < 20/min | every F | ≤ 36; ≤ 1.48 | yes |

**Verdict: REJECTED** (clause b, F2, by 2 underruns).

**Read beside the bar:**

- **Loss.** The flagged median is twice the controls' (10 vs 5
  packets/min), but within the pre-registered 3 ×. Neither side had a
  bursty minute. **E3-S5's run 1 bursts were a link episode, as far as
  60 flagged minutes can say.**
- **Underruns are the signal that remains.** All flagged sessions
  across E3-S5 and S5B had 9, 15, 15, 18 and 8 underruns per 20 min
  (mean 13.0). The unflagged ones had 14, 11 and 7 (mean 10.7).
  - That is a small, inconsistent excess.
  - It is consistent with the probe's wider tick jitter, sd 0.17 vs
    0.07 ms. An early or late audio packet near the client's cushion
    edge is the plausible path; this is **not tested**.
  - F2's 18 is also 1 above D-BASE's audio row (17 per session).
- **The probe's mechanism does not explain the rejection.** It found no
  gaps and no bunches. The jitter is the only measured difference.

## 3. What the user would be adopting, and the revert

- **Adoption, if wanted despite the verdict:** one drop-in line,
  `Environment=PRIVYHUB_AUDIO_SENDER_PACING=frame`.
  - Gain: ~11 % of a core and ~1-2.7 W while streaming.
  - Cost: a possible ~2-3 more underruns per 20 min.
- **Revert:** delete the line, `systemctl --user daemon-reload`, restart
  the unit.
- A variant was not tested; it would be a new task. It would keep the
  single timed wait but add a short final spin, to restore today's
  jitter.

## 4. State at the end; files

- **Final state** (`runs/final_state.json`, 01:31:01Z):
  - manager none; environ exactly the live default;
  - the e3 drop-in absent;
  - no game, RetroArch or encoder;
  - the PS1 files identical; **APK CONFIRMED**.
- The trace hook was used only in the probe and is absent everywhere
  else.
- No `nft`, no `sudo`, the Opal untouched.
- Files (`e3_s5b_2026-10-06/`):
  - `precondition.json`, `probe.md`, `e3_s5b_probe.py`;
  - `trace_noflag.txt`, `trace_flag.txt`, `probe_*_run.json`,
    `probe_stats.json`, `e3_s5b_send_trace_hook.diff`;
  - the pre-registration and its `.sha256`;
  - `runs/` (5 runs, `manifest.sha256`, `--check` OK);
  - `e3_s5b_analysis.py`, `e3_s5b_table.md/.json`,
    `e3_s5b_verdict.json`, `loss_per_minute.txt`, `redact_check.txt`.
- Git status: `logs/e3_s5b_git_status.txt`.
