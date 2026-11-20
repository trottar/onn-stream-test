# B167 — learn's real picture source starts (design, written and hashed before any code)

Queue: `handoffs/QUEUE_2026-11-19BD.md` §B167. Baseline `df81c762`. **No companion change** (the tool and its capture
module only).

## The diagnosis (one real run, before this design)

`rehearse T88 --collect other=2`, run once with nothing running and no client, `TMPDIR` pointed at a private folder
off the repo and RetroArch's own log copied out of the capture's temp folder before the tool removed it (both starts
caught). Both logs, the same: the core asks for an OpenGL context; **`[ERROR] [Wayland] Failed to connect to Wayland
server.`**, then the KMS context: **`[ERROR] [KMS] Error when switching mode.`**, **`[ERROR] [Video] Cannot open video
driver. Exiting...`**. **RetroArch was given no display.** The shell the tool runs in (A's, and mine) has no `DISPLAY`
and no `XAUTHORITY`; the hub's user manager has both (the companion's RetroArch gets them from it), and H7-V1 ran "on
the hub's display". The game file, the AppImage and the core were found; the config was read.

Read beside it — what H7-V1's capture passed that the tool's does not: **the hub's own core options** (the core-level
`<core>.opt` and the title's own `<game file stem>.opt`, copied into the temp config, `game_specific_options` on — its
record: "the render scale 4x as on the hub"); and the core: B95's list says `snes9x` for SNES, **the hub launches SNES
with `bsnes`** (`emulators.json`), whose states the other core cannot load. The AppImage and the cores folder are the
hub's own (the same files).

## The fix (`tools/party_add_game_capture.py`, and where `tools/party_add_game.py` calls it)

1. **The hub's display:** `DISPLAY` and `XAUTHORITY` from the caller's environment when set, else from the user
   manager's (`systemctl --user show-environment`) — the one the companion runs under. Neither → not started, the
   reason `display`. The window opens on the hub's display as H7-V1's did; nothing streamed.
2. **Never beside a user's session:** before any start, the hub's `status` and `native-stream-status` (the tool's own
   `users_session`): a game running or a client's stream up → not started, the reason `busy`.
3. **The hub's own core** for the system: `emulators.json`'s Linux core (ps1, snes), the N64 session's
   (`mupen64plus_next`); its states folder name from the core (`bsnes`, `Snes9x`, `Beetle PSX HW`,
   `Mupen64Plus-Next`). Not in the cores folder → the reason `core missing`.
4. **The hub's own core options**, read only from the user's RetroArch config (`$XDG_CONFIG_HOME` or `~/.config` →
   `retroarch/config/<core folder>/`): `<core folder>.opt` and `<game file stem>.opt` when present, copied into the
   capture's temp config; `game_specific_options` on (H7-V1's way).
5. **A reason, never "ProofError" alone:** every way the capture can fail raises `CaptureError(reason, words)`, the
   reason one of `busy`, `display`, `content not found`, `core missing`, `config`, `exited` (RetroArch stopped, its log
   naming none of the above), `not playing` (no PLAYING within the bound), `state refused` (B95's three load failures)
   — the words fixed per reason, no name. The log's lines are matched to a reason (`Cannot open video driver` →
   display; `Failed to load content` / `Could not read content` → content not found; `Failed to open libretro core` →
   core missing; `Failed to load config` / `Could not read config` → config); none matched → `exited`.
6. **The emulator's own log stays off the repo, beside the scratch:** every capture's RetroArch log is copied to the
   title's add_game folder, `logs/<role>.retroarch.log` (overwritten each run; that folder is never in the repo); a
   failing cell says "RetroArch's own log: logs/<role>.retroarch.log in the title's add_game folder" — no path.
7. **learn says it as a cell:** `_pictures` catches `CaptureError` → learn's cell **"pictures made"** read `"<reason>:
   <words>"`, not met, learn FAIL (today: an uncaught exception). rehearse carries it as `learn: pictures made`.
   Nothing written outside the tool's scratch and its own folders.

## The setup's cheats (BC's item 4) — settled by the run, not built first

T88's kept states and the user's slot are under its setup. The capture loads no cheats. The settle: with the capture
started, **rehearse's cells "<ending>: the scratch rules read it as the real rules"** — each of T88's kept endings
captured without cheats, read by the **real** rules (learnt in part from H7-V1's pictures, which loaded no cheats, and
from the sittings' recordings, under the setup) as its own ending. Met for all four → the pictures are the ones the real
rules know; no cheat loading built. Not met with the pictures looking otherwise → build it (the setup's cheats applied
as the hub's launch does). The record says which.

## Proved by the real thing

`rehearse T88 --collect other=2` run by me, each time only after `status` and `native-stream-status` show nothing running
and no client: **PASS** — learn's bars in the scratch, the scratch rules reading T88's kept endings as the real ones do,
the real rules folder before = after. Every run and its verdict disclosed. Then say what it proves of learn for a new
title and what it does not (another core, a title on the drive, four players).

## Tests (`tests/b167_pictures_start/`)

A fake RetroArch (a script standing in for the AppImage: writes made-up log lines and exits, or answers RetroArch's
network commands) and made-up cores and config folders: **each reason** — busy, display (no display given; and the
log's video driver line), content not found, core missing, config, exited, not playing, state refused; the log copied
to `logs/` and its words never on the page; the hub's core per system (bsnes for SNES); the core options copied (the
core's and the title's own) and `game_specific_options` on; the display taken from the user manager when the caller
has none. **learn's cell names the reason** (a made-up title whose capture fails). The mutation that swallows the
reason (`CaptureError` words → "ProofError") caught; the core list back to B95's (snes9x) caught; the display not
passed caught. B157's, B162's and B163's suites green.
