# Stage 4 — the game on the hub's display (no stream; nobody at the controls; 16:16-16:29Z)

**How the heaviest scene was reached** (stated in the pre-registration before any run): no check and no
`play_headless` run holds Witch Hill's dark half on screen for a minute, and the lobby shows the first board until
player 1 picks another. So `probe_dark.gd` (A's own, here and off both repos; it edits nothing) runs the game's own
main scene (`game/main.tscn`) with a window: Witch Hill set as player 1 would in the lobby (`main.set_board`), four of
the registry's characters standing on the board's darkest space (mood 1.00), the darkest mood held (the board's own
`hold_mood(1.0)`: fog 0.880 — the board's `FOG_MOST` — 2 ground-mist layers shown, 8 lamps lit), the game's own camera
following the first figure as on that player's turn. Godot's own `--print-fps` gives one frames-a-second line per
second; the probe prints the fog, lamps and mist every 10 s (unchanged through every run). Fog and lamps off: the
game's own setting (`Settings.mist = false`, `main.apply_mist()`) from the same script (fog 0.000, 0 lamps, 0 layers).
The lobby's join line ("Hold any button…") stays on screen; nobody joined.

**A's check pictures** (two, off both repos, described in words only): the dark half of the hill under fog and ground
mist, lit lanterns, bare trees with glowing eyes, the witch and her house, four small figures standing together on one
space, the lobby's join line across the top; Forward+ and Compatibility look the same.

**The command** (`<run>/cmd.txt`): DISPLAY `:0` (the X display the emulators use), `--path <the board game's repo>
--rendering-method <m> --rendering-driver <d> --resolution 1920x1080 --position 0,0 --print-fps` (+ `--disable-vsync
--max-fps 0` for vsync off — the project caps at 60 otherwise) `-s <probe> -- --content=<the pictures folder>`. The
project's files untouched. With `--content` the game's registry reads 2 content roots and 11 characters (without: 1
and 4; `probe_content.gd`, headless, counts only).

**The window** (every run, `run.txt`): found 0.5 s after the start by the process (`xdotool search --pid`); title class
`"Godot_Engine", "PrivyParty"`; **1920 × 1029 at (0, 51)** — the window manager keeps the desktop panel's strip, and
the game's fixed 1920 × 1080 picture is scaled into the window (narrow side bars). No error, warning or crash line in
any run (Godot's banner, the device line, the vsync line, the frame rates and the probe's lines only).

| renderer (Godot's own start line) | run | s | fps median | lowest | highest | < 50 | < 30 | Godot CPU % (one core) | graphics busy % | VRAM / GTT MB | load (max) | CPU / graphics °C (max) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Forward+** — Vulkan 1.4.305, RADV Renoir | vsync on | 74 | **60.0** | 60.0 | 60.0 | 0 | 0 | 18 | 49 | 424 / 131 | 1.03 | 45 / 38 |
| | vsync off | 75 | **146** | 143 | 147 | 0 | 0 | 45 | 99 | 417 / 135 | 1.46 | 52 / 51 |
| | fog and lamps off, vsync off | 75 | 252 | 251 | 254 | 0 | 0 | 67 | 99 | 418 / 135 | 1.65 | 58 / 57 |
| **Mobile** — Vulkan 1.4.305, RADV Renoir ("Forward Mobile") | vsync on | 75 | **60.0** | 60.0 | 60.0 | 0 | 0 | 17 | 27 | 417 / 135 | 1.72 | 66 / 55 |
| | vsync off | 75 | **334** | 332 | 335 | 0 | 0 | 89 | 99 | 408 / 144 | 1.71 | 63 / 61 |
| | fog and lamps off, vsync off | 75 | 421 | 406 | 428 | 0 | 0 | 114 | 83 | 409 / 142 | 2.15 | 68 / 61 |
| **Compatibility** — OpenGL 4.6 core, radeonsi Renoir | vsync on | 74 | **60.0** | 60.0 | 60.0 | 0 | 0 | 24 | 24 | 358 / 134 | 1.90 | 67 / 52 |
| | vsync off | 76 | **370** | 366 | 373 | 0 | 0 | 129 | 99 | 350 / 134 | 2.16 | 66 / 65 |
| | fog and lamps off, vsync off | 76 | 428 | 408 | 444 | 0 | 0 | 127 | 68 | 346 / 128 | 2.81 | 71 / 63 |

(The first printed second after the scene was set is left out of each run — partial; Godot's CPU and the graphics
figures are medians of one sample a second; the temperatures rose run after run from 45 °C, nine runs back to back.)

- **R:** every renderer **fit** (vsync on: median 60.0, lowest 60.0, no second under 50, ≥ 74 s). **Headroom** (vsync
  off): Compatibility 370, Mobile 334, Forward+ 146. **The one to carry forward: Compatibility (OpenGL)** — the fit
  renderer with the most headroom (stated, not adopted). Seen beside it, not a bar: Mobile at vsync on was the lightest
  on the graphics device (27 % against 24 % / 49 %) and on the CPU (17 % against 24 % / 18 %); Compatibility draws
  with more CPU when unthrottled (129 % against 89 %); Forward+ costs about twice the graphics time of the other two
  (the fog and lamps take ~42 % of its frame unthrottled: 146 → 252).
- **The close, every run:** `xdotool windowactivate --sync` on the game's window, then `xdotool key F10` (XTEST) — the
  game's `quit` action; **exit code 0 in 0.61 s, nine of nine**; no crash line; no Godot process left (counted). The
  window close request was not needed (xdotool 3.20160805 on the hub has no close-request command — `windowclose`
  destroys the window, `windowkill` kills the client — so F10 is the clean way available). The plain way (SIGTERM)
  was never used.
