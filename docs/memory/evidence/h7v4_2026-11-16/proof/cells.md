# H7-V4 — P, the self-proof (on "ready" 15:43:24.869Z; one run 15:43:24.999-15:43:49.540Z, 24.5 s; the user touching nothing)

Rows: `proof.jsonl` (every answer, every `recognised` row, the load step's output, the `ended` rows; ids `<id>`), the
watcher's rows in `../run/h7_results.jsonl`. Thresholds: screen 0.0902; start 0.1007 / end_P1 0.1032 / end_P2 0.0990;
margin 0.0929.

| step | what was read | when (UTC) | bar | met |
| --- | --- | --- | --- | --- |
| 1 — start (keep=1) | 200 `started`, `loaded` true (load line 44.1 ms), `replaced` false; **`recognised` true at 4.0 s** (start 0.092, screen 0.0036, margin 0.134) | 15:43:25.0 → 15:43:29.1 | ≤ 8 s | **met** |
| 2 — end P1 loaded by hand | `LOAD_STATE_SLOT 8` answered in 17.2 ms; RetroArch's load line (16,777,240 bytes, the scratch path) 57.9 ms after the send, **15:43:29.181Z**; the scratch copy removed; watching `start` before the load (no `ended`) → **`ended` `end_P1` 15:43:35.089Z = 5.91 s after the load line** (end_P1 0.0664, end_P2 0.3722, margin 0.170) | 15:43:29.1 → 15:43:35.1 | `end_P1` ≤ 15 s | **met** |
| 3 — start (keep=1) | 200 `started` (`replaced` false — the watch had ended), load line 33.6 ms; **`recognised` true at 4.0 s** | 15:43:35.2 → 15:43:39.3 | ≤ 8 s | **met** |
| 3 — end P2 loaded by hand | answered in 8.1 ms; load line 48.9 ms after the send, **15:43:39.397Z**; the copy removed; watching `start` before the load → **`ended` `end_P2` 15:43:45.299Z = 5.90 s after the load line** (end_P2 0.0733, end_P1 0.3633, margin 0.158) | 15:43:39.3 → 15:43:45.3 | `end_P2` ≤ 15 s | **met** |
| 4 — start (keep=1) | 200 `started`, load line 47.7 ms; **`recognised` true at 4.0 s** — the select screen at 00 – 00, where match 1 starts | 15:43:45.4 → 15:43:49.5 | ≤ 8 s | **met** |

Never the other side (the other end's distance 0.36-0.37 at each `ended`); no `ended` before a load (the watcher
`watching`, class `start`, at each load). **P MET** → match 1's line given.
