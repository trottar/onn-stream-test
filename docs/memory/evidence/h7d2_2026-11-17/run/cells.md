# H7-D2 — the cells (`preregistration.md`, sha256 `23d1dc16…`, hashed 23:41:23Z; the passes 23:41:39-23:45:41Z, unattended)

| cell | what was read | met |
| --- | --- | --- |
| **L** — the launches | pass P: both titles launched by the cheat query, `cheat_session.profile_id` the title's setup; each stopped (`stop` 200), RetroArch gone. Pass Q: each `minigame_launch` under the setup (the board's own path); each mini game ended; the board quit (F10, exit 0). Nothing left running | **met** |
| **D** — the loads | each `h7-start` answered `"begin": "setup"`, loaded (21.6 / 57.2 ms); the N64 load into a core answering PAUSED (after the launch: `PAUSED`, 0 toggles); every segment's status word recorded — **PAUSED after S0-S5 and S6's pause, PLAYING in S7, for both titles** (no `PLAYING` before S6) | **met** |
| **K** — the pictures | pass P's keep folders: T88 **74** pictures / 74 rows, T89 **74** / 74 (≥ 55 each; git-ignored) | **met** |
| **U** — nothing touched | 228 files before = after (every name and sha256); no `.state8`; the rules folder before = after; no in-game save changed (recorded) | **met** |

**MET** — L, D, K and U: the pictures and reads exist. What they show (`findings.md`) is for Cowork and B.
