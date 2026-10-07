# E3-S5C probe — the audio sender's send timing three ways (2026-10-07 05:32-05:38Z)

Measurement before the runs, on the adopted state. `e3_s5c_probe.py` (E3-S5B's probe extended to a third session and
to the sender thread's own counters) ran three PS1-stream sessions (E1-PS1-STREAM's launch), each with the dormant
trace hook (`PRIVYHUB_AUDIO_SEND_TRACE`, 60 s of `sendto` times from 30 s after the sender starts) in the E3 drop-in:
no pacing flag, `=frame`, `=frame_spin`. The sender thread (the companion's one SCHED_RR thread) was read at ~+35 s and
~+85 s, inside the trace (`/proc/<pid>/task/<tid>/status` context switches, `schedstat` CPU). Each session was torn
down by E1's rules (drop-in removed, environ checked against the adopted two lines, APK CONFIRMED, PS1 files
identical). Files: `trace_<tag>.txt`, `probe_<tag>_run.json`, `probe_stats.json`.

| 60 s, 12,000 originals + 12,000 duplicates each | no flag | `=frame` | **`=frame_spin`** |
| --- | --- | --- | --- |
| tick gap median ms | 4.999 | 4.996 | 4.998 |
| p99 / p99.9 / max ms | 5.24 / 5.57 / 5.74 | 5.53 / 5.79 / 6.77 | **5.31 / 5.49 / 5.98** |
| min ms | 4.23 | 2.64 | **4.06** |
| **sd ms** | **0.076** | **0.181** | **0.102** |
| gaps > 10 ms / > 20 ms | 0 / 0 | 0 / 0 | 0 / 0 |
| gaps < 1 ms | 0 | 0 | 0 |
| bunches ≥ 4 datagrams within 0.2 ms each | 0 | 0 | 0 |
| voluntary context switches/s (sender thread) | 16,875 | 272 | 302 |
| **wake-ups per packet** | **84.4** | 1.36 | **1.51** |
| involuntary switches/s | 0.4 | 0 | 0 |
| **sender thread CPU, % of a core** | **13.2** | **2.0** | **6.3** |

**Before the runs, as the task asks:**

- The task stated `frame_spin` was expected at sd ≈ 0.07 ms and ~1.4 wake-ups per packet, and that **if its sd is not
  ≤ 0.10 ms the hypothesis is already in doubt**. Measured: **sd 0.102 ms — just over 0.10. The hypothesis is in
  doubt by this rule.** The runs still go.
- What the spin did restore: the early ticks (min 4.06 vs `frame`'s 2.64 ms; today's 4.23) and most of the tail (p99
  5.31 vs 5.53; today's 5.24; max 5.98 vs 6.77). What it did not: the sd sits between today's and `frame`'s,
  nearer today's. The timed wait still oversleeps past its 0.25-ms margin on some ticks (the late tail), which the
  spin cannot undo.
- Wake-ups: 1.51 per packet, near the expected ~1.4 (the timed wait, plus a second short wait on a few early wakes).
  The CPU saving is partial: 6.3 % of a core against today's 13.2 and `frame`'s 2.0, as the 0.25-ms spin per 5-ms
  period (5 %) predicts.
- No gaps, no bunches, as for `frame` in E3-S5B.
