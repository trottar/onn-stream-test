# H7-V6b — the hand loads (B128 step 13 / 17; the scratch `.state8` in the setup's own states folder, removed right after the load reply)

| step | kept state | core | `GET_STATUS` before → at the load | the reply | load line (ms) | bytes | the line names the scratch | scratch removed | `.state8` after |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s5 02:17:23.877Z | end_p1 | ps1 | — (PS1: playing) | `LOAD_STATE_SLOT 8` (16.5 ms) | 57.3 | 16777240 | True | True | 0 |
| s6 02:18:15.238Z | end_p2 | ps1 | — (PS1: playing) | `LOAD_STATE_SLOT 8` (7.8 ms) | 48.9 | 16777240 | True | True | 0 |
| s8 02:18:31.289Z | end_p1 | ps1 | — (PS1: playing) | `LOAD_STATE_SLOT 8` (6.1 ms) | 46.8 | 16777240 | True | True | 0 |
| s8 02:21:37.627Z | end_p1 | ps1 | — (PS1: playing) | `LOAD_STATE_SLOT 8` (4.6 ms) | 45.2 | 16777240 | True | True | 0 |
| s9 02:23:38.801Z | results_1 | n64 | PLAYING → PAUSED (`PAUSE_TOGGLE`; resumed after: PLAYING) | `LOAD_STATE_SLOT 8` (14.9 ms) | 35.2 | 16793440 | True | True | 0 |

An N64 load only after `GET_STATUS` answered `PAUSED` that second (the loader sends nothing otherwise). No other `.state8` was written; none under `data/` or `runtime/` at the close.
