# Stage 4 — GameCube (T16): C37's GameCube line, B72 (e) (~16:58-16:59Z)

- **The user (verbatim):** "I can reach end, it's just off the screen 95%" / "Nothing different, the intro cinematic
  continued to play" (both about T17's first sitting, `../c38/T17_FIRST.md`) / "Stage 4" / "Touchpad does nothing".
- **Hub, read live 16:59:34Z:** the hub's pointer at 960 × 540 **inside the Dolphin window** (WM_CLASS `dolphin-emu`,
  0,0 1920 × 1080; `pointer_gc.txt`); the encoder **`-draw_mouse 0`**, once, before `-window_id`; the rest = C5-M1's
  pre-B70 argv with the adopted output `-r 60` (`encoder_argv_gc.txt`, `argv_compare_gc.txt`).
- **Dolphin's per-launch log** (`dolphin_devices.txt`): `Added device: evdev/0/PrivyHub Virtual Gamepad P1` … `P4`, the
  X core pointer (as HOME-9), **no `SDL/` device** (HOME-9's `SDL/0-3` gone). The four `SDL` lines in the log are SDL's
  own start banner (`dolphin_sdl_lines.txt`), not devices.
- **The game log** (`gc_lines.txt`): `GC launch: dolphin ports=4 backend=vulkan adapter=0 config=whole`, `GC window:
  2.1s`, `GC boot: cpu thread 1.0s`, `GC audio: sink-input 0.0s`, **`GC pads: P1=evdev/0 P2=evdev/0 P3=evdev/0
  P4=evdev/0`** (no MISMATCH); a Continue: `GC load: slot 1 hotkey; picture ok 0.9s`.
- **The launch's environment** (`sdl_hints_env.txt`, the Dolphin processes): `SDL_JOYSTICK_BLACKLIST_DEVICES=0x1209/0x5048`,
  `SDL_GAMECONTROLLER_IGNORE_DEVICES=0x1209/0x5048`.
- Rows (`rows_raw.jsonl`, pad ids redacted): `launch_ports` 16:58:45Z gamecube / dolphin; `state_reply` ok (the
  Continue's LOAD); `gc_session`; `session_started` 16:59:01Z; two joins (`pad_slots`).
- **Read:** C37 GameCube **MET** (the user's line; host half read live). **B72 (e) MET** — only the evdev four.
