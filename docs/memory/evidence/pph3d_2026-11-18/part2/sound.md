# PP-H3d — S: the sound after every planned switch (the onn's heartbeat rows after N_HB, beside the party rows; numbers only)

Rule (pre-registered): a row with `audio_queue_depth` > 0 within 4 s after T, and from that row to the next switch's start (its T − its `seconds`) `audio_underruns` rising ≤ 20 per row. Every row: `heartbeat_audio.tsv`.

| # | switch | T | `seconds` | first row with depth > 0 | rows to the next switch's start | underruns a row, max | `audio_lost_packets` | met |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | the self-proof: to the title | 06:58:15.403Z | 3.512 | **none within 4 s** (rows +1.6 s and +3.6 s: depth 0) — the next switch began 1.5 s after T | — | — | — | **no (as written)** |
| 2 | the self-proof: back to the board | 06:58:20.427Z | 3.53 | +0.8 s (depth 10) | 17 | 0 | 0 | yes |
| 3 | into the practice | 06:58:56.461Z | 1.964 | +1.0 s (depth 7) | 11 | 1 | 0 | yes |
| 4 | the practice's way back to the board | 06:59:19.996Z | 1.877 | +1.6 s (depth 9) | 35 | 2 | 0 | yes |
| 5 | into the real match | 07:00:33.559Z | 1.864 | +0.6 s (depth 2) | 53 | 2 | 0 | yes |
| 6 | the real match's end back to the board | 07:02:22.154Z | 1.769 | +0.8 s (depth 3) | 117 | 3 | 0 | yes |

**Switch 1** is the self-proof's: the title was ended by A's `party-minigame-end` 1.0 s after `playing`, so the switch back to the board began 1.5 s after T — before any row could show the title's sound (B143: the switch's own gap of no sound is up to its `seconds`). Read as written, S is not met on it. Every switch the user played through (3-6) and the self-proof's way back (2): sound within 0.6-1.6 s, at most 2 underruns a row, 0 lost. `audio_rx_packets` ~100 / s throughout.
