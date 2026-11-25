# T92 — solo: PASS

Written by `tools/party_add_game.py` (B157). Every cell as read / bar / met; no title, id or path.

| cell | read | bar | met |
| --- | --- | --- | --- |
| the mini game played was this title | {"another": 0, "this title": 2} | "this title >= 1, another 0" | yes |
| planned switches | 5 | ">= 4 (a practice in and out, the go, the end)" | yes |
| every planned switch switched | true | true | yes |
| every planned switch's seconds | [1.173, 1.32, 1.068, 1.141, 1.284] | "<= 1.6" | yes |
| the real match's go and end read for S (a practice's may be listed) | {"listed": [], "read": ["1 (a practice's)", "2 (a practice's)", "3 (a practice's)", "4 (the go)", "5 (the end)"]} | ["the go", "the end"] | yes |
| S: sound within 4 s of each switch, underruns rising <= 20 a row | [true, true, true, true, true] | "all" | yes |
| audio_max_arrival_gap_ms at each switch | [376, 572, 321, 391, 532] | "<= 1200" | yes |
| the band in the practices' encoder lines only | [1, 1] | "band lines = practices >= 1" | yes |
| keys_written | true | true | yes |
| the board's lines in order | ["cards", "practice", "load screen again", "start", "scores"] | ["cards", "practice", "load screen again", "start", "scores"] | yes |
| the board showed one card | 1 | 1 | yes |
| the hub's result = the winner the user named | 1 | 1 | yes |
