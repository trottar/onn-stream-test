# H7-V2 — the matches (times UTC; A's replies are in the main record)

| match | the characters (the user said none; the kept pictures, labels only) | the hub's class and when it said it | select screen back (first kept picture) → `ended` | the user's "back" | the user's line (verbatim) | met |
| --- | --- | --- | --- | --- | --- | --- |
| M1 (P1 asked to win) | two characters, neither of the saved pair (A / B): C (P1) and D (P2) | **never `ended`** — `watching`, class `other` at every read (237 reads to 03:36:23.6Z); the select screen at 01 – 00 read at screen distance 20.16 against the threshold 14.66 | 03:35:30.3Z → none (30 s after "back" passed at 03:36:07.7Z) | 03:35:37.7Z | "Player 1" | **not met** |
| M2 (P2 asked to win) | two characters, neither of the saved pair nor match 1's: E (P1) and F (P2) | **never `ended`** — `watching`, `other` at every read (160 reads to 03:40:36.0Z); the select screen at 00 – 01 read at 20.21 | 03:39:56.3Z → none (30 s passed at 03:40:33.0Z) | 03:40:03.0Z | "Player 2, I mean it's clearly broken. You need to diagnose this first, I'm not playing when it doesn't work" | **not met** |
| M3 (a mirror match) | — | — | — | — | — (not played: the user stopped the sitting) | **not played** |

- **Starts:** M1 `h7-start` 03:32:25.5Z → `started`, `loaded` true, `load_line_ms` 47.1; the first result `watching`,
  `seen_start` true. M2's first `h7-start` 03:36:55.4Z → **400 "a mini game is already being watched"** (M1's watch
  never ended, and B103 frees it only on `ended` or the game's stop — the line's "POST the start again" cannot work after
  a match the hub missed). A gave the retry step (END, launch again, Start Fresh, join); the second start 03:37:55.4Z →
  `started`, `loaded` true, 57.8 ms; `watching`, `seen_start` true.
- **Never during a fight:** held trivially — no `ended` row at all (`h7_results.jsonl`: refused, loaded, watching,
  refused, stopped, loaded, watching, stopped).
- **What the watcher read during the fights and the "wins" lines:** `other` throughout; **no `unknown` read** in the
  sitting (516 class reads, all `other`); the fights' screen distances 22-150, the select screen's 19.2-20.2 — every
  read, the select screen included, above the threshold.
- **How long after the select screen returned `ended` was said:** never.
