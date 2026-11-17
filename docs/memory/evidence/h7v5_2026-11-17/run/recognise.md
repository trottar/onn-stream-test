# H7-V5 — the seconds from each start's load to `recognised` (the `h7_results` rows; change 4)

| mini game | start (`minigame_start`) | the setup's begin loaded (`loaded` / `watching`, `"begin": "setup"`) | load line | `recognised` | seconds from the load | the window's last read |
| --- | --- | --- | --- | --- | --- | --- |
| **T88**, seats 1,2 (step 12) | 05:42:34.877Z | 05:42:35.828Z, spec version 2 | 27.1 ms, `.state8` under T88's setup's `states/` | **false** (05:42:43.843Z) | **8.0 s** (the hub's `recognise_s` 8.0; 8 reads) | class `other`, screen distance **0.0916** (the spec's `screen_threshold` 0.082) |
| **T89**, seats 1,2,3,4 (step 16) | 05:43:06.85Z | 05:43:08.632Z, spec version 3 | 56.1 ms | **false** (05:43:16.648Z) | **8.0 s** (8 reads) | class `other`, distances start **0.3175** (the spec's start threshold 0.0932), end / screen 0.1806 |

Both starts given up by the hub ("the title's start screen was not recognised"; `minigame_given_up` 05:42:43.881Z and
05:43:17Z); per change 4 each title was stopped there with `party-minigame-end` (the board kept), **no retry**.

**The cause, as far as the rows go:** neither title's start screen was recognised within the hub's 8-s window under a
cheat setup — B's named risk (B126: on H7-C2's run the first start read came 6.97 s after the load, RetroArch's notices
over the screen). T88's last read was near its threshold (0.0916 against 0.082); **T89's was far from its start
(0.3175 against 0.0932)** — more than the notices alone would explain on their own; no picture was kept in this task,
so what the window showed is not read. Not diagnosed further (no new code, no retry).
