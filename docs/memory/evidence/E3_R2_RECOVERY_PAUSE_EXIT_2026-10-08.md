---
memory_schema: 1
as_of: 2026-10-08
baseline_commit: 969085f
---

# E3-R2 — the false pause, fixed: threshold, exit, and a faithful replay

**Classification: REJECTED by the pre-registered bar** (clauses iii and
v). Everything the change is for held:

- **The replay is faithful now and its bar held (r1-r4).**
- **No recovery pause of any kind in four 20-min windows** (ii).
- The gap log saw a **1,253.5-ms** client→host silence in PS1 r1. Today's
  1-s rule would have paused on it and, with no exit, given up and saved
  120 s later. v2 let it pass.

What failed:

- **(iii) the CONC rows' rendered fps:** 58.97 and 59.42 are *above*
  E3-S6A's 57.64 by more than 0.5. The band is two-sided, and E3-S6A's
  CONC was a lossier night (1,312 loss/min against 518 / 284 here).
  Host CPU is within its band in all four runs.
- **(v) one gap began 41 ms after a gap-log write.** It is the second
  silence of one stall cluster (1,253.5 ms, then 361.6 ms 575 ms later).
  The write runs on its own thread and costs ~42 µs, so it is very
  unlikely to have caused a 362-ms uplink silence. The pre-registered
  rule counts any such gap anyway.

The bar is not changed after data. **NOT ADOPTED**; nothing committed.
The code is in the tree, dormant behind `PRIVYHUB_RECOVERY_TRIGGER=v2`.
**Adoption in any case waits for the user's nft paste (§4)**, the only
test of the real-drop path on the air.

**Context:**

- Task: `handoffs/E3-R2_RECOVERY_PAUSE_EXIT_TASK.md`, item 1 of
  `handoffs/QUEUE_2026-10-08B.md`.
- **Baseline commit: `969085f`**, the user's E3-R1/S7 commit.
- It ran on the adopted state (live, the guide index, Snes9x).
- Files: `e3_r2_2026-10-08/`.
- Timeline (UTC, 2026-10-08):

  | time | what |
  | --- | --- |
  | 13:08 | preconditions held (`precondition.json`, the three-line state); the change written; unit tests 17/17 |
  | 13:11-13:23 | the gap-log probe (window 13:12:38-13:22:38), `PRIVYHUB_RECOVERY_GAP_LOG=1` alone; teardown clean |
  | **13:23:28** | **pre-registration hashed** (`95f2995a…7943`) |
  | 13:23 (after the hash) | the replay scored: r1-r4 hold |
  | 13:23:44-15:00:56 | PS1-STREAM ×2, CONC ×2 with the flag; all OK, all valid |

## 1. The change (`patches/E3-R2_RECOVERY_PAUSE_EXIT.md`)

Three parts, all behind `PRIVYHUB_RECOVERY_TRIGGER=v2`. Absent = today,
byte for byte in behaviour. Diff `e3_r2_recovery_exit.diff` (on top of
R1's v2 threshold, which `969085f` carries).

1. **The gap log** (also alone as `PRIVYHUB_RECOVERY_GAP_LOG=1`).
   - The controller receive loop notes every client→host silence over
     250 ms.
   - 500 ms after a silence ends, it hands one line to its own writer
     thread: start, end, length, the catch-up burst's packets, a
     truncated mark, and the time written.
   - The file is `logs/games/native_stream_ctrl_gaps.log`: 512 KB plus
     one rotated copy.
2. **The threshold.** R1's v2: 5,000 ms, confirmed on two checks
   ≥ 250 ms apart with no packet between.
3. **The exit.** A `controller_silence` pause resumes by itself when
   both hold:
   - (a) the controller age is < 500 ms on two checks ≥ 250 ms apart;
   - (b) a heartbeat received after that shows the client's output age
     at 0-300 ms. A stale one waits for the next.

   How it resumes, and its limits:
   - It uses `EmulatorManager.resume()`, the call the client's gate
     makes, and logs `resumed` with `via: controller_return`.
   - Nothing is loaded (R3c2 untouched). It needs the encoder up.
   - A failed resume stays paused and logs `controller_exit_failed`.
   - The 120-s give-up still applies. A client-triggered pause keeps its
     own exit.
   - Why 300 ms: it is the task's figure. R1's `idle_stats.json` has the
     client's idle output-age maximum at 144 ms (the 295 ms there is the
     controller age), and a real drop reads ≥ 1,000 ms, rising.

**Tests** (`test_e3_r2.py`, `unit_tests.txt`; synthetic timelines, not
data):

- 17/17 pass: confirm 4, gap log 5, exit 8.
- The writer thread was also run end to end against a temp file.
- `tools/test_c3_f1_recovery_restart.py` is 7/8: the same old error R1
  recorded at `def1ad1`.
