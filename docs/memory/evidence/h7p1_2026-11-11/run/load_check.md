# The headless load check (2026-11-11 15:59:28-15:59:31Z; one `--as-is` load of the `begin` copy, a throwaway rule)

- Called as B's tool with one change on the calling side only: the tool's temp folder kept for its log
  (`shutil.rmtree` replaced by a no-op in the calling process; the tool's file unchanged); `TMPDIR` under `~/.cache`.
- RetroArch's log (127 lines): the core loaded, the game file opened by the core (its own `Loading …` line, the
  controllers, the GL context), **`[State] Loading state …, 16777240 bytes`** (N > 0), no state-failure line. The JSON:
  `state_loaded` true, `as_is` true (the throwaway rule's values mean nothing).
- **The BIOS line:** `Firmware is missing: scph5501.bin` — **the same line as in the hub's own PS1 launches** (the
  hub's system folder holds no PS1 BIOS either; its PS1 games play). So the headless session matches the hub; **no
  BIOS link was needed** and none was placed.
- Other warnings, the same as any headless run: GameMode unavailable, no Wayland (X used), the null joypad driver
  falling back to udev.
- **Core options:** the hub's PS1 game-specific options file 91 keys; the headless session's (the core's defaults) 91
  keys; **1 differs — the internal render resolution** (the hub 4x, headless 1x; drawing only, not game memory).
- RetroArch processes after: 0.
