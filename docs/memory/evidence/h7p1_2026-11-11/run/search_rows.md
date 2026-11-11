# The search (2026-11-11 16:00:22-16:01:09Z; `tools/h7_rule_search.py --system ps1 --states <3 states> --time`)

| row | value |
| --- | --- |
| the states | begin (null), end P1, end P2 — 2 players |
| read seconds | 44.26 |
| search seconds | 2.66 |
| `unstable_bytes` | 0 |
| template (a) a per-player counter — count | 8520 |
| template (b) a per-player level that empties — count | 3084 |
| template (c) a single winner field — count | 163475 |
| `decided` | **False** |
| `would_split` | "a second 'end' state won by P1" |

## The top five candidates per template, with their values in the three states (begin, end P1, end P2)

Memory addresses are the game's own (RAM offsets), not an identifier.

**(a) a per-player counter:**

| # | address(es) | bytes | values: begin / end P1 / end P2 |
| --- | --- | --- | --- |
| 1 | 0xaa079 / 0xaa07d | 1 | [0, 0] / [5, 0] / [0, 12] |
| 2 | 0xaabc6 / 0xaabca | 1 | [0, 0] / [1, 0] / [0, 7] |
| 3 | 0xcde42 / 0xcde46 | 1 | [0, 0] / [10, 6] / [4, 6] |
| 4 | 0xe40db / 0xe40df | 1 | [0, 0] / [3, 0] / [3, 16] |
| 5 | 0xe4143 / 0xe4147 | 1 | [0, 0] / [3, 0] / [3, 16] |

**(b) a per-player level that empties:**

| # | address(es) | bytes | values: begin / end P1 / end P2 |
| --- | --- | --- | --- |
| 1 | 0xa9d6e / 0xa9d72 | 1 | [255, 255] / [255, 0] / [0, 255] |
| 2 | 0xa9d6e / 0xa9d72 | 2 | [65535, 65535] / [65535, 0] / [0, 65535] |
| 3 | 0xa9d6f / 0xa9d73 | 1 | [255, 255] / [255, 0] / [0, 255] |
| 4 | 0xa9db2 / 0xa9db6 | 1 | [255, 255] / [255, 0] / [0, 255] |
| 5 | 0xa9db2 / 0xa9db6 | 2 | [65535, 65535] / [65535, 0] / [0, 65535] |

**(c) a single winner field:**

| # | address(es) | bytes | values: begin / end P1 / end P2 |
| --- | --- | --- | --- |
| 1 | 0x84c4 | 2 | 3 / 1 / 9 |
| 2 | 0x84c8 | 2 | 36171 / 36169 / 36177 |
| 3 | 0x84c8 | 1 | 75 / 73 / 81 |
| 4 | 0x84cc | 2 | 57512 / 57480 / 57608 |
| 5 | 0x84cc | 1 | 168 / 136 / 8 |

RetroArch processes after the search: 0.