- Cost: the gap log adds 51.5 ns per packet (0.0024 points of a core at
  460 packets/s). A written line costs 42.4 µs, off the receive thread.

## 2. Before the runs: the probe and the replay

**The gap-log probe** (`e3_r2_gap_probe.py`, `gap_probe/`,
`gap_stats.json`): a PS1 stream PLAYING for 600 s, nobody at the
controller, today's trigger live.

- **One gap > 250 ms in 10 min** (254.6 ms; its burst 335 packets). None
  over 500 or 1,000 ms, so today's rule would not have paused.
- The controller age polled at 4 Hz peaked at 178 ms; the client's output
  age at 59 ms. PLAYING throughout; teardown clean.
- **Idle, the uplink is quiet at this resolution.** The stalls appeared
  under the suite's load (§3).

**The replay** (`e3_r2_replay.py` → `replay.json`, `replay.md`,
`replay_console.txt`).

- It reads R1's `timelines.json` in place (R1's scripts were not run).
- The fix: recorded recovery state from neighbouring events, before the
  event's own time, is carried. A replayed controller firing while that
  state is not PLAYING does not happen.
- **S1-CONC r2a was excluded from r1 by name before the hash** (the 1-s
  resolution limit).

| clause | needed | got | holds |
| --- | --- | --- | --- |
| r1. today's rule reproduces every gated event (±2 s); no fire on N05 / F05 | all but S1-CONC r2a | all 16 gated. **S1-CONC r1b now at +0.83 s** (R1's model: −5.24 s; the carried state is r1a's pause until −3 s). A2 r1 −1.42 s, E2-1080P r1 +0.56 s. N05, F05 none | **yes** |
| r2. v2 fires on every real drop within +2 s of today | 8 | 8 (the client trigger, unchanged by v2) | **yes** |
| r3. v2's controller rule fires on none of the four controller false pauses | none | none in any ±60 s window | **yes** |
| r4. the exit resumes each of the four within 10 s of the packets' return | 4 | E2-1080P r1 3.03 s (telemetry substitute, pre-registered), S1-CONC r1b 3.04, S1-CONC r2a 3.0 (overlapping-run basis), A2 r1 3.01 | **yes** |

Reported, not gated:

- S1-CONC r2a, today's rule: the first replayed fire is at +24.86 s, as
  in R1.
- Out of suite: 0401 and 0402 are reproduced; 1514 has no data.
- The client pauses under v2 fire as recorded: the client's detector is
  unchanged.

## 3. The runs and the bar

`runs/` (4 runs; `manifest.sha256`; `--check` OK), `runs_console.log`,
`e3_r2_analysis.py` → `validity.json`, `gaps/`, `e3_r2_table.md/.json`,
`e3_r2_verdict.json`.

| | PS1 r1 (flag) | PS1 r2 (flag) | CONC r1 (flag) | CONC r2 (flag) | E2 PS1-STREAM | E3-S6A CONC |
| --- | --- | --- | --- | --- | --- | --- |
| valid (no recovery pause) | yes | yes | yes | yes | yes | yes |
| recovery events in window | none | none | none | none | — | — |
| host CPU % | 11.1 | 11.7 | 20.9 | 23.4 | 11.7 | 22.2 |
| rendered fps | 59.81 | 59.85 | **58.97** | **59.42** | 59.81 | 57.64 |
| video loss/min | 58.6 | 40.2 | 518 | 284 | 32.3 | 1,312 |
| underruns; resyncs | 13; 0 | 20; 1 | 12; 25 | 5; 9 | 11; 0 | 11; 52 |
| companion CPU % | 25.0 | 25.2 | 26.0 | 27.1 | 24.3 | 26.5 |
| gaps > 250 ms (max ms; > 1 s) | 7 (**1,253.5**; 1) | 3 (398.9; 0) | 3 (357.2; 0) | 1 (268.8; 0) | — | — |
| gap log cost, points of a core | 0.0024 | 0.0024 | 0.0025 | 0.0025 | — | — |
| gaps starting ≤ 50 ms after a write | **1** | 0 | 0 | 0 | — | — |

| clause | needed | got | holds |
| --- | --- | --- | --- |
| (i) r1-r4 | all | all | yes |
| (ii) no `gave_up_saved`; no unexited `controller_silence` pause | none | **no recovery event at all** in four windows | yes |
| (iii) host CPU ± 2, rendered ± 0.5 of the reference | PS1 11.69 / 59.81; CONC 22.2 / 57.64 | PS1 in band; CONC CPU in band, **rendered 58.97 / 59.42 (+1.33 / +1.78)** | **no** |
| (iv) companion CPU ± 2 of the reference | 24.3; 26.5 | 25.0, 25.2; 26.0, 27.1 | yes |
| (v) gap log ≤ 0.5 point; no gap caused by its own write | | 0.0025; **one gap 41 ms after a write** (PS1 r1, 13:44:17.675Z) | **no** |

