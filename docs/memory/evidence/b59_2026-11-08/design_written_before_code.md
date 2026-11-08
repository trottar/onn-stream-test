# B59 — design, written before any B59 code (H1: N64 through RetroArch, behind `PRIVYHUB_N64=1`)

Queue: `handoffs/QUEUE_2026-11-08V.md` §B59. Baseline `a8a505e5`. Built in `/tmp/b_q14v_b59` (companion/, tools/,
tests/, PrivyHub/ only); the tree gets the diff at the end, uncommitted. **Nothing fetched (no core), no emulator
started, nothing written to the drive; no title, serial or path in any record** (the drive's folders by role only).

## 0. Settled (read on the hub, read-only)

**(1) The core.**
- **The RetroArch AppImage bundles no core.** Its squashfs, listed with `7z l` (nothing run): 123 files, `usr/bin`,
  `usr/lib` (system libraries only), `usr/share`; no `*_libretro.so`. Its version: `emulators.json` says 1.22.2 (the
  folder is named for the 2026-09-07 nightly).
- **The cores folder** `runtime/emulators/retroarch/cores-linux/` holds fceumm, bsnes, snes9x, blastem and
  mednafen_psx_hw: **no N64 core.** The AppImage home's `cores/` holds 322 core-info files (Mupen64Plus-Next and
  ParaLLEl-N64 among them): descriptions, no binary.
- **So: "fetch needed".** Neither core is at hand, so neither is measured (the queue: both only if both are present).
- **First choice: Mupen64Plus-Next** (`mupen64plus_next_libretro.so`), because:
  - it is the maintained N64 core;
  - its default renderer is GLideN64, hardware OpenGL (core 3.3 / GLES 2), which the hub's Vega 7 runs through Mesa;
  - RetroArch here has no `video_driver` line, so it uses the default GL driver, which Beetle PSX HW already uses;
  - its own info file calls it "a good first choice for most users", working "better than the ParaLLEl-N64 core".
- **ParaLLEl-N64** is kept by name only: `PRIVYHUB_N64_CORE=parallel_n64`. Its strength (ParaLLEl-RDP, accurate, on
  Vulkan, with an LLE RSP) costs CPU and GPU the hub has not shown it can spare, and it wants RetroArch's Vulkan
  driver. B59 writes no options for it.
- **The fetch is A's, with the user's go** (B fetches nothing):
  - E3-S4's precedent for snes9x is `https://buildbot.libretro.com/nightly/linux/x86_64/latest/mupen64plus_next_libretro.so.zip`;
  - the stable tree for 1.22.2 is recalled to ship cores only inside the full `RetroArch_cores.7z`. A lists
    `stable/1.22.2/linux/x86_64/` first, takes a per-core file there if one exists, else the nightly one;
  - unzip into `cores-linux/`; record the zip's and the `.so`'s sha256 (the emulator's, not content);
  - then run `tools/n64_core_check.py`: "bundled" (present) and each option key below found in the `.so`'s bytes. It
    scans strings only and never loads or runs the core.

**(2) The `n64` system, in place from the drive.**
- **The drive's N64 folder** is the sibling of the PS2 one (counted by extension only): 13 files, all `.v64`, no
  subfolders, no stem in two formats. It is read-only for this user.
- **Generalised from B49:** a system → a folder that a key of the gitignored paths file names. That is the same file
  as PS2's: `PRIVYHUB_PS2_PATHS` names it, else `runtime/h3_p1_paths.txt`. N64 reads **`N64_DIR=`** from it and
  nothing else; GameCube will read `GAMECUBE_DIR=` (B61). A adds the one line at stage 1. A missing key or folder →
  an empty list, and a launch refused "N64 folder is not configured".
- **The new module** `companion/inplace_library.py`:
  - `read_dir(project_root, key)`;
  - `list_titles(folder, rank)`: read-only, `os.walk`, hidden names skipped, one entry per (folder, stem
    case-folded), the best-ranked suffix kept;
  - `resolve(folder, relative, prefix)`: refuses an escape, a missing file and a wrong prefix.
  - **PS2's `ps2_session` is not moved onto it** (B49-B57's tested path untouched; a later item may).
- **N64's rules:** `.z64` > `.v64` > `.n64` (the core reads all three byte orders). The id is the plugin's
  `_stable_id("n64", "n64/<relative>")`, the title its `_clean_name`, and `relative_path` is `n64/<inside N64_DIR>`.
  - That form makes the save-state stem the file's stem, as for every system.
  - The plugin's user-content lookup (`PROJECT_ROOT/relative_path` under `games/`) returns its empty answer, as PS2's
    does.
