# PP-H1 — pre-registration (hashed at the end of stage 1, before the fetch)

Task: `handoffs/PP-H1_PRIVYPARTY_HUB_PROBE_TASK.md` — PrivyParty on the hub, step 1 of four: the probe with no stream.
Unattended; no user, no onn, no pads. No stream, no companion or keeper restart, no flag, no emulator. Nothing
perceptual; nothing here adopts anything.

## Stage 1 as read (`pre/`)

This repo: HEAD `a302339b` (H7-V4 committed), the tree clean but for this record; the two units; no game, no stream;
eighteen lines; `--check` ok (adb up). The board game's repo: HEAD `21e7e44f` (2026-11-12, the hand-back note),
`git status --short` empty (also with `--ignored`), 282 tracked files; `checks/` 25 scripts (step0-step24);
Godot's cache `.godot/` absent and git-ignored. The owner's pictures folder: exists, 116 files, 15,039,288 bytes.
The hub: AMD Ryzen 5 PRO 4650G (12 threads), its Radeon (Renoir) integrated graphics on `amdgpu`; Vulkan 1.4 (RADV,
Mesa 25.0.7) and OpenGL 4.6 core (radeonsi) offered; the X display the emulators use `:0`, 1920 × 1080 at 60 Hz, a
window manager running; at rest load 0.15, graphics busy 0 %, CPU 31-34 °C, graphics 27 °C. Godot's user folders
under home absent.

## The cells

- **F — the fetch:** the zip's SHA-512 equals the line published for it in the release's sums file; the executable
  reports 4.7.2 stable.
- **C — the checks:** 25 of 25 end with their `STEP N CHECK: PASS (K assertions)` line and exit code 0 on the hub
  (headless, from the board game's repo root, after the import step once).
- **G — the game starts and stops:** under at least one renderer the game starts on the hub's display with the
  owner's pictures (`--content=` after `--`), with no error or crash line, and closes by the `quit` action (F10 to the
  window) or a window close request, with exit code 0.
- **R — a renderer is "fit"** when, in the heaviest scene at 1920 × 1080 with fog and lamps on and vsync on, the
  frames a second have a median ≥ 59 and no second under 50, over ≥ 60 s. Each of Forward+ (Vulkan), Mobile (Vulkan)
  and Compatibility (OpenGL) marked fit / not fit / did not start; with vsync off (and the frame cap lifted) the median
  is its headroom. **The one to carry forward** = the fit renderer with the most headroom (stated, not adopted). No
  renderer fit → said plainly, with the numbers with fog and lamps off if they could be taken.
- **The heaviest scene** (A's to settle, stated here before any run): no check and no `play_headless` run holds Witch
  Hill's dark half on screen for a minute (the checks are short scripted asserts; `play_headless` plays a whole game at
  once), and the lobby shows the first board until player 1 picks another. So a short probe script of A's own, kept off
  both repos, runs the game's own main scene (`game/main.tscn`) with a window: it picks Witch Hill (as player 1 would),
  stands four of the registry's characters on the darkest space, holds the board's darkest mood (fog at its most, the
  ground mist and the lit lamps — the board's own `hold_mood(1.0)`), and holds the game's own camera on that space;
  Godot's own `--print-fps` gives the frames a second. Fog and lamps off through the game's own setting
  (`Settings.mist`, `main.apply_mist()`) from the same script. Nothing in the board game's repo is edited.
- **U — nothing else touched:** eighteen lines before = after, `--check` as at stage 1; the two units only (no restart);
  this repo's tree changed only by this record; the board game's repo `git status --short` after = before (if Godot's
  cache were not ignored, what appeared would be listed and left); the pictures folder's count and size before = after;
  the hub's saves untouched (161 files, the same listing; no emulator started); nothing left running.

**MET** = F, C, G and U met and at least one renderer fit. F, C, G, U met with no renderer fit = **"MET but for R"**.
Anything else NOT MET.
