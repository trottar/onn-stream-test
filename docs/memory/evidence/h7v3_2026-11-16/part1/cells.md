# H7-V3 part 1 — the pre-registered cells (`preregistration.md`, sha256 `d649ebb7…`, hashed 15:07:12Z)

| cell | what was read | when (UTC) | met |
| --- | --- | --- | --- |
| **The spec** | learn: every class separable; screen 0.0902; start 0.1007 / end_P1 0.1032 / end_P2 0.0990; margin needed 0.0929; masks 13,756 / 97 px; `unlike_label` 3 / 4 / 5; version 2. Score: H7-V1 788 + 72 + 74 + 218 = 1,152 / 1,152; live 70 + 113 + 98 + 214 = 495 / 507, the 12 others `unknown` (3 / 4 / 5); `other_read_as_screen` 0. Replay K = 3: `ended` end_P1 153.03 s (screen from 151.02), end_P2 420.03 s (from 418.03) | 15:02:59-15:05Z | **met** (= B104's arrangement 3 in every number) |
| **R — recognised** | never reached: no start could be made — `h7-start?keep=1` → 400 "the stream is not up" | 15:08:47Z | **not met** (no start, no `recognised` row) |
| **E1 — end P1** | never reached (no watch; the state not loaded) | — | **not met** (not run) |
| **E2 — end P2** | never reached | — | **not met** (not run) |
| **F — mid-fight** | never reached | — | **not met** (not run) |
| **S — stop and replace** | never reached as a cell (`h7-stop` with no watch → `{"ok": true, "watch": "none"}` at stage 1 only; 0 `replaced` rows) | 15:05:52Z | **not met** (not run) |
| **G — the game** | launched **paused** by the launch itself (by design); `native-stream-start` 503 (the opus gate, adopted line 8); `native-stream-ready` 503 "Native stream is not active; gameplay remains paused." — the game never ran unpaused; status every 10 s: 6 reads active + paused (15:08:03-15:08:53Z), none ended by the hub; stopped by A's call 15:08:53.653Z; `launch_orphaned` 2 → 2 | 15:07:55-15:09:03Z | **not met** — the game could not be kept running unpaused with no client (`code_read.md`); not ended or paused by the hub beyond the launch's own pause; `launch_orphaned` unchanged |
| **U — nothing of the user's touched** | saves: 161 before = 161 after, the full listing (every name and sha256) identical; T88's 4 files unchanged, slots 1-3 none; **no `.state8` anywhere** after; the drive before = after; no profile changed | 15:06:47Z / 15:09:10Z | **met** |

**Verdict: NOT MET** — stopped at B's step 8 by change 3's own clause: with the eighteen adopted lines, a stream to
nobody cannot start from loopback (adopted line 8 needs the client's signed opus declaration), so the pause cannot be
released and the watcher refuses to start. `last`'s distances: none — the watcher never read a picture.
