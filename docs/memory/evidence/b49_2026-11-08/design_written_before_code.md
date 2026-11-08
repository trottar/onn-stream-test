# B49 — the PS2 launch kind (design, written and hashed before any B49 code)

Queue: `handoffs/QUEUE_2026-11-08P.md` §B49. H3-P1 (`evidence/H3_P1_PS2_PROBE_2026-11-07.md`): PCSX2 v2.8.2 at full
speed; the capture and the audio carry over by the started PID; the pads must come from the onn (the user: "It's via
the onn on Bluetooth always"). Baseline `f3f912c5`, the tree clean; built in `/tmp/b_q08p_b49`. **Everything below is
behind `PRIVYHUB_PS2=1`; absent = today byte for byte.**

## 0. Settled (read from the code; PCSX2 not started)

**S1. How the onn learns a system and its titles.** The host's `GamesPlugin.SYSTEMS` (nes / snes / genesis / ps1:
name, folder under `games/`, extensions). `_scan` walks `games/<folder>/` per entry, giving each file an id
(`game_<system>_<sha1 16>` of its relative path), title, system and relative path. `systems` turns `SYSTEMS` into the
node tree (one lazy category per system, `games?system=<id>`), and the onn renders the host's nodes. **The client has no
hard-coded system set** (`MainActivity` reads only `system_name` and the host's nodes; the `ps1_*` keys it reads belong
to the PS1 multitap toggle). So `ps2` needs **no client change and no APK item**. The `details` call for a title needs
`EmulatorManager.controller_profile`, which raises for a system missing from `emulators.json`. The design returns
"Core default" (not selectable) for `ps2`.

**S2. Pause and resume today.**
- `launch` → `EmulatorManager.launch` (RetroArch; it waits for the command port) → the paused handoff
  `EmulatorManager.pause()` (`PAUSE_TOGGLE` until `GET_STATUS PAUSED`).
- The onn opens the stream: `native-stream-start` pauses if needed and starts the capture by the PID. The client's
  `native-stream-ready` → `resume()`.
