# B69 — design, written before any B69 code (H2: the `dolphin` launch kind, behind `PRIVYHUB_GAMECUBE=1`)

Queue: `handoffs/QUEUE_2026-11-09Y.md` §B69. Baseline `9db5a35c` (H2-P1 committed, the tree clean). Built in
`/tmp/b_q17y_b69` (companion/, tools/, tests/, PrivyHub/ only; `/tmp/b_q17y_base` is the baseline copy); the tree
gets the diff at the end, uncommitted. **Dolphin is not started** (not even `--help` / `--version`: H2-P1's
`stage1/help.txt` already holds them); nothing fetched; nothing written to the drive; no title, serial, game id or
path in any record (the drive's folder by role only).

## 0. Settled (read on the hub, read-only)

**(1) Dolphin's own names, read from the AppImage without running it** (`7z x -so … usr/bin/dolphin-emu | strings`;
the squashfs read as an archive; scratch output under `/tmp/b69_scratch/`, removed at the end):
- **the evdev input names:** the classes `evdev::NamedButton`, `NumberedButton`, `NamedButtonWithNoBackwardsCompat`,
  `Axis`, `AnalogInput`; the format strings `Button {}` (the numbered fallback) and `Axis {}{}` (index, sign); the
  prefixes `BTN_` / `KEY_` beside the button code (stripped). So a button is libevdev's code name without `BTN_`, an
  absolute axis is `Axis <n>+` / `Axis <n>-` by its order among the device's axes, and
  `Device::AddFullAnalogSurfaceInputs` / `FullAnalogSurface` give the whole-range `Axis <n>-+`;
- **libevdev's code names** (the AppImage bundles `libevdev.so.2`; its name table lists `BTN_SOUTH`, `BTN_EAST`,
  `BTN_NORTH`, `BTN_WEST`, `BTN_TL`, `BTN_TR`, `BTN_START` first and `BTN_A` … `BTN_Y` only in its alias table; the
  hub's own libevdev 1.13.4, called through `ctypes`, returns `BTN_SOUTH` … `BTN_THUMBR` for the pad's ten codes);
