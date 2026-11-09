---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: 9db5a35c (H2-P1 committed, the tree clean; B69 built in /tmp/b_q17y_b69 and applied to the tree, uncommitted)
---

# B69 — the GameCube launch kind (Dolphin), behind `PRIVYHUB_GAMECUBE=1`

**Classification: SETTLED + BUILT**, host only (no client change, no APK item).
- **Tests:** `tests/gamecube_session` 54 green ×3 (no temp dir left); every host suite as the baseline copy
  (67 entries each; the B69 copy adds only the new suite).
- **Mutations:** 5 / 5 caught.
- **Proof:** absent = today, hunk by hunk (`b69_2026-11-09/proof_flag_absent.md`).
- NOT ADOPTED (no drop-in written). **Dolphin not started by B** (not even `--help` / `--version`: H2-P1's
  `stage1/help.txt` holds them); nothing fetched; nothing written to the drive; nothing committed.

Design `b69_2026-11-09/design_written_before_code.md`, sha256 `a717ed68…0b57`, hashed **02:55:55Z, before any B69
code**. Precondition met: only the companion and `privyhub-diag` active; `git status --short` empty (H2-P1 committed,
HEAD `9db5a35c`).

## 0. Settled (read-only)

- **Dolphin's own names, read from the AppImage as an archive** (`7z x -so … usr/bin/dolphin-emu | strings`; nothing
  run):
  - evdev inputs: `NamedButton` (libevdev's code name with `BTN_` / `KEY_` stripped), `Button {}` as the fallback,
    `Axis {}{}` (the axis's order and its sign), and `FullAnalogSurface` (`Axis <n>-+`, the whole travel);
  - the device lines `Added device: {}` / `Removed device: {}` (log type `CI`);
  - the log line format `{:%M:%S}:{:03} {}:{} {}[{}]: {}`;
  - the hotkey names `Toggle Pause`, `Save State Slot 1-10`, `Load State Slot 1-10`;
  - the keys `BackgroundInput`, `PauseOnFocusLost`, `OnScreenDisplayMessages` and every H2-P1 key.
- **libevdev's names:** `BTN_SOUTH` / `EAST` / `NORTH` / `WEST` / `TL` / `TR` / `START` lead the bundled library's name
  table (`BTN_A` … only as aliases). The hub's own libevdev 1.13.4 returns `BTN_SOUTH` … `BTN_THUMBR` for the pad's ten
  codes.
- **States have no log line:** `Saved State to {}` / `Loaded State from {}` are on-screen messages, so a save is
  confirmed by its file and a load by B52's picture check (as H2-P1 measured).
- **H2-P1's own `Hotkeys.ini`** (four lines) was kept whole by Dolphin 2609b, so a file written whole binds only its
  own lines.
- **The companion's pads:** "PrivyHub Virtual Gamepad P1-P4", one name each → `evdev/0/…` for each. ✕ → `BTN_SOUTH`,
  ○ → `EAST`, □ → `WEST`, △ → `NORTH`, R1 → `TR`; axes in code order X 0, Y 1, Z 2 (L2), RX 3, RY 4, RZ 5 (R2), hat 6 / 7.

## 1. Built (`b69.diff`, 17 files; `companion/gamecube_session.py` new)

1. **The config: written whole, every launch** (not `-C`). Five files in `data/games/gamecube/user/Config/`, each to a
   temp name and renamed:
   - `Dolphin.ini`: H2-P1's keys (`CPUThread`, `SkipIPL`, Vulkan, `SIDevice0-3 = 6`, `SlotA = 8`, `RenderToMain`,
     `Fullscreen`, `ConfirmStop` / panic handlers off, analytics asked and off, `UpdateTrack` empty, Cubeb), plus
     **`OnScreenDisplayMessages = False`** (no "Saved State to …" text on the TV), `PauseOnFocusLost = False` and
     **`[Input] BackgroundInput = True`** (the pads and the hotkeys work whatever window has focus);
   - `GFX.ini`: `Adapter = 0` (RADV), native resolution, `ShaderCompilationMode = 2`, `WaitForShadersBeforeStarting`,
     **`ShowFPS = False`**, `LogRenderTimeToFile = True`;
   - `Hotkeys.ini`: **only** F10 (pause) and Shift+F<n> / F<n> for slots 1, 2, 3, 8, 9. No Dolphin default is bound
     (no Stop on Escape, no fullscreen toggle, no screenshot);
   - `GCPadNew.ini` (item 2); `Logger.ini`: Verbosity 4 to the file, `BOOT` / `CORE` / `VIDEO` / `AUDIO` / `COMMON` /
     **`CI`** on, the other 2609b types off.
   - **Why whole:** one known state per launch; the input files cannot go by `-C`; `-C`'s system name for `GFX.ini` is
     unproven. The command stays H2-P1's: `-b -u data/games/gamecube/user -e <title>`, `start_new_session`.
2. **The pads** (`[GCPad1-4]`, `Device = evdev/0/PrivyHub Virtual Gamepad P<n>`):

   | GameCube | the onn's pad |
   | --- | --- |
   | A / B / X / Y | ✕ / □ / ○ / △ (`SOUTH` / `WEST` / `EAST` / `NORTH`) |
   | Z | R1 (`TR`) |
   | Start | Start |
   | the main stick | the left stick (`Axis 0` / `1`) |
   | the C-stick | the right stick (`Axis 3` / `4`) |
   | L / R, analog and the click | L2 / R2, the whole travel (`Axis 2-+` / `5-+`); the click past Dolphin's threshold |
   | the D-pad | the D-pad (`Axis 6` / `7`) |

   L1, Select and the stick clicks are unbound. **The check:** after the launch and at each pause, the companion reads
   Dolphin's per-launch log for `Added device: evdev/<n>/PrivyHub Virtual Gamepad P<k>` and writes `GC pads: P1=evdev/0
   …`, or `none yet`, or `… MISMATCH (the ini names evdev/0)`, to the game log and the `gc_session` row.
3. **The pause path** (`Session`):
   - F10 by `xdotool` (`windowactivate --sync`, `windowfocus --sync`, keydown, 0.12 s, keyup), **confirmed when the
     `CPU thread`'s clock stands for a 0.5-s window** starting within 1.5 s;
   - a silent clock or no window → SIGSTOP with no key; an unconfirmed key → SIGSTOP, no second key;
   - resume the same way: F10 confirmed by ≥ 2 ticks of growth within 0.5 s; one more F10 if it still stands; SIGCONT
     for a SIGSTOP (then F10 if a late key had paused Dolphin as well: `sigcont+hotkey`);
   - a state key after a SIGSTOP pause: SIGCONT, then F10 confirmed first.
   - **The launch returns** after the window (≤ 30 s), **the shader pre-compile window** (the CPU thread up and its
     clock growing, ≤ 90 s) and **the sink-input** (≤ 45 s). Then the plugin's start pauses it as every session.
4. **States** (`user/StateSaves/<game id>.s0<n>`, found by its slot suffix and its change; the id is never read or
   logged):
   - **SAVE 1-3:** Shift+F<n>, **confirmed when the file is new or changed, non-empty and standing 0.25 s, within
     1.0 s**. Then the slot index and the PS1-shaped reply (`control: dolphin_hotkey_save_state`, `hotkey`). Else
     "PrivyHub could not verify the saved GameCube state".
   - **LOAD 1-3:** paused only; F<n>, 0.5 s, resume, **B52's picture check** (3 distinct grabs, not the pre-load one,
     not black, the clock growing, ≤ 5 s), pause again. Else "The game did not resume from the save", the game paused.
   - **Live:**
     - **the hold's return:** Shift+F9 at the quiet mark into the running game. The release: the file stable within
       0.45 s, F9, 0.2 s, the row, then the picture after the recovery's resume (static → `rewind_failed`);
     - **the stall resume:** the same path;
     - **the give-up:** Shift+F8, 5-s bound, the recovery index, `gc_states: hotkey` on `gave_up_saved`. The prompt's
       Resume: F8 and the picture, left running. Copy to a slot: verified by sha256.
   - **Not live:** the relaunch (`relaunch_ports` and `save_relaunch_state` refuse); **the rewind is off**
     (`rewind_skipped`, "gamecube: no rewind in Dolphin").
5. **Four native ports:** the plan `{ports 4, multitap false, multitap_available false, source gamecube}` on every
   launch, whatever the pick or the join; hold-to-join fills P1-P4 with no relaunch. No `capable`.
6. **The listing:** `gamecube` / "GameCube" in place from `GAMECUBE_DIR=` (`inplace_library`, unchanged): `.rvz` >
   `.gcm` > `.iso` > `.ciso`. The `.bin` is skipped by its suffix (never opened), anything under 1 MiB by its size. No
   disc-header read.
7. **Exit:** SIGCONT if stopped, SIGTERM, ≤ 5 s, else SIGKILL; `GC exit: sigterm <s>s helper=<n>`. **The next
   GameCube launch waits ≤ 10 s** for the old session's AppImage helper, then SIGKILLs what is left (`GC helper: …`).
   The stop's reply is not held.
8. **Rows and logs:**
   - the game log `logs/games/<ts>-gamecube.log`, UTC lines `GC launch / helper / dolphin-log / window / boot / audio /
     pads / pause / resume / save / load / state save / state load / recovery save / recovery load / exit`, with no
     title, id or path (a test checks);
   - `gc_mode` on the start response and every heartbeat; the `gc_session` row (`gc_states: hotkey`, `live`, `off`,
     `pads`);
   - **Dolphin's log per launch:** `user/Logs/dolphin.log` symlinked to
     `data/games/gamecube/logs/<UTC stamp>-dolphin.log`. If Dolphin replaced the link, its file is appended at the
     exit. The render / vblank counters are moved beside it; 30-day prune;
   - **the keeper:** `-gamecube.log` is a game log; `-dolphin.log` files copied as `raw/gclogs__<name>/`, the tails
     resumed. Live at the keeper's next restart;
   - **`diag_read`:** a GameCube session (a `gc_session` row ≤ 120 s before its start, or the launch order) reads
     "GameCube" / `dolphin`. Its row gains `system: gamecube` and `dolphin_log` = boot / pad_added / pad_removed /
     error / warning, without Translation.cpp's start lines; the line times are the launch hour + `MM:SS`, carried
     forward. The `## Dolphin logs (B69)` section appears only with such a row. `diag_check`'s last-session line
     covers `gamecube`.
9. **The metric** `tools/gc_frames.py`:
   - from a capture (`showinfo`) and/or Dolphin's `render_times.txt`: each second snapped to 30 / 60, runs of one rate
     ≥ 5 s are the segments, the edges and the short runs dropped;
   - a capture's segments are read by `n64_frames.analyze(…, internal_fps=rate)`; Dolphin's presented frames get the
     same 5/6 bar;
   - `--vblank` beside (VIs a second, p50 / p95 / p99, > 34 / > 100 ms; `--window`).

## 2. Tests (`tests/gamecube_session`, 54; `fake_dolphin.py`: a fake `/proc` clock, `xdotool` / `pactl`, a state writer, a grab)

- the list, the resolver, the paths key, the AppImage pick;
- the five files whole (a stale key gone), the hotkeys and nothing else, `GCPadNew.ini` for four pads, the layout
  against the companion's source;
- the pads read from a fake log (a mismatch named);
- pause / resume:
  - the hotkey confirmed by the clock; a silent clock → SIGSTOP, no key; an unconfirmed key → SIGSTOP once;
  - the late-key resume, the missed-key retry, a resume that never comes;
  - no window; the SIGSTOP → hotkey pause for a state key; the boot wait;
- the manager (in-process, `_gc` set as the flag sets it):
  - the command, the config, four ports from any pick, the log without title / id / path, the drive untouched;
  - the relaunch refused; unconfigured → no Popen; no window → SIGTERM;
  - the exit and the next launch's helper wait;
- SAVE (the reply, the index, a missing file, a file still changing at the bound); LOAD (confirmed, static → the error
  with the game paused, refused running or empty);
- the slot-9 save, the hold's and the stall's release, the static verifier row, no file → no load, the rewind off, the
  give-up / Resume / copy, `gc_states` on `gave_up_saved`;
- Dolphin's log (the link, the fallback, the counters, the prune); the helper count, its wait and the SIGKILL bound;
- **the hooks in fresh interpreters:** absent and `0` identical, today's refusal, nothing made; with `1` the list and
  the catalog;
- `gc_mode` / `gc_session` on the start and heartbeat (none without the flag or for a RetroArch session);
- the keeper copying a new `-dolphin.log`; `diag_read`'s events (the hour carried) and counts; `diag_check`;
- `gc_frames` (two segments, the transition seconds dropped, a hitch; render times; vblank).

**Mutations** (`tests_mutations.txt`), each in a fresh copy: M1 the pause key with a silent clock; M2 the plugin
importing without the flag; M3 the rewind skip removed; M4 the size skip removed; M5 the save confirmed before the
file stands. **All caught.**

**Regression:** every `tests/` suite and `tools/test_*.py` in the B69 copy and in the baseline copy
(`tests_host_b69.txt` / `tests_host_baseline.txt`): identical line for line (times aside), plus
`tests/gamecube_session`. The same six `tools/` tests fail in both copies (`test_adaptive_bitrate_live`,
`test_c3_f1_recovery_restart`, `test_c3_l4_nft_night`, `test_cl_b1_decoder_report_body`, `test_e1_remote`,
`test_fec_xor8_2`), as in earlier queues. From the tree after the apply: 18 touched suites OK
(`tests_in_the_tree.txt`). No JVM run: no client file changed. The runner and the mutation script are in
`b69_2026-11-09/scripts/`.

## 3. Known limits (read at the TV, HOME-9+GC)

- **Recalled, read back at C34:** the device index `evdev/0`, the axis numbering, `Axis <n>-+` for the triggers and
  the trigger threshold. The `GC pads:` line names a mismatch; the fix is `PAD_DEVICE` / `PAD_LAYOUT`.
- **The paused save / load:** H2-P1 measured both with the game running; PrivyHub's SAVE / LOAD come paused (C35).
- **`BackgroundInput`'s section** (`[Input]`) is recalled. If it is wrong, the H2-P1 focus sequence still precedes
  every key; the pads then need the window focused (it is fullscreen and the only window).
- **The pause confirmation needs ≥ 0.5 s** (the clock's stand window); the pause itself is the key.
- **The F10 after a load:** Dolphin's hotkey thread runs the load. A resume key pressed during it can be missed, hence
  the 0.5-s / 0.2-s settles and the one retry.
- **Not built:** a Wii-disc check, GameCube `.m3u`, an IPL, a keep-awake, `CursorVisibility`, any client change.

## Disclosed

- **`git_status_at_start.txt`** holds this record's own directory: it was made first, a moment before the status
  was written; `git status --short` was empty when checked (02:49Z), before any write.
- **`title_check.py`** (B68's, extended with the game ids in Dolphin's StateSaves / Cache file names): its first run
  flagged one of Dolphin's own Cache folder names (the RetroAchievements cache, also a log type in the code), not a
  title. The checker now loads file names only there; both checks then read 0 fails.
- **The tests' subprocess interpreters** wrote `__pycache__` under `companion/` in the tree (gitignored; as earlier
  queues).
- **The scratch** `/tmp/b69_scratch/` (the binary's strings, about 700k lines; the runner and the mutation script,
  copied into `scripts/` first) was removed at the end. It was my own, made this run.

## 4. Files

`b69_2026-11-09/`:
- `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`, `applied_to_tree_at.txt`;
- the design + `design.sha256` + `design_hashed_at.txt`;
- `b69.diff`, `diff_check.txt`, `proof_flag_absent.md`;
- `tests_x3.txt`, `tests_mutations.txt`, `tests_host_b69.txt`, `tests_host_baseline.txt`, `tests_in_the_tree.txt`;
- `scripts/` (`run_host.sh`, `mutate.py`), `units_before_apply.txt`;
- `redact_check.py` / `.txt`, `title_check.py` / `.txt`, `manifest.sha256`.

Patch note: `patches/B69_GAMECUBE_LAUNCH_KIND.md`.

**One line for the user:** on your controller, ✕ = A, □ = B, ○ = X, △ = Y, R1 = Z, L2 / R2 = L / R (press all the way
for the click), the left stick is the main stick, the right stick the C-stick, and Start and the D-pad are where they
are.
