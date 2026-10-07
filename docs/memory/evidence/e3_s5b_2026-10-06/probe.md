# E3-S5B probe — the audio sender's send timing, without and with `=frame` (2026-10-06 23:24-23:29Z)

Measurement before the runs. The trace hook added by this task (`PRIVYHUB_AUDIO_SEND_TRACE=<path>`,
`e3_s5b_send_trace_hook.diff`, measurement only, off) records the `perf_counter_ns` of every `sendto` (original
and duplicate) for 60 s, starting 30 s after the sender starts. `e3_s5b_probe.py` ran two PS1-stream sessions
(E1-PS1-STREAM's launch), first with the trace only, then with the trace + `PRIVYHUB_AUDIO_SENDER_PACING=frame`;
each was torn down by E1's rules (drop-in removed, environ the live default, APK CONFIRMED, PS1 files identical).
Files: `trace_noflag.txt`, `trace_flag.txt`, `probe_*_run.json`, `probe_stats.json`.

| 60 s, 12,000 originals + 12,000 duplicates each | no flag | `=frame` |
| --- | --- | --- |
| gap between originals (ticks), median ms | 4.998 | 4.999 |
| p99 / p99.9 / max ms | 5.19 / 5.47 / 5.95 | 5.52 / 5.72 / **6.63** |
| min ms | 4.17 | **3.37** |
| sd ms | 0.070 | **0.170** |
| gaps > 10 ms / > 20 ms | 0 / 0 | **0 / 0** |
| gaps < 1 ms (two ticks collapsed) | 0 | 0 |
| bunches ≥ 4 datagrams within 0.2 ms each | 0 | **0** |
| bunch sizes (1 / 2 datagrams) | 22 / 11,989 | 36 / 11,982 |

**Before the runs, as the task asks:**

- **The flagged sender shows no gap over 20 ms (none over 10 ms) and no bunch of ≥ 4 datagrams**, at any
  rate. The oversleep-and-bunch mechanism the task names is **not present** at the 60-s scale.
- What `=frame` does change is the jitter: tick spacing sd 0.17 vs 0.07 ms, p99 5.52 vs 5.19 ms. Each
  timed wait wakes up to ~0.6 ms late, and the next tick then comes early (min 3.37 ms) against the
  fixed deadline. This is sub-millisecond, about one tenth of the 5-ms packet period.
- So, if the runs show the flag making loss burstier, the probe does not point to a mechanism at the
  sender. The bar decides either way.
