# E3-S7 probe — the grabber child's share, CPU vs network (2026-10-08 04:04-04:47Z)

Measurement before the change, on the adopted state, no task flag. `e3_s7_probe.py`: per arm one PS1-stream session
(E1-PS1-STREAM's launch), the 1-s sampler (`--e2 --telemetry`), E3-S6's probe hook (`PRIVYHUB_MEM_PROBE=1`): `op=prepare`
once, then `op=spawn` ×20 at 15-s spacing (the grabber child for CNBCUK.uk@SD, no parse, no cache write), aligned as
E3-S6 did (`e2_analysis.py`'s loss series; offsets 0..10 s; baseline = seconds outside 0..10 s of any trigger).

- **A** — the child as today;
- **B** — the child at SCHED_IDLE / nice 19 / idle I/O (E3-S1's flag `PRIVYHUB_EPG_GRAB_PRIORITY=idle`): CPU removed;
- **C** — the child in its own user + network namespace (this task's probe hook `PRIVYHUB_EPG_GRAB_NONET=1`:
  `/usr/bin/unshare -rn` prefixed to the spawn; no route, loopback down; unprivileged, no sudo): its start-up as today
  (busiest core 79-86 %), its first DNS lookup fails, nothing leaves the host (`ok` = false is not checked for C; the
  spawn returns after ~2.4 s instead of ~2.9).

**E3-A2's validity rule, applied to the sessions:** B's first session had a `client_output_silence` pause at 04:20:18Z
and C's first a `controller_silence` false pause at 04:25:49Z (then `gave_up_saved` 04:27:49, paused for ~2/3 of its
triggers). Both are INVALID, reported here, and were replaced (B_r1, C_r1); the reading uses A, B_r1, C_r1.

| session | valid | 0-2 s loss, lost pkt/s | baseline loss/s | aligned loss 0..5 s | busiest core % 0..4 s | eno1 rx kB/s 0..4 s | spawn wall s (median) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | yes | **39.773** | 1.639 | [9.6, 46.08, 63.64, 49.48, 12.24, 2.83] | [30.17, 77.33, 77.75, 28.49, 27.07] | [36.65, 33.3, 36.65, 48.6, 39.81] | 2.9135 |
| B | **no** (desync_pause) | **44.89** | 10.247 | [29.2, 52.45, 53.02, 12.33, 14.7, 14.88] | [24.82, 39.46, 42.15, 28.71, 26.5] | [35.53, 35.19, 35.06, 49.96, 40.77] | 2.923 |
| C | **no** (desync_pause) | **1.883** | 1.694 | [0.25, 2.49, 2.91, 1.57, 1.05, 0.42] | [17.86, 21.7, 76.67, 80.55, 29.54] | [36.28, 37.12, 37.65, 38.34, 40.96] | 2.3449999999999998 |
| B_r1 | yes | **3.563** | 1.541 | [1.02, 4.25, 5.42, 2.31, 2.04, 0.25] | [23.96, 38.31, 40.23, 25.86, 23.43] | [35.03, 38.76, 36.79, 50.91, 41.74] | 3.289 |
| C_r1 | yes | **3.07** | 1.962 | [1.32, 2.46, 5.43, 3.64, 0.0, 2.02] | [27.61, 79.19, 86.25, 31.11, 26.77] | [34.85, 35.56, 37.73, 37.2, 39.01] | 2.413 |

**The reading (the task's rule): A 39.8; B_r1 3.563 and C_r1 3.07, both <= 25 % of A -> the probe names BOTH -> the
change is the network one** ("both -> the network one, since E3-S1 already measured the CPU one").

Read beside the rule:

- The arms are sequential sessions (A 04:06-04:12, B_r1 04:31-04:38, C_r1 04:40-04:46) and A was not repeated: the
  link's drift between sessions is a confound. The invalid first B session, on a lossy link (baseline 10.2 lost/s),
  showed **no** reduction (44.9 vs A's 39.8); the valid B_r1, on a quiet one, did.
- In C the CPU burst is fully there (busiest core 79-86 % at +1..+2 s) and the loss is not: CPU contention **alone**
  does not produce the peak. In A the child's download is small (eno1 rx +12 kB/s at +3 s).
- The grabber sleeps 3 s (the epg-grabber library's default) before each request, so the request lands ~+3 s; the
  heartbeat loss series smears by ±1-2 s, so a loss peak "at +1-2 s" is consistent with that request (and its DNS
  lookup) rather than the start-up. This is an inference; nothing on the host times the child's sockets.
