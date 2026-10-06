# E3-S5 probe — the audio sender's wake-ups per packet (2026-10-06 06:41-06:52Z)

Measurement before the change. A PS1 stream (E1-PS1-STREAM's launch through `tools/e1_suite.py`'s own
functions, `e3_s5_probe.py`) PLAYING, 60 s settle, then 180 s of the companion's per-thread counters
(`tools/e3_probe.py threads`: `/proc/<pid>/task/<tid>/status` context switches, `schedstat`, the syscall mode
every 0.1 s) and the audio counters from the companion's status. E1's teardown after (environ the live
default, APK CONFIRMED, PS1 files identical, no game). Files: `probe_threads.json`, `probe_run.json`.

| the audio sender thread (SCHED_RR) | today (probe) | with the flag (smoke, not data) |
| --- | --- | --- |
| CPU, % of a core | **13.7** | 2.25 |
| voluntary context switches / s | **17,167** | 277 |
| involuntary / s | 0.2 | 0 |
| syscall mode in 0.1-s samples | futex 82 %, running 14 %, clock_nanosleep 5 % | futex 98 %, running 2 % |
| audio packets sent / s (originals; + duplicates) | 200 (+ 200) | 200 (+ 200) |
| send underflows / errors | 0 / 0 | 0 / 0 |
| **wake-ups per original packet** | **85.8** | **1.39** |
| the companion's threads, total % of a core | 25.2 | 13.3 |

- **Wake-ups per packet = 85.8, far above 1.5: the hypothesis stands.** The thread is mostly waking and
  polling, not sending.
- **Why**, from the code (`companion/native_session_io.py`, `_linux_wait_until`, the 5-ms PHA1 pacer):
  - while more than 1.5 ms remain it waits 1 ms at a time (`Event.wait(0.001)`);
  - from 1.5 ms to 0.25 ms it yields (`time.sleep(0)`);
  - for the last 0.25 ms it spins.
  - The yield loop accounts for most of the wake-ups.
- **The change** (`e3_s5_audio_sender_pacing.diff`): with `PRIVYHUB_AUDIO_SENDER_PACING=frame`, read once when
  the sender starts, the wait is **one timed wait to the packet's deadline** (`Event.wait(remaining)`, re-armed
  if early).
  - Packetization (5 ms, 200/s), redundancy 2/4, `SCHED_RR` priority 1 and the relay are unchanged.
  - Absent = today's wait. The only addition on that path is one boolean check per wait iteration.
  - The comment in the code records that "Baseline 34" validated the final spin against scheduler catch-up
    bursts. That is exactly what the bar's underrun, loss and D-BASE clauses test.
- **The smoke's session report** (4 min each, reported, not data):

  | | probe (no flag) | smoke (flag) |
  | --- | --- | --- |
  | audio underruns | 2 | 9 |
  | audio lost packets | 4 | 5 |
  | video lost | 115 | 66 |
  | spikes ≥ 20 ms | 192 | 204 |
  | stale drops | 14 | 18 |
  | max output gap ms | 92 | 208 |

  Underruns 2 → 9 is a signal to watch in the runs; one 4-min pair cannot separate it from noise.
