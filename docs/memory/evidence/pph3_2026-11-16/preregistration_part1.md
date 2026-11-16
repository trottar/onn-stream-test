# PP-H3 part 1 — pre-registration (hashed at the end of stage 1, before part 1's run; unattended, no user)

Task: `handoffs/PP-H3_MINIGAME_FROM_THE_BOARD_TASK.md` — B's §"A — PP-H3" (`SESSION_B_DONE_2026-11-16AP.md`) part 1
steps 1-11 and 13-15, used exactly, with the handoff's changes (**step 12, the 15-minute give-up, not run** — change 1).
T88 = H7's 2-player PS1 title. Both bench flags (`PRIVYHUB_H7=1`, `PRIVYHUB_PARTY=1`) for the task only. Nothing here
adopts anything.

## Stage 1 as read (`pre/`)

This repo at `8bb21700` (queue AP), clean; the board's repo at `820673c` with its two new files committed
(`minigames/hub_minigame.gd` `644f0541…`, `checks/hub_minigame_check.gd` `de4c9db0…`; their `.gd.uid` files not in
it), clean; the two units; no game; eighteen lines; adb up; `--check` ok; the APK `ca53df0d…` CONFIRMED. The sidecar
`<id>.party.json` = `{"players": 2, "scores": {"end_P1": [1, 0], "end_P2": [0, 1]}}` in the rules folder (beside H7-V3's
version-2 spec and the kept begin state); the board's config renderer `gl_compatibility`. Both drop-ins; the companion
restarted 20:16:34Z; **twenty lines** (`PRIVYHUB_H7=1`, `PRIVYHUB_PARTY=1`); the keeper not restarted. Before: 161
save files, no `.state8`; the pictures 116 files / 15,039,288 bytes; both repos clean; `party.jsonl` 27 rows; bitrate
rows 5,751; recovery log 2,264; `launch_orphaned` 2.

## The cells (B's steps, `H` = the games plugin on loopback)

- **P6** — the board launched by the hub itself → `active`, `paused`; `bench-release` → `"released": true`.
- **P7** — `party-minigames` → **one entry, `"players": 2`**.
- **P8** — `party-minigame-start` seats **1,2** with the bench word → `starting`; `party-minigame-result` →
  **`playing`, `recognised` true within 10 s**; the title's window in front (the active window's pid = RetroArch's);
  rows `minigame_route` {"1": 1, "2": 2} and `minigame_stream` "switched": false.
- **P9** — the kept end P1 state brought in by hand (H7-V3 step 10: scratch slot 8, RetroArch's load line, the copy
  removed) → **`ended`, `end_P1`, `scores` exactly [1, 0]** within 8 s.
- **P10** — `party-minigame-end` → `"ended": true`; RetroArch gone; the board's window active again; the status
  `launch_kind` godot; a second end → `"again": true`.
- **P11** — seats **2,1** with the kept end P2 state → **`ended`, `end_P2`, `scores` exactly [0, 1]**; then P10 again.
- **P12** — the 15-minute give-up: **not run** (change 1).
- **P13** — the board's own script (`hub_minigame.gd`) driven headless against the live hub (A's driver off both
  repos, Godot's folders redirected) → its draw line ("a draw: the hub gave it up (the mini game did not start: the
  stream is not up)") and **`DRIVER [0, 0]`**; RetroArch gone after.
- **P14** — the board quit: `stop` → `party_exit` "quit 0" (F10, exit code 0, no `sigterm`).
- **K1** — no board `pause` / `resume` / `quit` row between any `minigame_playing` and `minigame_end` row.
- **U1** — the saves before = after (count and every hash), no `.state8`; the pictures' count and bytes unchanged.

**Part 1 MET** = P6-P11, P13, P14, K1 and U1 all met → part 2's pre-registration hashed, the watchers started, the
sitting's first line (the flags left on). Anything not met → the close and the last reply, one plain sentence on what
failed.
