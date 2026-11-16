# H7-V4 — the matches (the user's lines verbatim in `user_lines.txt`; the watcher's rows in `h7_results.jsonl`)

Characters: **the user named none**; labels from A's look at the kept select-screen pictures only (no names): the saved
fights' pair is A (left) / B (right). Thresholds: screen 0.0902.

| match | the characters as the user described them (labels) | `recognised` | the hub's side and when | seconds from the select screen's first row to `ended` | the user's "back" | the user's line verbatim | met |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M1 (P1 to win) | none described; seen: C vs D — another pair (neither A nor B) | true at 4.0 s (proof 4, 15:43:49.5Z) | **`end_P1` (player 1, the left side) 15:46:14.522Z** | first row under 0.0902 after the fight: 147.00 s (15:46:12.528Z, `end_P1`) → **1.99 s** | 15:46:16.910Z (`ended` 2.4 s earlier) | "Player 1" | **met** |
| M2 (P2 to win) | none described; seen: E vs F — a third pair (none of A-D) | true at 4.0 s (15:46:38.9Z; start 15:46:34.8Z, `replaced` false) | **`end_P2` (player 2, the right side) 15:48:35.890Z** | 119.00 s (15:48:33.896Z, `end_P2`) → **1.99 s** | 15:48:39.058Z (`ended` 3.2 s earlier) | "Player 2" | **met** |
| M3 (mirror) | none described; seen: A vs A — the mirror (the saved fights' left character on both sides) | true at 4.0 s (15:49:00.5Z; start 15:48:56.4Z, `replaced` false) | **`end_P1` (player 1, the left side) 15:50:56.478Z** | 118.00 s (15:50:54.484Z, `end_P1`) → **1.99 s** | 15:50:59.128Z (`ended` 2.7 s earlier) | "Player 1" | **met** |

- **R** (`recognised` true before each match, read before its line): **met** — 4.0 s each, the line given after.
- **Never during a fight: met.** A's look at the one kept picture at each `ended` row: **M1 — the select screen, the
  tally one to nought, the left side's raised; M2 — the select screen, nought to one, the right side's raised; M3 — the
  select screen, one to nought, the left side's raised, the same portrait on both sides.** The kept index of each match:
  `start` (4-44 / 4-17 / 4-17 s), then `other` throughout the fight (102 / 101 / 100 reads; screen 0.135-0.312, never
  under 0.0902, no `unknown`), then the end class from the first row back on the select screen; **no `ended` before it**;
  the only `ended` rows are the three above.
- **The characters the spec never saw:** M1's and M2's four characters and M3's mirror were never in the spec's learning
  pictures as a pair; M3's mirror is the first mirror match seen.
