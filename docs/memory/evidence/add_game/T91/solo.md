# T91 — solo: PASS

Written by `tools/party_add_game.py` (B157). Every cell as read / bar / met; no title, id or path.

| cell | read | bar | met |
| --- | --- | --- | --- |
| the mini game played was this title | {"another": 0, "this title": 1} | "this title >= 1, another 0" | yes |
| planned switches | 4 | ">= 4 (a practice in and out, the go, the end)" | yes |
| every planned switch switched | true | true | yes |
| every planned switch's seconds | [1.074, 1.082, 1.18, 1.072] | "<= 1.6" | yes |
| the real match's go and end read for S (a practice's may be listed) | {"listed": [], "read": ["1 (a practice's)", "2 (a practice's)", "3 (the go)", "4 (the end)"]} | ["the go", "the end"] | yes |
| S: sound within 4 s of each switch, underruns rising <= 20 a row | [true, true, true, true] | "all" | yes |
| audio_max_arrival_gap_ms at each switch | [331, 65, 432, 325] | "<= 1200" | yes |
| the band in the practices' encoder lines only | [1, 1] | "band lines = practices >= 1" | yes |
| keys_written | true | true | yes |
| the board's lines in order | ["cards", "practice", "load screen again", "start", "scores"] | ["cards", "practice", "load screen again", "start", "scores"] | yes |
| the board showed one card | 1 | 1 | yes |
| the hub's result = the winner the user named | 1 | 1 | yes |
