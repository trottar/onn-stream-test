# The search with hints on five states (2026-11-11 20:29:36Z-20:31:13Z; `tools/h7_rule_search.py --system ps1 --states <5 states> --hints <T88's cached list> --time`)

| row | value |
| --- | --- |
| the states | begin (null), end P1, end P2, end P1 b (mid-fight, P1 ahead), end P2 b (mid-fight, P2 ahead) — 2 players |
| read / search seconds | 74.48 / 22.31 |
| `unstable_bytes` | 0 |
| the hints (counts) | codes 12, read 6; by player and kind {"P1": {"other": 1, "level": 2}, "P2": {"other": 1, "level": 2}}; skipped {"no player": 6} |

| template | count | families_found | passing_count | evidence | folds run / skipped |
| --- | --- | --- | --- | --- | --- |
| (a) a per-player counter | 628 | 491 | 453 | strong | 4 / 0 |
| (b) a per-player level that empties | 207 | 165 | 165 | strong | 4 / 0 |
| (c) a single winner field | 62 | 55 | 37 | strong | 4 / 0 |
| (b2) a per-player level, the winner's the larger | 162274 | 29972 | 29382 | strong | 1 / 3 |
| (h) a hinted pair, tested directly | 2 | 1 | 1 | strong | 4 / 0 |

`hinted_sets`: found 3, tested 3, **hold 2**, fail 1.

| `evidence` | **strong** |
| --- | --- |
| `decided` | **True** |
| `template` | **h** (the hinted pair) |
| `would_make_strong` | None |
| the acceptance rule (pre-registered) | strong AND template h → **accepted** |
| `rule` | P1 0xa961e / P2 0xaaeaa, 2 bytes little, winner `max`, none when `equal` |
| `also_fits` (each template's top) | a: 0xe4247 / 0xe424b; b: 0xe33af / 0xe33bf; c: 0xbf63f; b2: 0xd0914 / 0xd0918 |

(b2): strong: every winner seen has at least two 'end' states; 29382 families pass all 1 folds; the answer is the top one — only 1 of 4 folds ran (3 skipped), the loose template B97 notes; by the acceptance rule a non-hinted (b2) answer would count as "weak" — it is not the answer here.

## Every hinted set (the game's own cheat list's per-player addresses), values in all five states

| # | addresses P1 / P2 | width | kind | holds | values: begin / end P1 / end P2 / end P1 b / end P2 b | failing states |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0xa961e / 0xaaeaa | 1 | level | True | [0, 0] / [140, 70] / [133, 140] / [140, 100] / [110, 140] | — |
| 2 | 0xa961e / 0xaaeaa | 2 | level | True | [0, 0] / [140, 70] / [133, 140] / [140, 100] / [110, 140] | — |
| 3 | 0xb8b94 / 0xb8b74 | 2 | other | False | [0, 0] / [0, 0] / [0, 0] / [0, 0] / [0, 0] | end P1, end P2, end P1 b, end P2 b |

## The top five passing families per template (values: begin / end P1 / end P2 / end P1 b / end P2 b)

**(a) a per-player counter:**

| # | address(es) | width | members | hinted | values |
| --- | --- | --- | --- | --- | --- |
| 1 | 0xe4247 / 0xe424b | 1 | 2 | False | [0, 0] / [3, 0] / [3, 16] / [3, 0] / [3, 4] |
| 2 | 0xe43b3 / 0xe43b7 | 1 | 1 | False | [0, 0] / [3, 0] / [3, 16] / [3, 0] / [3, 12] |
| 3 | 0xa0529 / 0xa053d | 1 | 1 | False | [0, 0] / [17, 0] / [0, 4] / [3, 0] / [0, 2] |
| 4 | 0xa054d / 0xa0561 | 1 | 1 | False | [0, 0] / [16, 0] / [0, 4] / [4, 0] / [0, 2] |
| 5 | 0xdcd6e / 0xdcd86 | 1 | 1 | False | [1, 1] / [18, 13] / [18, 22] / [24, 13] / [0, 13] |

**(b) a per-player level that empties:**

| # | address(es) | width | members | hinted | values |
| --- | --- | --- | --- | --- | --- |
| 1 | 0xe33af / 0xe33bf | 1 | 1 | False | [255, 255] / [48, 0] / [0, 255] / [16, 0] / [0, 255] |
| 2 | 0xe33ab / 0xe33bf | 1 | 1 | False | [255, 255] / [16, 0] / [0, 255] / [4, 0] / [0, 255] |
| 3 | 0xab3da / 0xab402 | 2 | 3 | False | [65535, 65535] / [65535, 0] / [0, 65535] / [65535, 0] / [0, 65535] |
| 4 | 0xab3da / 0xab446 | 2 | 3 | False | [65535, 65535] / [65535, 0] / [0, 65535] / [65535, 0] / [0, 65535] |
| 5 | 0xab3da / 0xab48a | 2 | 3 | False | [65535, 65535] / [65535, 0] / [0, 65535] / [65535, 0] / [0, 65535] |

**(c) a single winner field:**

| # | address(es) | width | members | hinted | values |
| --- | --- | --- | --- | --- | --- |
| 1 | 0xbf63f | 1 | 1 | False | 151 / 0 / 1 / 0 / 1 |
| 2 | 0xbf647 | 1 | 1 | False | 255 / 0 / 1 / 0 / 1 |
| 3 | 0xbf727 | 1 | 1 | False | 31 / 0 / 1 / 0 / 1 |
| 4 | 0xc1893 | 1 | 1 | False | 221 / 0 / 1 / 0 / 1 |
| 5 | 0xc189b | 1 | 1 | False | 16 / 0 / 1 / 0 / 1 |

**(b2) a per-player level, the winner's the larger:**

| # | address(es) | width | members | hinted | values |
| --- | --- | --- | --- | --- | --- |
| 1 | 0xd0914 / 0xd0918 | 1 | 1 | False | [255, 255] / [228, 73] / [108, 151] / [212, 97] / [108, 155] |
| 2 | 0xd1804 / 0xd1808 | 1 | 2 | False | [246, 246] / [199, 94] / [73, 94] / [118, 94] / [57, 94] |
| 3 | 0xe2aa0 / 0xe2aa4 | 2 | 10 | False | [65535, 65535] / [8559, 4487] / [1979, 59255] / [461, 254] / [1553, 64089] |
| 4 | 0xe2aca / 0xe2ace | 2 | 22 | False | [65535, 65535] / [32784, 0] / [32784, 65535] / [32784, 0] / [32795, 65535] |
| 5 | 0xe2d45 / 0xe2d49 | 1 | 1 | False | [255, 255] / [33, 17] / [7, 231] / [1, 0] / [6, 250] |

**(h) a hinted pair, tested directly:**

| # | address(es) | width | members | hinted | values |
| --- | --- | --- | --- | --- | --- |
| 1 | 0xa961e / 0xaaeaa | 2 | 2 | True | [0, 0] / [140, 70] / [133, 140] / [140, 100] / [110, 140] |

RetroArch processes after the search: 0.