**Verdict: REJECTED** (iii, v).

**Read beside the bar:**

- **(iii) fails on the good side.** Rendered fps cannot move *up*
  because of a recovery trigger that never fired. Tonight's CONC link
  was cleaner than E3-S6A's (loss 518 / 284 vs 1,312; resyncs 25 / 9 vs
  52). Comparing CONC rows across nights carries that drift; a same-night
  control would remove it.
- **(v)** is one coincidence inside a stall cluster. Of the other 14
  gaps in the runs, the nearest began 0.75 s after a write.
- **The change did its job:**
  - PS1 r1's 1,253.5-ms uplink silence (13:44:15.847Z, burst 712
    packets) is exactly the false-pause case R1 located. Today's rule
    would have fired at +1.0 s; v2 needs 5 s.
  - Nothing paused in 80 min. The exit never had to run in a run.
- PS1 loss/min (58.6 / 40.2) is above E2's 32.3: reported, not banded.
  Underruns were 13 / 20 against E2's 11.

## 4. The hand step: the real-drop check on the air (the user's; adoption waits for it)

The runs cannot test a real drop. That needs nft, and nft is the user's
step:

- The harness is R3b's `d_base_r3b_2026-09-21/r3b_run.sh`. It drops UDP
  ports with `sudo -n nft` for N seconds and records the recovery lines.
- `tools/c3_l4_nft_night.py` cannot be used: its preflight refuses an
  unadopted flag.
- With this task's code, the flag also turns on the gap log and the exit.

One paste, from the repo root:

```bash
printf '[Service]\nEnvironment=PRIVYHUB_RECOVERY_TRIGGER=v2\n' > ~/.config/systemd/user/privyhub-companion.service.d/e3_flag.conf
systemctl --user daemon-reload && systemctl --user restart privyhub-companion
(cd docs/memory/evidence/d_base_r3b_2026-09-21 && ./r3b_run.sh V2-N3 output 48100,48101 3 30 && ./r3b_run.sh V2-N15 output 48100,48101 15 40 \
  && ./r3b_run.sh V2-C2 input 48102 2 30 && ./r3b_run.sh V2-C8 input 48102 8 40)
rm ~/.config/systemd/user/privyhub-companion.service.d/e3_flag.conf
systemctl --user daemon-reload && systemctl --user restart privyhub-companion && python3 tools/e3_state.py
```

**What the reply must contain** (each run's `recovery_lines.jsonl`; the
gaps are in `logs/games/native_stream_ctrl_gaps.log`):

| run | expected |
| --- | --- |
| V2-N3, V2-N15 (host→client dropped) | `desync_pause` `client_output_silence` at ~+1.3 s, then `resumed` (N15 after its `encoder_restart`s), as R3b N3 / N15. **The real-drop path is unchanged.** |
| **V2-C2** (client→host dropped 2 s) | **no `desync_pause`.** Today's rule pauses at +1 s and never comes back. A ~2,000-ms gap line. |
| **V2-C8** (client→host dropped 8 s) | `desync_pause` `controller_silence` at ~+5.25 s. **Then `resumed` with `"via": "controller_return"` within ~10 s of the clear, and no `gave_up_saved`** (the exit working). An ~8,000-ms gap line. |

The last line of the reply: `e3_state.py` `"ok": true`, three lines.

## 5. State at the end; files

- **Final state** (`runs/final_state.json`, 15:00:56Z):
  - manager none; environ exactly live + the index + Snes9x;
  - no e3 drop-in; no game, RetroArch or encoder;
  - the PS1 files identical; **APK CONFIRMED**.
- The flag and the gap log are absent; the code is dormant.
- No `nft`, no real `sudo`, the Opal untouched; nothing fetched, nothing
  deleted. No other task's script was run (R1's timelines read in place;
  E3-A2's validity rule re-implemented).
- Files (`e3_r2_2026-10-08/`):
  - `precondition.json`, `predecessor_sha256.txt`, `e3_r2_recovery_exit.diff`;
  - `test_e3_r2.py`, `unit_tests.txt`;
  - `e3_r2_gap_probe.py`, `gap_probe/`, `gap_probe_console.log`, `gap_stats.json`;
  - the pre-registration and its `.sha256`;
  - `e3_r2_replay.py`, `replay.json`, `replay.md`, `replay_console.txt`;
  - `runs/` (`manifest.sha256`, `check.txt`), `runs_console.log`;
  - `e3_r2_analysis.py`, `analysis_console.txt`, `validity.json`,
    `gaps/`, `e3_r2_table.md/.json`, `e3_r2_verdict.json`;
  - `redact_check.txt`.
- Git status: `logs/e3_r2_git_status.txt`.
