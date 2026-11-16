# PP-H3b part 1 — pre-registration (hashed at the end of stage 1, before part 1's run; unattended, no user)

Task: `handoffs/PP-H3B_MINIGAME_RETRY_TASK.md` — B's §"A — PP-H3b" (`SESSION_B_DONE_2026-11-16AQ.md`): part 1 as
PP-H3's (B113's steps 6-11 and 13 as PP-H3 ran them; **step 12 not run**; **P14 replaced by P14b**), then **P11b**,
**P14b**, **P15**, with the route watcher from part 1's start. T88 = H7's 2-player PS1 title. Both bench flags
(`PRIVYHUB_H7=1`, `PRIVYHUB_PARTY=1`) for the task only. Nothing here adopts anything. On the bench there is no
stream, so the switch is not run here; part 1 shows the routes stay answered and the calls are taken in order.

## Stage 1 as read (`pre/`)

This repo at `363f538f` (queue AQ), clean; the board's repo at `f1adc44` with B116's two files committed
(`4706a28b…`, `c09036b7…`), clean; the two units; no game; eighteen lines; adb up; `--check` ok; the APK `ca53df0d…`
CONFIRMED. The sidecar and the board's config as PP-H3. Both drop-ins; the companion restarted 21:51:32Z (after HEAD's
commit time); **twenty lines**; the keeper not restarted. Before: 161 save files, no `.state8`; the pictures 116 files /
15,039,288 bytes; both repos clean; `party.jsonl` 84 rows; bitrate rows 5,985; recovery log 2,310; `launch_orphaned` 2.

## The cells (`H` = the games plugin on loopback)

- **P6** — the board launched by the hub itself → `active`, `paused`; `bench-release` → `"released": true`.
- **P7** — `party-minigames` → **one entry, `"players": 2`**.
- **P8** — seats **1,2** with the bench word → `starting` → **`playing`, `recognised` true within 10 s**; the title's
  window in front; rows `minigame_route` {"1": 1, "2": 2} and `minigame_stream` "switched": false.
- **P9** — the kept end P1 state by hand (scratch slot 8, RetroArch's load line, the copy removed) → **`ended`,
  `end_P1`, `scores` exactly [1, 0]** within 8 s.
- **P10** — `party-minigame-end` → `"ended": true`; RetroArch gone; the board's window active again; the status
  `launch_kind` godot; a second end → `"again": true`.
- **P11** — seats **2,1** with the kept end P2 state → **`ended`, `end_P2`, `scores` exactly [0, 1]**; then P10 again.
- **P12** — not run.
- **P13** — the board's own script driven headless against the live hub → its draw line ("a draw: the hub gave it up
  (the mini game did not start: the stream is not up)") and **`DRIVER [0, 0]`**; RetroArch gone after.
- **P11b** — two mini games back to back with the concurrent calls: seats 1,2 (bench) → `playing`; the kept end P1
  state → **`ended` `end_P1` [1, 0]**; **at once** `party-minigame-end` → **`"ended": true` within 2 s**; **at once**
  seats 2,1 → `playing`; during it **Home** (`native-stream-stop`) → **200 with `"taken": "home"` within 2 s, the status
  `paused` true** (the title paused, no board key); `bench-release` → released; the kept end P2 state → **`ended`
  `end_P2` [0, 1]**; the end → `"ended": true`. Rows: `minigame_taken` for each end and Home; `minigame_stream` "the
  stream is not up".
- **P14b** — END during a mini game: seats 1,2 → `playing` → `stop` → **200 `"taken": "end"` within 2 s** →
  **RetroArch gone within 10 s**; the party rows `minigame_given_up` "ended from the onn", `minigame_end` "onn",
  `quit`, **`exited` code 0**; `status` → **`active` false**; no board / Godot / RetroArch process left.
- **K1** — no board `pause` / `resume` / `quit` row between any `minigame_playing` and `minigame_end` row (but P14b's
  END's own `quit`).
- **P15 / U1** — the saves before = after (count and every hash), no `.state8`; the pictures' count and bytes
  unchanged.
- **R** — **every line of `route_watch.tsv` from part 1's start: `ok` 1 and `seconds` < 2.0** (the maximum per route
  recorded).

**Part 1 MET** = P6-P11, P13, P11b, P14b, K1, P15 / U1 and R all met → part 2's pre-registration hashed and the
sitting's first line (the flags left on). Anything not met → the close and the last reply, one plain sentence on what
failed.