- **the device line** `Added device: {}` / `Removed device: {}` (ControllerInterface, log type `CI` in `Logger.ini`),
  and `evdev combining devices with unique id: {}, physical location: {}` (only devices that share a unique id;
  python-evdev's uinput pads set none);
- **the log line format** `{:%M:%S}:{:03} {}:{} {}[{}]: {}` (minutes:seconds:ms, file:line, level letter, type),
  `Booting from disc: {}`, the file `Logs/dolphin.log`;
- **the state messages** `Saved State to {}` / `Loaded State from {}` are on-screen messages (`Core::DisplayMessage`,
  recalled), **not log lines**: no log confirmation exists for a state, so a save is confirmed by its file and a load
  by B52's picture check (as H2-P1 measured);
- **the hotkey names** `Toggle Pause`, `Save State Slot 1` … `10`, `Load State Slot 1` … `10`; the config keys
  `BackgroundInput`, `PauseOnFocusLost`, `OnScreenDisplayMessages`, `ShowFPS`, `LogRenderTimeToFile` and every key
  of H2-P1's list are present as strings.

**(2) H2-P1's own files in the user dir** (gitignored, read only): Dolphin 2609b kept the probe's whole
`Hotkeys.ini` (four lines, its mtime the probe's write) and wrote `Dolphin.ini` / `GFX.ini` back with H2-P1's keys.
**A present `Hotkeys.ini` is taken whole: only its lines are bound** (Dolphin's defaults apply only when the file is
absent — recalled from `InputConfig::LoadConfig`, consistent with the probe: its F10 / Shift+F1 / F1 worked with no
other binding written). `Logger.ini` lists every log type of 2609b (the list is copied into the code: names only).
The probe's `dolphin.log` (35 KB per run, Verbosity 4) holds 3 `E[COMMON]` / 6 `W[COMMON]` translation lines on every
start (`Translation.cpp`), the boot line, and a `W[COMMON]: Delete: …` line on a save over an existing slot.

**(3) The companion's pads** (`native_session_io`): uinput "PrivyHub Virtual Gamepad P1" … "P4", one name each, so
Dolphin numbers each `evdev/0/…` (the index counts devices of the same source and name). Buttons `BTN_SOUTH` ← the
onn's ✕, `BTN_EAST` ← ○, `BTN_WEST` ← □, `BTN_NORTH` ← △, `BTN_TL` / `BTN_TR` ← L1 / R1, `BTN_SELECT`, `BTN_START`,
`BTN_THUMBL` / `BTN_THUMBR`; axes in code order `ABS_X` 0, `ABS_Y` 1 (up negative), `ABS_Z` 2 (L2, 0-255),
`ABS_RX` 3, `ABS_RY` 4 (up negative), `ABS_RZ` 5 (R2, 0-255), `ABS_HAT0X` 6, `ABS_HAT0Y` 7 (−1 / 0 / 1, up negative).

## 1. The decisions

**(1) The per-launch config: written whole, every launch** (not `-C`). Five files under
`data/games/gamecube/user/Config/`, each written to a temp name and renamed, replacing what Dolphin wrote last time:
- **why whole:** one known state per launch; nothing a previous run (or Dolphin's own exit save) left carries over;
  the input files (`GCPadNew.ini`, `Hotkeys.ini`) cannot go by `-C` anyway; and `-C`'s system name for `GFX.ini` was
  not proven by H2-P1. The command stays H2-P1's: `<AppImage> -b -u <user dir> -e <title>`;
- **`Dolphin.ini`:** `[General] UseDiscordPresence = False`; `[Interface] ConfirmStop = False`,
  `UsePanicHandlers = False`, **`OnScreenDisplayMessages = False`** (no "Saved State to <file>" text on the TV; H2-P1
  had it on), `PauseOnFocusLost = False`; `[Display] RenderToMain = True`, `Fullscreen = True`; `[Core]
  CPUThread = True`, `SkipIPL = True`, `GFXBackend = Vulkan`, `SIDevice0-3 = 6`, `SlotA = 8`, `SlotB = 255`,
  `EnableCheats = False`; `[DSP] Backend = Cubeb`, `DSPThread = True`; **`[Input] BackgroundInput = True`** (the pads
  and the hotkeys read whatever window has X focus; the hotkey path still focuses the window first, as H2-P1);
  `[Analytics] PermissionAsked = True`, `Enabled = False`; `[AutoUpdate] UpdateTrack =` (empty);
- **`GFX.ini`:** `[Hardware] Adapter = 0` (RADV, as H2-P1 read it); `[Settings] InternalResolution = 1`,
  `ShaderCompilationMode = 2`, `WaitForShadersBeforeStarting = True`, **`ShowFPS = False`**,
  `LogRenderTimeToFile = True` (Dolphin's `render_times` / `vblank_times`, the counter beside the metric);
- **`Hotkeys.ini`** (whole, so no Dolphin default is bound: no Stop on Escape, no fullscreen toggle, no screenshot, no
  other slot): `Device = XInput2/0/Virtual core pointer` (H2-P1's), `General/Toggle Pause` = F10; save / load for the
  slots in use only — **1, 2, 3** (PrivyHub's SAVE / LOAD), **8** (the give-up save), **9** (the hold / stall scratch):
  `Save State/Save State Slot n = @(Shift+`F<n>`)`, `Load State/Load State Slot n = `F<n>``;
- **`GCPadNew.ini`** (§(2));
- **`Logger.ini`:** `Verbosity = 4`, `WriteToFile = True`, console / window off; `BOOT`, `CORE`, `VIDEO`, `AUDIO`,
  `COMMON`, **`CI`** on (the device lines), every other type of 2609b's list off.

**(2) The pads — `GCPadNew.ini`, `[GCPad1]` … `[GCPad4]`, `Device = evdev/0/PrivyHub Virtual Gamepad P<n>`:**

| GameCube | Dolphin input | the onn's pad |
| --- | --- | --- |
| A | `SOUTH` | ✕ |
| B | `WEST` | □ |
| X | `EAST` | ○ |
| Y | `NORTH` | △ |
| Z | `TR` | R1 |
| Start | `START` | Start |
| Main Stick up / down / left / right | `Axis 1-` / `Axis 1+` / `Axis 0-` / `Axis 0+` | the left stick |
| C-Stick up / down / left / right | `Axis 4-` / `Axis 4+` / `Axis 3-` / `Axis 3+` | the right stick |
| L-Analog / R-Analog | `Axis 2-+` / `Axis 5-+` | L2 / R2, the whole travel |
| L / R (the click) | `Axis 2-+` / `Axis 5-+` | L2 / R2 past Dolphin's trigger threshold (its default, 90 %) |
| D-Pad up / down / left / right | `Axis 7-` / `Axis 7+` / `Axis 6-` / `Axis 6+` | the D-pad |

L1, Select and the stick clicks are unbound. Every input is written in backticks. **Recalled, read at the TV:** the
device index (`evdev/0`), the axis numbering, the full-range trigger name and the trigger threshold. **The check:**
after the launch the companion reads Dolphin's per-launch log for `Added device: evdev/<n>/PrivyHub Virtual Gamepad
P<k>` and writes `GC pads: …` (the four seen and their index, or "none yet") to the game log and the `gc_session` row,
so a mismatch (any index but 0, or a different name form) is read at the first launch → the fix is the ini's device
line.

**(3) The pause path** (`gamecube_session.Session`, PS2's shape with PINE replaced by the thread clock):
- **the clock:** the thread whose `comm` is `CPU thread` under `/proc/<pid>/task/`, its `utime + stime` ticks;
- **the hotkey:** `xdotool windowactivate --sync <wid>`, `windowfocus --sync <wid>`, `keydown <keys>`, 0.12 s,
  `keyup <keys reversed>` (H2-P1's exact sequence), the window being the PID's visible one (the capture's search);
- **pause:** F10, then **confirmed when the clock stands for a 0.5-s window**, polled every 0.05 s, the window
  starting within 1.5 s of the key → `hotkey`. **No clock** (no `CPU thread`, or unreadable) or no window → **SIGSTOP**
  with no key sent; **an unconfirmed key** → SIGSTOP, no second key → `sigstop`;
- **resume:** the way it was paused. `hotkey` → F10, confirmed when the clock **grows by ≥ 2 ticks within a 0.5-s
  window** (running used 13-36 ticks a second in H2-P1); unconfirmed → one more F10 only if the clock still stands;
  still not → an error. `sigstop` → SIGCONT, then (with a clock) the growth check; a clock that still stands means a
  late key paused Dolphin → one F10, confirmed → `sigcont+hotkey`;
- **for a state key** (`ensure_hotkey_pause`): a SIGSTOP-paused Dolphin cannot read keys → SIGCONT, F10, the stand
  check → `hotkey`; else SIGSTOP again and an error (PS2's `ensure_pine_pause`);
- **the paused handoff after the launch:** the launch returns only after **(a)** the PID's window (≤ 30 s), **(b)** the
  shader pre-compile window: the `CPU thread` exists and its clock has grown (≤ 90 s; with
  `WaitForShadersBeforeStarting` the emulation starts only after the pre-compile), and **(c)** the PID's sink-input
  (≤ 45 s, B50's lesson). Then the plugin's start pauses it as every session (the hotkey, confirmed). A bound missed in
  (b) or (c) is logged and the launch goes on (PS2's (c) rule).

**(4) States** (Dolphin's files `user/StateSaves/<game id>.s0<n>`; the id is never read or logged by PrivyHub — the
file is found by its slot suffix and its change):
- **SAVE (slots 1-3):** `ensure_hotkey_pause` if SIGSTOP-paused; the folder snapshot (name → mtime ns, size, inode);
  Shift+F<n>; **confirmed when a `*.s0<n>` file is new or changed since the snapshot, non-empty, and its size and
  mtime stand for 0.25 s, within 1.0 s of the key** (H2-P1: stable ≤ 0.21 s; Dolphin writes a temp file and renames
  it). Then the slot index as PS1's and **the PS1-shaped reply** (`accepted`, `confirmed`, `replaced_existing`,
  `slot_detail`, `state_file`, `control: dolphin_hotkey_save_state`, `hotkey: Shift+F<n>`). Not confirmed → "PrivyHub
  could not verify the saved GameCube state", the game left paused;
- **LOAD (slots 1-3):** only paused (PS1's rule); the slot's file must exist; `ensure_hotkey_pause`; the CPU thread
  must exist (else "The game is still starting…"); the picture before; F<n>; 0.5 s for Dolphin's hotkey thread to
  finish the load; resume (the hotkey, confirmed); **B52's picture check** (≥ 3 distinct grabs of the PID's window,
  not the pre-load one, one not black, the clock growing, within 5 s); pause again. `ok` → the PS1-shaped reply
  (`verification: picture`, `paused: true`, `control: dolphin_hotkey_load_state`); else "The game did not resume from
  the save", **the game paused**. **Disclosed:** H2-P1 measured the save and the load with the game running; the
  paused save and load (Dolphin runs a state on its CPU thread either way, recalled) are read at C35;
- **which recovery uses go live** (the save is 0.21 s, inside every budget):
  - **the hold's return — live:** the scratch save at the quiet mark is Shift+F9 into the running game (H2-P1's
    path); at the release: the slot-9 file stable within B55's 0.45-s share, `ensure_hotkey_pause`, F9, the release
    row, then **B52's picture check after the recovery's resume** in a verifier thread (static → the PS1-shaped
    `rewind_failed` row), as B55's PS2 path;
  - **the stall resume — live:** the same release path (B12's load goes through it);
  - **the give-up — live:** Shift+F8 → the file (5-s bound: no one waits on it), the recovery index as PS1's,
    `gave_up_saved` with `gc_states: hotkey`; the prompt's Resume in a fresh launch: running, the CPU thread up,
    `ensure_hotkey_pause`, F8, resume, the picture check, left running; the copy to a user slot (`.s08` → `.s0<n>`,
    verified by sha256, indexed);
  - **the relaunch — not live:** four native ports never relaunch (`relaunch_ports` refuses a GameCube session;
    `save_relaunch_state` refuses);
  - **the rewind — off** (`rewind_skipped`, "gamecube: no rewind in Dolphin", in the rewind method only).

**(5) Four native ports:** every GameCube launch sets `SIDevice0-3 = 6` and the plan `{players_chosen 4, ports 4,
multitap false, multitap_available false, device_args [], source "gamecube"}` (N64's shape), whatever the pick or the
join; the plugin's join marking (`source: join`) applies as for every launch. `players_session.ports_set` accepts the
source `gamecube`. Hold-to-join fills P1-P4 with no relaunch; `capable` never set.

**(6) The listing:** `gamecube` ("GameCube") in place from `GAMECUBE_DIR=` in the gitignored paths file
(`inplace_library.read_dir`, that key only); `.rvz` > `.gcm` > `.iso` > `.ciso`, one per folder + stem, hidden names
skipped, read-only, no `mkdir`. **The small `.bin` is skipped by its suffix (never opened)**, and any candidate under
1 MiB is skipped by its size (stat only). No disc-header read (no Wii check; H2-P1's 27 are GameCube; disclosed).
`inplace_library` is not changed.

**(7) Exit:** SIGCONT if SIGSTOP-paused, SIGTERM to the started PID, ≤ 5 s, else SIGKILL (≤ 2 s); the game log
`GC exit: sigterm <s>s helper=<n>` (the processes still in the started PID's session: the AppImage's FUSE helper).
**The next GameCube launch waits ≤ 10 s for that session to empty, then SIGKILLs what is left** (the bound; a killed
helper can leave a stale mount, logged), before its Popen. The stop's reply is not held for the helper.

**(8) Rows and logs:**
- **the game log** `logs/games/<local ts>-gamecube.log`, each line UTC-stamped, no title / id / path: `GC launch:
  dolphin ports=4 backend=vulkan adapter=0 config=whole`, `GC helper: …`, `GC dolphin-log: <name>`, `GC window: <s>`,
  `GC boot: cpu thread <s>|none`, `GC audio: sink-input <s>|none`, `GC pads: …`, `GC pause: hotkey|sigstop`,
  `GC resume: hotkey|sigcont|sigcont+hotkey`, `GC save: slot <n> …`, `GC load: slot <n> … picture <verdict>`,
  `GC state save / load: slot 9 …`, `GC recovery save / load: slot 8 …`, `GC exit: …`;
- **the start response** `gc_mode: true`; **the `gc_session` recovery row** at each stream start (`gc_mode`,
  `gc_states: hotkey`, `live: [state_save_slot9, hold_return_load, stall_resume_load, recovery_save]`,
  `off: [rewind, relaunch]`, `pads: …`); `gc_mode` on every heartbeat row (copied by `native_stream_heartbeat`);
- **Dolphin's log per launch:** `user/Logs/dolphin.log` is made a symlink to
  `data/games/gamecube/logs/<YYYYmmddTHHMMSSZ>-dolphin.log` (created empty) before the Popen; at the exit, if Dolphin
  replaced the link by a file, the file's text is appended to the per-launch log; `render_times.txt` /
  `vblank_times.txt` are moved beside it as `<stamp>-render_times.txt` / `<stamp>-vblank_times.txt`; names older than
  30 days are pruned at each launch (B53's rule);
- **the keeper** (`trip_log_keeper` / `diag_keeper`): a `<ts>-gamecube.log` is a game log; the per-launch
  `-dolphin.log` files are copied as `raw/gclogs__<name>/` from their first byte (B53's shape), tails resumed across
  the keeper's restarts. Live at the keeper's next restart (B does not restart it); `diag_read` reads the live logs
  meanwhile;
- **`diag_read`:** a `-gamecube.log` launch reads title "GameCube", core `dolphin`; a session within 120 s after a
  `gc_session` row is a GameCube session (B50's rule); its row gains **`system: "gamecube"`** and **`dolphin_log`** =
  `boot`, `pad_added`, `pad_removed`, `error`, `warning` (the two levels without `Translation.cpp`'s start lines),
  counted from the previous session's end (or the launch) to this session's end; the line times from the file's UTC
  launch time + `MM:SS` unwrapped forward (whole-hour time zones; disclosed). A GameCube session is never a PS1
  reference. The Markdown gains `## Dolphin logs (B69)` only when such a row exists. `diag_check`'s last-session line
  (B66) covers `gamecube`.

**(9) The metric:** `tools/gc_frames.py`:
- `showinfo` (a capture, as `n64_frames`) and/or `--render <render_times.txt>` (Dolphin's presented frames, cumulative
  ms → per-second counts): each kept second snapped to 30 / 60, runs of one rate ≥ 5 s are segments, shorter runs and
  the edges dropped as transitions; **each segment read by `n64_frames.analyze(..., internal_fps=rate)`** (capture) or
  the same bar on Dolphin's counts (`< 5/6` of the rate is a hitch second);
- `--vblank <vblank_times.txt>` beside: VIs per second, p50 / p95 / p99, intervals > 34 ms and > 100 ms (optionally a
  `--window START:END` in Dolphin's own seconds). Numbers only.

**The hooks** (all behind `PRIVYHUB_GAMECUBE=1`; **absent: nothing imported, `SYSTEMS` unchanged, a `gamecube`
title refused as today (no emulator profile), nothing under `data/games/gamecube/` touched**):
- `companion/gamecube_session.py` (new);
- `games/emulator_manager.py`: the import, the class defaults `_gc` / `_gc_helper_sid`, the `dolphin` branch before
  the RetroArch path in `launch`, the pause / resume / stop / save / load / recovery / copy / relaunch branches, the
  catalog's Core default for `gamecube`, the resets;
- `plugins/games.py`: the import, `SYSTEMS`, the scan, `gc_mode` + `gc_session` on the start, `gc_mode` on heartbeats;
- `players_session.py` (the `gamecube` source), `relaunch_ports.py` (the refusal), `hold_rewind.py` (the rewind skip),
  `rewind_cores.py` (the slot-9 save and release), `games/link_drop_recovery.py` (`gc_states`),
  `games/native_stream_heartbeat.py` (`gc_mode`) — each line reached only by a `dolphin` session;
- `tools/diag_read.py`, `tools/trip_log_keeper.py`, `tools/diag_keeper.py`, `tools/diag_check.py` (the label, the
  logs); `tools/gc_frames.py` (new).

## 2. Tests (`tests/gamecube_session/`; fakes only — a fake Popen, a fake `/proc` tree with a `CPU thread` stat, a fake
`xdotool` / `pactl` runner, a fake `StateSaves/` writer, a fake grab; temp dirs removed at exit; the real folder never
used)

- the flag and the paths key; the AppImage pick; the list (rank, one per stem, hidden, the `.bin` and the < 1 MiB
  skipped, nothing written, no folder → []); the resolver's refusals;
- the command from a fake config; the five files written whole with the expected keys (H2-P1's, `ShowFPS = False`,
  the hotkeys and nothing else, `BackgroundInput`), a stale key from a previous file gone;
- `GCPadNew.ini` for four fake pads (the device lines, the layout table, backticks);
- pause confirmed by a fake thread clock (stands → `hotkey`); a silent clock → SIGSTOP with no key; an unconfirmed key
  → SIGSTOP, no second key; resume by hotkey (grows), the one retry, SIGCONT, `sigcont+hotkey`;
- SAVE → Shift+F<n> → the file check → the PS1-shaped reply; a file that never stands → the error;
- LOAD → F<n> → the picture check → confirmed; static → the error with the game paused; not paused → refused;
- the hold's slot-9 save and release through the reserved slot (the row, the verifier's static row); the give-up
  save (index, `gc_states`), the recovery load and copy; the relaunch refused;
- four ports from `players_joined` 1 / 3 / none, no relaunch; `ports_set` reads the plan;
- the list with and without the flag (fresh interpreters: `0` / absent / `1`); the drive's tree unchanged; absent →
  today's refusal, nothing under `data/games/gamecube/` made;
- the exit: SIGTERM, the helper count, the next launch's helper wait and its SIGKILL bound;
- the game log's lines and no title / id / path; the `gc_session` row, `gc_mode` on the start and heartbeats (none
  without the flag or for a RetroArch session);
- Dolphin's log per launch (the symlink, the fallback append, the render / vblank moves, the 30-day prune); `diag_read`
  (the label, the counts in the window), the keeper copying a new `-dolphin.log`; `gc_frames` (two segments, a
  transition dropped, a hitch counted, the vblank summary).

**Mutations** (each must fail a test): the pause key sent with a silent clock; the plugin importing without the flag;
the rewind skip removed; the `.bin` / size skip removed; the save confirmed before the file stands.

**Proof absent = today:** every touched file's new lines are reached only through `_gc` / `_gc_session` (None without
the flag), `_launch_kind == "dolphin"`, a `gamecube` source / system, a `-gamecube.log` / `-dolphin.log` name or the
`gc_session` row; the hooks test runs the plugin and the manager in fresh interpreters with the flag absent and `0`;
every host suite in the copy as the baseline copy.

## 3. Not built / for A

- Not built: a Wii-disc check, multi-disc `.m3u` for GameCube, Dolphin's IPL, a keep-awake (H2-P1: none needed),
  `CursorVisibility` (the encoder's cursor handling as today), any APK change (no client file is touched; the "Change
  disc" entry and any GameCube string stay listed for the next APK).
- **Read at the TV (C34-C36):** the pad device names in Dolphin's log, the layout, the paused save / load, the first
  boot's pre-compile seen through the stream, the per-segment fps with Dolphin's counter beside.