- **The listing does no `mkdir` and writes nothing** (a test snapshots the folder).

**(3) The pad.**
- **The chain:** the onn's pad → the companion's uinput pads P1-P4 → RetroArch's autoconfig
  (`data/games/retroarch/autoconfig/udev/`, read):
  - button 0 = RetroPad B (south), 1 = A (east), 2 = X (north), 3 = Y (west);
  - 4 / 5 = L / R; 6 / 7 = Select / Start; 8 / 9 = L3 / R3;
  - axes +2 / +5 = L2 / R2; the hat = the D-pad; axes 0 / 1 = the left stick, 3 / 4 = the right stick.
- **The core's N64 mapping** (Mupen64Plus-Next's defaults, **recalled**; the user's C21 line reads them back). On the
  onn's pad (Xbox labels / PlayStation labels):

  | N64 | RetroPad | the onn's pad |
  | --- | --- | --- |
  | the analog stick | left stick | left stick |
  | A | B (south) | A / Cross |
  | B | Y (west) | X / Square |
  | **C-buttons** | **right stick** | **right stick** (up / down / left / right = C-up / C-down / C-left / C-right) |
  | Z | L2 | the left trigger |
  | L / R | L / R | the bumpers |
  | Start | Start | Start |
  | D-pad | D-pad | D-pad |

  The core also turns the face buttons into C-buttons while R2 is held (recalled).
