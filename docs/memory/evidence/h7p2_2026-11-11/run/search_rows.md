# The search with hints (2026-11-11 20:13:19-20:14:06Z; `tools/h7_rule_search.py --system ps1 --states <3 states> --hints <T88's cached list> --time`)

| row | value |
| --- | --- |
| the states | begin (null), end P1, end P2 — 2 players |
| read / search seconds | 44.25 / 3.07 |
| `unstable_bytes` | 0 |
| the hints (counts) | codes 12, read 6; by player and kind {"P1": {"other": 1, "level": 2}, "P2": {"other": 1, "level": 2}} |

| template | count | families_found | passing_count | evidence | folds run / skipped |
| --- | --- | --- | --- | --- | --- |
| (a) a per-player counter | 8520 | 6304 | 6304 | weak | 0 / 2 |
| (b) a per-player level that empties | 3084 | 2392 | 2392 | weak | 0 / 2 |
| (c) a single winner field | 2457 | 2010 | 2010 | weak | 0 / 2 |
| (b2) a per-player level, the winner's the larger | None | None | 0 | none | 0 / 2 |
| (h) a hinted pair, tested directly | 2 | 1 | 1 | weak | 0 / 2 |

`hinted_sets`: found 3, tested 3, **hold 2**, fail 1.

| `evidence` | **weak** |
| --- | --- |
| `decided` | **False** |
| `template` | None |
| `would_make_strong` | "one more 'end' won by P1 and one more 'end' won by P2" |

((b2) not testable: "too many (b2) candidates to rank: more than 200,000 — the template cannot decide here")

## Every hinted set (the game's own cheat list's per-player addresses)

| # | addresses P1 / P2 | width | kind | holds | values: begin / end P1 / end P2 | failing states |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0xa961e / 0xaaeaa | 1 | level | True | [0, 0] / [140, 70] / [133, 140] | — |
| 2 | 0xa961e / 0xaaeaa | 2 | level | True | [0, 0] / [140, 70] / [133, 140] | — |
| 3 | 0xb8b94 / 0xb8b74 | 2 | other | False | [0, 0] / [0, 0] / [0, 0] | end P1, end P2 |

## The top five passing families per template (values: begin / end P1 / end P2)

**(a) a per-player counter:**

| # | address(es) | width | members | hinted | values |
| --- | --- | --- | --- | --- | --- |
| 1 | 0xaa079 / 0xaa07d | 1 | 1 | False | [0, 0] / [5, 0] / [0, 12] |
| 2 | 0xaabc6 / 0xaabca | 1 | 1 | False | [0, 0] / [1, 0] / [0, 7] |
| 3 | 0xcde42 / 0xcde46 | 1 | 1 | False | [0, 0] / [10, 6] / [4, 6] |
| 4 | 0xe40db / 0xe40df | 1 | 5 | False | [0, 0] / [3, 0] / [3, 16] |
| 5 | 0xe43b3 / 0xe43b7 | 1 | 1 | False | [0, 0] / [3, 0] / [3, 16] |

**(b) a per-player level that empties:**

| # | address(es) | width | members | hinted | values |
| --- | --- | --- | --- | --- | --- |
| 1 | 0xa9d6e / 0xa9d72 | 2 | 6 | False | [65535, 65535] / [65535, 0] / [0, 65535] |
| 2 | 0xa9f4a / 0xa9f4e | 2 | 12 | False | [65535, 65535] / [65535, 0] / [0, 65535] |
| 3 | 0xc9902 / 0xc990a | 1 | 1 | False | [255, 255] / [18, 0] / [0, 28] |
| 4 | 0xc992a / 0xc9932 | 1 | 1 | False | [255, 255] / [18, 0] / [0, 12] |
| 5 | 0xc994a / 0xc9952 | 1 | 1 | False | [255, 255] / [46, 0] / [0, 222] |

**(c) a single winner field:**

| # | address(es) | width | members | hinted | values |
| --- | --- | --- | --- | --- | --- |
| 1 | 0x9bd63 | 1 | 2 | False | 2 / 0 / 1 |
| 2 | 0xa9bef | 1 | 1 | False | 251 / 0 / 1 |
| 3 | 0xaa201 | 1 | 1 | False | 249 / 0 / 1 |
| 4 | 0xaa205 | 1 | 1 | False | 248 / 0 / 1 |
| 5 | 0xaa61d | 1 | 1 | False | 249 / 0 / 1 |

**(b2) a per-player level, the winner's the larger:** none passing.

**(h) a hinted pair, tested directly:**

| # | address(es) | width | members | hinted | values |
| --- | --- | --- | --- | --- | --- |
| 1 | 0xa961e / 0xaaeaa | 2 | 2 | True | [0, 0] / [140, 70] / [133, 140] |

RetroArch processes after the search: 0.