- Back → `native-stream-stop` → `pause()`. Resume (B46's "unpause") → a new start, then `ready`.
- The recovery and stall paths call the same `pause()` / `resume()`.
- **PCSX2 has no UDP command port.** It does have:
  - the `TogglePause` hotkey (`Keyboard/Space` in the probe's ini);
  - PINE, its IPC socket: when `EnablePINE = true`, `$XDG_RUNTIME_DIR/pcsx2.sock` at the default slot. `MsgStatus`
    (opcode 0x0F) answers 0 running / 1 paused / 2 shutdown — **recalled, confirmed at A's run**.
- **So the design for `pause()` / `resume()` on a PCSX2 session:**
  1. read PINE's status;
  2. if PINE answers: focus the window found by the PID (`xdotool windowfocus --sync <wid>`), send the hotkey
     (`xdotool key space`), then poll PINE up to 1.5 s for the wanted state;
  3. if PINE is unreachable (the hotkey cannot be confirmed), or the state does not come: **SIGSTOP** the started PID
     to pause, **SIGCONT** to resume. The method is kept, so a SIGSTOP pause is undone by SIGCONT, never by the hotkey.
- The paused handoff right after the launch goes the same way, after the launch waited for the PID's window (≤ 30 s;
  the probe saw it in 3 s).

**S3. What uses RetroArch save states, and each one off for a PS2 session** (a `ps2` session has no network-command
port and no state slots):
- **the hold's return with a rewind** (`hold_rewind.Rewinder.rewind`, B4 / B8, under the adopted umbrella): skipped;
  the row is `rewind_skipped` with `reason: "ps2_mode: no save states"` and `ps2_mode: true`. The hold still freezes
  and resumes the game: B32 / B39's hold holds the picture and the stream; only the rewind is gone;
- **the scratch state save at a silence or a stall** (`rewind_cores.Cores.save`, B9 / B12 / B16, slot 9): not sent;
  counted as `saves_skipped_ps2`;
- **the stall resume's load** (`Cores.release` → `LOAD_STATE_SLOT 9`): goes through `Rewinder.rewind`, so it is the
  first item's skip: a stall then resumes with no rewind;
- **the link-drop give-up save** (D-BASE-R3, `save_recovery_state`): not taken. The row `gave_up_saved` carries
  `ps2_mode: true, save_skipped: true`, and no recovery prompt follows;
- the player's save-state slots (`save_state` / `load_state` / the recovery load / copy / discard): refused with "Save
  states are not available for a PS2 session".

**S4. The pads.** The companion's four uinput pads ("PrivyHub Virtual Gamepad P1-P4", 0x1209 / 0x5048, version 1, USB)
carry ten buttons and seven axes:
- the buttons, in code order: `BTN_SOUTH` `BTN_EAST` `BTN_NORTH` `BTN_WEST` `BTN_TL` `BTN_TR` `BTN_SELECT` `BTN_START`
  `BTN_THUMBL` `BTN_THUMBR`;
- the axes: X, Y, Z (the left trigger), RX, RY, RZ (the right trigger), and HAT0X / HAT0Y.

SDL's Linux backend numbers the buttons in key-code order (b0-b9) and the non-hat axes in code order (a0-a5), with the
hat as h0. So **the mapping line** is:

`03000000091200004850000001000000,PrivyHub Virtual Gamepad,a:b0,b:b1,y:b2,x:b3,leftshoulder:b4,rightshoulder:b5,back:b6,start:b7,leftstick:b8,rightstick:b9,leftx:a0,lefty:a1,lefttrigger:a2,rightx:a3,righty:a4,righttrigger:a5,dpup:h0.1,dpright:h0.2,dpdown:h0.4,dpleft:h0.8,platform:Linux,`

- `BTN_NORTH` (top) is y and `BTN_WEST` (left) is x, as the companion writes XUSB Y → NORTH and X → WEST.
- It is given to PCSX2 in its environment (`SDL_GAMECONTROLLERCONFIG`). **No file is written for it.**
- The pads exist before every launch (`ensure_game_controller`) in creation order P1-P4, so SDL opens them as SDL-0 …
  SDL-3. The order is recalled; A reads PCSX2's log of the opened controllers.
- **The DualShock 2 layout**, `[PadN] Type = DualShock2`:
  - Cross = `SDL-k/A`, Circle = `B`, Square = `X`, Triangle = `Y`;
  - Select = `Back`, Start = `Start`;
  - L1 / R1 = `LeftShoulder` / `RightShoulder`, L2 / R2 = `+LeftTrigger` / `+RightTrigger`;
  - L3 / R3 = `LeftStick` / `RightStick`;
  - the d-pad = `DPadUp` / `DPadRight` / `DPadDown` / `DPadLeft`;
  - the left stick: LUp = `-LeftY`, LRight = `+LeftX`, LDown = `+LeftY`, LLeft = `-LeftX`; the right stick: RUp =
    `-RightY`, RRight = `+RightX`, RDown = `+RightY`, RLeft = `-RightX`;
  - no motors (the pads have no force feedback).
- **The ports:**
  - no multitap: player 1 → Pad1 (port 1), player 2 → Pad2 (port 2);
  - multitap on port 1: players 1-4 → 1A / 1B / 1C / 1D = Pad1 / Pad3 / Pad4 / Pad5 (PCSX2's numbering, recalled),
    Pad2 none;
  - 1 player: Pad2 none;
  - every unused PadN: `Type = None`.

**S5. The multitap:** `[Pad] MultitapPort1` = true when `players_chosen` is 4, else false; `MultitapPort2` false; at
launch only (B46's rule). `players_session.plan("ps2", n)` → ports 1 / 2 / 4, multitap for 4, `multitap_available`
true, no `--device` arguments.

**S6. The metadata default:** a PS2 title with no entry reads `player_mode` unknown and `max_players` 0 → B41's rule
gives 2 (`players_source: default`); no launch pick → 2 → Pad1 + Pad2.

## 1. Where the files come from

- **The folders:** `BIOS_DIR` and `GAMES_DIR` from the paths file `PRIVYHUB_PS2_PATHS` names, else
  `runtime/h3_p1_paths.txt` (gitignored; `KEY=value` lines; only those two keys read). They are read at run time only,
  never written into code, a record, a test or a fixture. With the flag on and the file or a key missing, the `ps2`
  system lists **zero** titles and a launch refuses ("PS2 folders are not configured").
- **The emulator:** the single `*.AppImage` in `runtime/emulators/pcsx2/` (gitignored); none or several → the launch
  refuses.
- **The drive is never written:** the listing only reads (no `mkdir` under `GAMES_DIR`; `_scan`'s generic `mkdir` is
  not run for `ps2`); the launch reads the title through PCSX2 and the BIOS folder once (the copy below).
- **On the hub** (`data/games/ps2/`, gitignored): `config/` (PCSX2's `-datapath`; its ini at
  `config/PCSX2/inis/PCSX2.ini`, as the probe found), `memcards/`, `sstates/`, `bios/`.

## 2. The launch kind `pcsx2` (`companion/ps2_session.py` new; thin hooks in `EmulatorManager`)

- `EmulatorManager.launch(game, …)`: for `game["system"] == "ps2"` **with the flag on**, `_launch_pcsx2(game,
  players_chosen)`; with the flag absent, today's path (which refuses: no `ps2` profile). `_launch_kind = "pcsx2"` is
  set for the session and cleared where the session state is cleared.
- **The BIOS copy, once:** if `data/games/ps2/bios/` holds no file, every regular file of `BIOS_DIR` is copied there
  (`copy2`, read-only on the drive); never overwritten later (the NVRAM then evolves on the hub). The ini's `BIOS` name
  is kept from the existing ini when that file is in the hub copy, else the single 4-MiB file there, else the single
  `.bin`; else the launch refuses. No name in any record.
- **The ini written per launch**, merged into the existing one (PCSX2's other keys kept):
  - `[UI]` StartFullscreen / SetupWizardIncomplete false / ConfirmShutdown false / HideMouseCursor / PauseOnFocusLoss
    false / StartPaused false;
  - `[Folders]` Bios / MemoryCards / Savestates (absolute hub paths);
  - `[Filenames] BIOS`;
  - `[EmuCore]` EnableDiscordPresence false, EnablePINE true, PINESlot 28011, SaveStateOnShutdown false,
    EnableFastBoot true;
  - `[EmuCore/GS]`:
    - Renderer 14 (Vulkan), upscale_multiplier 1;
    - Adapter = the existing value when it names AMD / RADV, else the first `vulkaninfo --summary` device naming RADV /
      AMD, else left as is and the game log says so;
    - the performance overlay off (OsdShowSpeed / FPS / VPS / CPU / GPU / Resolution false);
  - `[AutoUpdater] CheckAtStartup` false;
  - `[InputSources]` SDL true, Keyboard true (the hotkey), Mouse false;
  - `[Hotkeys] TogglePause = Keyboard/Space`;
  - `[Pad]` the multitap; `[Pad1]`-`[Pad8]` from S4.
- **The command:** `<AppImage> -datapath <abs data/games/ps2/config> -nogui -fullscreen -- <abs title>`:
  - the environment is the companion's, plus `SDL_GAMECONTROLLERCONFIG`;
  - `start_new_session`;
  - stdout / stderr into the game log.
- **The game log** (`logs/games/<ts>-ps2.log`): it names neither the id nor the title (today's RetroArch log names both
  in its filename and lines; the PS2 log does not). The lines:
  - `PS2 launch: pcsx2 players=<n> multitap=<bool>`;
  - `PS2 pause: hotkey|sigstop`, `PS2 resume: hotkey|sigcont`;
  - `PS2 exit: sigterm <s>s|sigkill`.
- **The window:** the launch waits ≤ 30 s for `xdotool search --onlyvisible --pid` (the same search the capture uses),
  then returns; the plugin's paused handoff follows (S2).
- **The exit:** SIGCONT if paused by SIGSTOP; SIGTERM to the started PID; wait 5 s; else SIGKILL (and wait 2 s).
- The capture and the sink: unchanged (by the started PID, H3-P1 P0b / P0c).
- `players_session` / B46's `ports_set`: the plan for `ps2`.

## 3. The list (`plugins/games.py`)

- With the flag, the plugin's `SYSTEMS` gains `ps2` ("PlayStation 2") as an instance attribute; without it the class
  dict is used as today.
- `_scan` handles `ps2` with `ps2_session.list_titles(GAMES_DIR)`:
  - read-only, recursive; hidden names skipped;
  - `.chd` / `.iso` / `.cue` listed; a `.bin` is never listed itself, and a `.cue` whose `FILE` entries do not all
    exist is skipped;
  - a stem present more than once in one folder is listed once, by `.chd` > `.iso` > `.cue`.
- Each title gets `relative_path` `ps2/<path inside GAMES_DIR>` (not under `games/`, so the cheat / mod / sidecar code
  sees nothing). The launch resolves it under `GAMES_DIR` and refuses anything escaping it.

## 4. The rows

- At `native-stream-start` for a PS2 session: the response `ps2_mode: true`, and a recovery row `ps2_session` with
  `ps2_mode: true` and `save_states: "off"` listing the four behaviours (S3).
- Every heartbeat row of the session: `ps2_mode: true` (the heartbeat log copies it).
- S3's skip rows carry `ps2_mode: true`.

## 5. The P2 metric for A (`tools/ps2_p2_frames.py`, new)

- **The input:** ffmpeg's `showinfo` log of a 60-fps `x11grab` capture **with every frame** (no `mpdecimate`): per
  frame `pts_time`, `checksum`, `mean` (Y).
- **Per second:**
  - unique = frames whose checksum differs from the previous frame's;
  - corrected = unique plus the **isolated single repeats** (a frame equal to the one before, while the one after
    differs: the 59.94-on-60 beat);
  - a second is **static / black** when ≥ 90 % of its frames are near-black (Y mean ≤ 24) or its unique count ≤ 2.
- **Out:** the median of unique over all full seconds; the corrected minimum over the seconds that are not static /
  black; the excluded seconds' count; `--pcsx2-fps <v>` printed beside (A reads PCSX2's own counter with the overlay
  on).
- **A's bars, pre-registered:** median ≥ 59, corrected minimum ≥ 55.
- No path or title is read or printed beyond the input file given.

## 6. Tests (`tests/ps2_session/`, fakes only; no real folder in any test or fixture)

- the flag;
- the paths file parse (two keys only, missing → none);
- the AppImage pick (one / none / two);
- the command from a fake config (no real path);
- the ini: written keys, kept foreign keys, the overlay off, the adapter rules with a fake `vulkaninfo`;
- the four pads' lines in creation order, with multitap true / false and 1 / 2 / 4, and the SDL line exactly;
- the BIOS copy once (not overwritten; the source tree unchanged);
- the list: dedupe, `.chd` preferred, `.bin` without `.cue` skipped, `.cue` with a missing `.bin` skipped, hidden
  skipped, nothing created in the source tree;
- `SYSTEMS` with and without the flag;
- `_scan` / `systems` unchanged without the flag;
- the launch hook: a fake ps2 game with the flag absent → today's refusal, with it → `_launch_pcsx2` with a fake
  Popen;
- pause / resume via fake PINE + fake xdotool (hotkey confirmed; PINE unreachable → SIGSTOP / SIGCONT; the hotkey not
  confirmed → SIGSTOP);
- the exit (SIGTERM in time; SIGKILL after 5 s);
- S3's four skips with their rows;
- the heartbeat's `ps2_mode`;
- `players_session.plan("ps2", …)`;
- `controller_profile` for ps2;
- the analyzer on synthetic showinfo logs (black seconds excluded, single repeats corrected, a real drop kept).

**Absent → today:** without `PRIVYHUB_PS2` no new import at plugin load, `SYSTEMS` is the class dict, the scan and
the node tree are the same, a `ps2` launch is today's refusal, and nothing under `data/games/ps2/` is touched.