- **The choice: the C-buttons on the right stick** (the core's default):
  - the virtual pads carry the right stick;
  - most C-button uses are camera / direction clusters, which suit a stick;
  - A / B stay where a player expects them.
- **The alternative, stated and not chosen:** the C-buttons on the face buttons, through the core's "independent
  C-button controls" option (recalled key `mupen64plus-alt-map`). It moves A / B as well. B61 does it only if the
  user's C21 line asks.
- **The form: core options, no remap file.** `privyhub-input.cfg` is written as for every system, with N64's profile
  `analog_dpad: none`, so `input_player1-4_analog_dpad_mode = "0"`: the left stick stays analog, never a D-pad.
  `mupen64plus-alt-map = "False"` is written explicitly, so an older setting cannot flip the layout.

**(4) Four ports, always.**
- **On every N64 launch:** `--device=1:1 --device=2:1 --device=3:1 --device=4:1` (RETRO_DEVICE_JOYPAD), from
  `players_joined`, `players_chosen` or neither alike. No multitap.
- **The plan** `n64_session.plan()`: `ports 4`, `multitap false`, `multitap_available false`, `source "n64"` (the
  plugin's B54 line still sets `"join"` when the launch carried `players_joined`). `players_session.ports_set` accepts
  the source `"n64"` (one more value in its tuple, reached only by this plan).
- **The start's `ports_set`** reads `players 4, multitap false, multitap_available false`, so the client's
  `PlayerPrompt` (read, unchanged):
  - joins P1-P4 on the ports that exist (its cap is the title's player count when 1, else `ports.players` = 4);
  - **never asks for a relaunch**: a relaunch is asked only when `multitap_available`;
  - so **no "Setting up 4 players…" ever on N64**. `relaunch_ports` would refuse anyway ("The session already has
    these ports").
- **The cost, disclosed:** the core sees four controllers plugged in, each with a pak. A title that shows the
  controllers present shows four. The input polling of four ports is not measurable as a cost.
- **No client change, no APK.**

**(5) Save states and the recovery stack: RetroArch's, as PS1's; no skip.**
- PrivyHub's SAVE / LOAD (slots 1-3), the hold's slot-9 scratch, the stall resume's load and the give-up recovery
  save all go through RetroArch's network commands. None checks the system (read: `rewind_cores`, `hold_rewind`,
  `link_drop_recovery`, `save_state` / `load_state`).
- **The rewind:** `PRIVYHUB_INPUT_HOLD_REWIND=1` is B12's `state` mode, so **no RetroArch rewind keys for any core**
  (`config_allowed` false). The hold saves slot 9 at 400 ms of controller silence and loads it at the release, as
  PS1.
  - **The state's size is recalled** at the order of Beetle's 16 MB, the size `LOAD_CONFIRM_S` 0.15 s was set for. A
    reads the first N64 state's size at C22.
  - RetroArch's own rewind would cost as Beetle's did (B9: a buffer near 1 GB, +16.6 CPU points), so it stays off.
- **Paks:** `mupen64plus-pak1`-`4 = "memory"`, so a title saving to the Controller Pak saves; cartridge saves are the
  core's own. The user's saves are PrivyHub's SAVE button (the standing rule), as PS1.

**(6) The core options for the hub.**
- **The file** is the per-core `.opt` RetroArch reads: `<RetroArch config dir>/Mupen64Plus-Next/Mupen64Plus-Next.opt`,
  under `~/.config/retroarch/config/`, as PS1's Beetle `.opt`. It is **merged at launch**: our keys set, every other
  line kept, temp + rename; created if absent; written only for `mupen64plus_next`.
- **The keys (recalled names; `n64_core_check.py` confirms each against the fetched `.so`):**
  - `mupen64plus-rdp-plugin = "gliden64"`, `mupen64plus-rsp-plugin = "hle"`, `mupen64plus-cpucore =
    "dynamic_recompiler"`;
  - **native resolution first:** `mupen64plus-EnableNativeResFactor = "1"`, `mupen64plus-43screensize = "320x240"`,
    `mupen64plus-aspect = "4:3"`;
  - `mupen64plus-Framerate = "Original"`;
  - `mupen64plus-alt-map = "False"`;
  - `mupen64plus-pak1` … `mupen64plus-pak4 = "memory"`.
- **Audio:** no core option. RetroArch resamples to `audio_out_rate` 48000 as for every core, and the companion moves
  the sink-input by PID as today.
- **The frame rate and the metric.**
  - The stream's capture is x11grab at a fixed 60 with `-r 60` (`PRIVYHUB_SNES_CAPTURE_FIX=output_rate`, adopted). So
    the stream carries 60 frames a second whatever the title draws.
  - An N64 title drawing 20-30 frames internally therefore reads 60 on the heartbeats, and **UX-R3's R rule (rendered
    < 50 fps) does not fire on it**; nor does it see the title's own slowdowns.
  - **The metric for A, `tools/n64_frames.py`:** ffmpeg `showinfo` of a capture, parsed with `ps2_p2_frames.parse`
    (YUV only).
    - Distinct frames per second; static / black seconds excluded, as P2's.
    - **The title's internal rate** is the most common distinct count of the kept seconds, snapped to 20 / 30 / 60
      (or `--internal-fps`). The beat forgiveness applies at 60 only.
    - **A hitch second** is a kept second with distinct frames < 5/6 of the internal rate (UX-R3's 50-of-60, scaled:
      < 50 / < 25 / < 17).
    - **The hitch rate** is per 10 min, set beside the stream's UX-R3 hitch rate from `diag_read` and PS1's.

**The game log, the keeper and the rows.**
- **Two lines** in the RetroArch session's game log:
  - `N64 launch: core=<name> ports=4`;
  - `N64 core options: <n> keys (Mupen64Plus-Next)`, or `none (<core>)`.
  - Today's header lines (game id, title) stay as for every RetroArch system, unchanged.
- **The start payload** gains `n64_session: {core, ports, options_keys}`, only on an N64 launch.
- **The keeper's label:**
  - `diag_read.CORES` gains `"n64": "mupen64plus-next"`, so an N64 launch reads `N64 <4-hex>` with its core.
  - The trip / diag keepers' `GAME_LOG` already copies `game_n64_…` logs.
  - The `diag_read` entry is the one unconditional line: a dict entry that only an `n64` log name reaches.

## 1. Behind `PRIVYHUB_N64=1`

- **`companion/n64_session.py`** (new):
  - `FLAG_ENV`, `SYSTEM_ID "n64"`, `SYSTEM_NAME "Nintendo 64"`, `RELATIVE_PREFIX "n64/"`, `SUFFIX_RANK`;
  - `CORE_ENV "PRIVYHUB_N64_CORE"` (default `mupen64plus_next`; `[a-z0-9_]+` else refused), `core_file()`,
    `core_path(cores_dir)` (refused "N64 core not installed (fetch needed): <file>");
  - `presence(project_root)` → `{"state": "bundled"|"fetch needed", "core", "cores_dir_has", "appimage_bundles":
    false}`;
  - `PROFILE` (the system profile injected into a copy of the runtime: name, extensions, `controls.analog_dpad
    "none"`) and `runtime_with_profile(runtime)`;
  - `plan()`, `OPTIONS`, `options_library(core_file)`, `merge_options(text, keys)`, `write_options(config_dir,
    core_file)`;
  - `titles_for_plugin(...)`, `log_lines(...)`.
- **`companion/inplace_library.py`** (new): §0 (2).
- **`EmulatorManager`:**
  - the import under the flag;
  - `_controller_profile_catalog` → Core default for `n64` (as `ps2`);
  - in `launch`, an `n64_launch` boolean that drives the profile-injected runtime, `_resolve_n64` instead of
    `_resolve_game`, the plan (four ports, replacing any pick's), the `.opt` merge, the two log lines and the payload
    key.
  - **Everything else is the RetroArch launch unchanged:** the session cfg, the input cfg, the network-command port,
    the paused handoff, the save states, stop.
- **`plugins/games.py`:** the import under the flag; `SYSTEMS` + `n64` per instance; the scan's `n64` branch (no
  `mkdir`, as `ps2`'s).
- **`players_session.ports_set`:** `"n64"` in the plan sources.
- **`tools/n64_core_check.py`** (new): the presence line, and with `--keys` the option keys found / missing in the
  installed `.so`. No network, no load.
- **`tools/n64_frames.py`** (new): §0 (6).
- **`tools/diag_read.py`:** the `CORES` entry.

**Absent (or any value but `1`):**
- nothing imports `n64_session` / `inplace_library`;
- `SYSTEMS` has no `n64` and the scan is today's;
- an `n64` launch is today's refusal (`emulators.json` has no `n64` profile, so `_resolve_game` refuses);
  `controller_profile` refuses as today;
- no `.opt` is written and no `N64` line appears;
- `status()` is unchanged (no `n64` in `core_status` with the flag either: the profile is injected per launch only,
  so a missing core never turns the runtime "not ready").
- **Flag on, core missing:** the list shows N64, and a launch refuses "N64 core not installed (fetch needed)". A puts
  the bench drop-in on only after the core is in place.

## 2. Tests (`tests/n64_session/`; fakes only, temp dirs removed at exit by `_tmp_cleanup`)

- **The list:**
  - `.z64` / `.v64` / `.n64`, one per stem, `.z64` preferred; hidden names and other suffixes skipped; subfolders;
  - nothing written (a snapshot);
  - no `N64_DIR` → [];
  - the resolver refuses escapes, a wrong prefix and a missing file.
- **The plugin, in fresh interpreters:** flag absent / `0` / `1` → the import, `SYSTEMS`, the scan (with the flag the
  `n64` entries, `relative_path` `n64/…`), the catalog (absent: `EmulatorError`; on: Core default).
- **The launch** (a fake RetroArch tree in a temp project, the real `emulators.json`, a fake Popen, the command-ready
  wait faked, `XDG_CONFIG_HOME` a temp dir):
  - **the command:** `--config …`, `--device=1:1` … `4:1`, `--verbose -L <cores>/mupen64plus_next_libretro.so
    <the fake .z64>`;
  - **`--device` for 1-4** from `players_joined` 1 / 2 / 3 / 4 and from no key (always four);
  - **the `.opt`:** every key and value, a foreign key kept, idempotent;
  - **the remap file:** `privyhub-input.cfg` with `analog_dpad_mode "0"` for players 1-4 and no bind lines;
  - **the log** has the two lines; the start's `ports_set` reads players 4 / multitap false / multitap_available false;
  - `PRIVYHUB_N64_CORE=parallel_n64` → that core, no `.opt`;
  - a missing core → refused, no Popen;
  - a malformed core name → refused.
- **Absent → today byte for byte:**
  - an `n64` launch → `EmulatorError`, no Popen, no `.opt`;
  - **a SNES launch with the flag absent and on** gives the same command, the same `privyhub-input.cfg` (its random
    port masked) and the same session cfg.
- **The presence check:** "fetch needed" with no core, "bundled" with a fake `.so`; no network (a test fails any
  socket connect); `--keys` reports found / missing on a fake `.so` with some keys.
- **The metric:**
  - a 30-fps synthetic capture (every frame doubled) → internal 30, no hitch second;
  - a second at 20 → a hitch;
  - a 60-fps capture with the beat → 60, no hitch;
  - black seconds excluded;
  - `--internal-fps` overrides.
- **The keeper's label:** an `n64` game log name → core `mupen64plus-next`.
- **Mutations** after the suite is green (`tests_mutations.txt`), each expected caught:
  - the flag gate removed;
  - the four ports cut to two;
  - the `.opt` written for another core;
  - `.v64` preferred over `.z64`;
  - the listing's `mkdir`;
  - the `"n64"` source dropped from `ports_set`;
  - the hitch threshold not scaled.

## 3. Not built / for A

- **The fetch** (the user's go). The first launch, the mapping and the frame rates are HOME-7's C21-C23.
- **Recalled, read back at C21-C22:**
  - the option keys (by `n64_core_check.py --keys` before the first launch);
  - the R2 face-button C mode;
  - the state's size.
- **A wrong key is inert:** RetroArch ignores an option the core does not declare, and the core default runs.
