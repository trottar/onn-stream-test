# H7-V6b — the window's pictures (B142's grab, once a second, from each `minigame_launch` / `minigame_practice_end` row to its go) — in the git-ignored `runtime/h7v6b_frames/`, never in git

| preparation | files | first / last grab | result |
| --- | --- | --- | --- |
| T88 step 5 (seats 1,2, held) | **none** (179 tries) | 02:14:16.449Z / 02:17:20.698Z | no_window |
| T88 step 6 (seats 2,1, go before ready) | `s6_001.png` - `s6_001.png` (1) | 02:18:11.138Z / 02:18:11.138Z | ok |
| T88 step 8 (seats 1,2, held) | `s8a_001.png` - `s8a_003.png` (3) | 02:18:25.555Z / 02:18:27.790Z | ok |
| T88 step 8, the way back after practice 1 | `s8b_001.png` - `s8b_003.png` (3) | 02:19:58.537Z / 02:20:00.892Z | ok |
| T88 step 8, the way back after practice 2 | `s8c_001.png` - `s8c_003.png` (3) | 02:21:31.642Z / 02:21:34.014Z | ok |
| T89 step 9 (seats 3,1,4,2, held) | `s9a_001.png` - `s9a_003.png` (3) | 02:22:00.040Z / 02:22:02.234Z | ok |
| T89 step 9, the way back after its practice | `s9b_001.png` - `s9b_003.png` (3) | 02:23:32.586Z / 02:23:34.799Z | ok |

**Step 5's 179 grabs found no window** (02:14:16-02:17:20Z): A's monitor ran without `DISPLAY`, so `xdotool search` answered nothing and no picture was written; A restarted the monitor with `DISPLAY=:0` before step 6 (`notes.txt`); step 5 was not run again (no retry). Every later preparation has its pictures. None missed its start, so none was looked at (B142: looked at only if a preparation misses). `git check-ignore -v` → `check_ignore.txt`.
