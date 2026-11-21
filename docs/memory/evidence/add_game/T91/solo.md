# T91 — solo: FAIL

Written by `tools/party_add_game.py` (B157). Every cell as read / bar / met; no title, id or path.

| cell | read | bar | met |
| --- | --- | --- | --- |
| the mini game played was this title | {"another": 0, "this title": 1} | "this title >= 1, another 0" | yes |
| planned switches | 4 | ">= 4 (a practice in and out, the go, the end)" | yes |
| every planned switch switched | true | true | yes |
| every planned switch's seconds | [1.336, 1.067, 1.227, 1.123] | "<= 1.6" | yes |
| switches read for S (the next starts 4 s or more after) | [3, 1] | ">= 4 read" | **no** |
| S: sound within 4 s of each switch, underruns rising <= 20 a row | [true, false, true] | "all" | **no** |
| audio_max_arrival_gap_ms at each switch | [68, 60, 374] | "<= 1200" | yes |
| the band in the practices' encoder lines only | [1, 1] | "band lines = practices >= 1" | yes |
| keys_written | true | true | yes |
| the board's lines in order | ["cards", "practice", "load screen again", "start", "scores"] | ["cards", "practice", "load screen again", "start", "scores"] | yes |
| the board showed one card | 1 | 1 | yes |
| the hub's result = the winner the user named | 1 | 1 | yes |

Listed, not read (the next switch began less than 4 s after): switch 2 (to the board, 1.067 s; the next began 2.3 s after).
