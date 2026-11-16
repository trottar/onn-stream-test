# B116 — design, written before code (hashed before the first edit to the board's two files)

The board's repo at `820673c` (the two files committed by the user after B111), its tree clean. **Only my two files**:
`minigames/hub_minigame.gd` and `checks/hub_minigame_check.gd`; nothing else there; nothing committed there; Godot
headless only, in a scratch copy of the board's repo (its HEAD + the two files), Godot's own folders redirected.

## What PP-H3 showed

While the title played the board kept drawing behind it at a full core (Godot 98 %, against 21 % in front; the
title's RetroArch 51 %). In front, the board is held to the display's refresh (vsync); behind a full-screen window
the frame pacing no longer holds it and it draws as fast as it can — a picture nobody sees (the stream captures the
title's window) on the same CPU the title and the encoder need.

## The change (in `hub_minigame.gd` only)

- **While it waits, the board draws at most `IDLE_FPS` = 10 frames a second** — Godot's own `Engine.max_fps`
  (the engine's frame cap; physics and input are not slowed, timers keep their seconds). Applied by the pad gate the
  script already adds while it waits (B111's `PadGate`): when the gate enters the tree it remembers the board's own
  `Engine.max_fps` and sets the cap (never raising it: a board already capped lower keeps its own); **its restore puts
  the remembered value back** and is idempotent.
- **Restored whatever way the wait ends:** the script restores it **as soon as the wait ends** (a result, a give-up,
  the hub not answering, the board's own time limit) — **before** it tells the hub the end, so the board draws at its
  own rate again before the stream switches back to it (B115's way back switches at the end call); and the gate
  restores it when it leaves the tree — the gate removed after the end call, or torn down with the scene / the tree
  (the board quitting by F10, END from the onn) — so no path leaves the board capped. No wait (no hub, a refusal, no
  mini game for the players) → never capped.
- No line added to the board's log (its lines stay as B111's); nothing else in the board touched.

## Measured under Godot headless (the check) / what only the sitting can show

The check asserts, with its own stand-in hub: the cap is 10 at every result poll while waiting; at the end call the
board's own value is already back (for a board left uncapped, 0, and for one capped at 144: 144); after every path —
ended, a give-up, the hub not answering (missed polls), the gate torn down mid-wait — the board's own value is back;
for a refusal and no hub it was never changed. Its PASS line's count goes from 20 to the new count. **Headless has no
display and no compositor**: it shows the setting applied and restored on every path, **not the CPU**. **Only the
sitting can show** Godot's CPU behind the title (PP-H3b records it from its status watch: expected well under the 98 %
of PP-H3, nearer its 21 % in front or below).
