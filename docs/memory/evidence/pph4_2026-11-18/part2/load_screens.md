# The load screens (rows; seconds from the go's hold)

| mini game | practices (by, s) | ready after each (`after_practice`, prepare_s) | real go's held_s | PAUSED watch → go |
| --- | --- | --- | --- | --- |
| X1 T89 | select_button 16.249 | true 1.224 | 4.582 | 4/4, 5/5 |
| X2 T89 | select_button 21.258 | true 1.228 | 6.215 | 1/1, 7/7 |
| D1 T88 | select_button 26.866; select_button 22.718 | true 1.200; true 1.184 | 12.642 | 4/4, 36/36, 13/13 |
| D2 T88 | select_button 12.889 | true 1.199 | 2.903 | 2/2, 3/3 |

First ready `prepare_s` 1.317 / 1.327 (T89), 1.311 / 1.308 (T88); frame advance T89 0 frames ~185-198 ms mute, T88 2
frames ~338-372 ms, after a T88 practice 14 frames ~1150 ms. `load screen again` 5 in the board's log, one a practice.
No `minigame_ended` inside a practice. **Every practice left by Select; none by time** (part 1's by time, 90.001 s).
