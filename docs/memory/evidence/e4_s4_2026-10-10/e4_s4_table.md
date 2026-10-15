# E4-S4 — grab deferral while streaming: the table

| | control (PS1-STREAM, no flag) | CONC + flag r1 | CONC + flag r2 | CONC + flag at 150 % |
| --- | --- | --- | --- | --- |
| host_cpu | 11.84 | 12.4 | 11.7 | 10.8 |
| companion_cpu | 25.28 | 25.32 | 25.74 | 24.95 |
| rendered_fps | 59.38 | 58.6 | 58.92 | 58.07 |
| loss_per_min | 147.71 | 529.97 | 364.04 | 817.01 |
| resyncs | 5 | 26 | 5 | 47 |
| underruns | 14 | 27 | 50 | 32 |
| samples_with_epg_child | 0 | 0 | 0 | 0 |
| grabs_run_in_window | 0 | 0 | 0 | 0 |
| deferred_rows | 0 | 240 | 240 | 240 |
| deferred_pending_max | 0 | 6 | 6 | 6 |
| client_pauses | 0 | 2 | 0 | 2 |
| controller_pauses | 0 | 0 | 0 | 0 |
| socket_w | 20.01 | 19.7 | 21.81 | 20.92 |
| usage_cores | 0.97 | 1.02 | 0.99 | 0.96 |
| throttled_s | None | None | None | 0.0 |
| drain (queued / ok / failed / s) | — | 6 / 6 / 0 / 32.66 | 6 / 6 / 0 / 33.44 | 6 / 6 / 0 / 35.68 |

**Verdict: REJECTED (a, d)**

```
{
 "comparability": {
  "control_host_cpu": 11.842,
  "control_rendered": 59.385,
  "holds": true
 },
 "clauses": {
  "a": false,
  "b": true,
  "c": true,
  "d": false,
  "e": true
 }
}
```
