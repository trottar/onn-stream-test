# PP-H2 — the cells (`preregistration.md`, sha256 `77dbedb8…`, hashed 17:46:43Z)

The user's lines verbatim with their times: `user_lines.txt` ("ready" 17:48:17Z; "paused" 17:50:34Z; "Each pad works as
expected" 17:51:54Z; "ended" 17:52:36Z; "ended" 17:54:39Z). The party rows: `party_rows.jsonl` / `party_rows_readable.txt`.

| cell | what was read | when (UTC) | met |
| --- | --- | --- | --- |
| **C** — the board's checks | 25 of 25 PASS, exit 0 (the board's HEAD `d774402d`; step 19 130 assertions) | 17:35:44-17:45:22 | **met** |
| **W** — the window (stage 1's own launch) | found by class PrivyParty in 0.79 s, its pid the board's; **1920 × 1080 at 0, 0**, `_NET_WM_STATE_FULLSCREEN` | 17:45:34 | **met** |
| **A** — the sound (stage 1) | one sink-input with the board's pid (1 of 1); `audio` row `sink_input` true | 17:45:35 | **met** |
| **D** — the pads (stage 1) | `pads` row P1-P4 in event order (11, 12, 13, 14); A's headless line: devices 0-3 = P1-P4 | 17:45:35 | **met** |
| **Q** — the quit (stage 1) | `stop` → `quit` F10 → `exited` code 0 in 0.31 s; `party_exit` "quit 0"; no `sigterm` row | 17:46:03 | **met** |
| **P** — each pad its own seat | the sitting's `pads` row P1-P4 in event order 11-14 (P1 = device 0, P2 = device 1) at 17:47:54Z (and again at 17:52:57Z under Mobile); the onn's `pad_slots` P1 = slot 0, P2 = slot 1; the user: **"Each pad works as expected"** | 17:47:54 / 17:51:54 | **met** |
| **H** — Home / RESUME | Home → `pause` key **Escape** 17:50:26.308Z; the status `paused` true from 17:50:27Z; RESUME → `resume` key **Escape** 17:50:52.446Z; `paused` false from 17:50:52Z. (Run 2: Home → Escape 17:54:24.9Z.) | 17:50:26-17:50:52 | **met** |
| **E** — END | `quit` key **F10** 17:52:27.648Z → `exited` code **0** in 0.41 s; no `sigterm` row. (Run 2 the same: F10 → code 0 in 0.41 s.) | 17:52:27 / 17:54:30 | **met** |
| **S** — the stream | no stall, no recovery row, `launch_orphaned` 2 → 2; fps median **59.8 / 59.8 / 59.6** over the three play sessions (lowest 53.8; none under 50); bitrate 7,000, never acted; 5 packets lost; PRESSURE 4 of 156 samples (`stream_rows.md`) | 17:47:59-17:54:22 | **met** |
| **AU** — sound | the stream's audio packets grew every second of the play: +14,501, +8,700, +7,601, never falling | the play | **met** |
| **U** — nothing of the user's touched | saves 161 = 161, every name and hash; no `.state8`; the pictures folder 116 files, 15,039,288 bytes before = after; the board repo's `git status --short` empty before and after (`--ignored` the same) | 17:37 / 17:54 | **met** |

**Recorded, no bar** (`cpu_gpu.md`): encoder 38 % / 38 % / 38 %, Godot 22 % / 22 % / 19 %, graphics busy 21 % / 23 % /
27 % (Compatibility to Home, after RESUME; Mobile). The joins by the rows: 5.1 s, after RESUME 4.5 s, 4.6 s. SAVE /
LOAD: not pressed (no refusal row).

**Verdict: MET** — C, W, A, D, Q, P, H, E, S, AU and U all met.
