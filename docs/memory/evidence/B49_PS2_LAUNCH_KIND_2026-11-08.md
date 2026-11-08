---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: f3f912c5 (the tree clean; B49 built in /tmp/b_q08p_b49 and applied to the tree, uncommitted)
---

# B49 — the PS2 launch kind (PCSX2), behind `PRIVYHUB_PS2=1`

**Classification: SETTLED + BUILT**, host only (no client change, no APK item).
- **Tests:** `tests/ps2_session` 35 green ×3; every host suite as the baseline copy.
- **Mutations:** 4 caught.
- **Proof:** absent = today, hunk by hunk (`b49_2026-11-08/proof_flag_absent.md`).
- NOT ADOPTED (no drop-in written); PCSX2 not started by B (no title, no BIOS read, no display); nothing fetched;
  nothing written to the drive; nothing committed.

Design `b49_2026-11-08/design_written_before_code.md`, sha256 `4d90fec5…d144d`, hashed **01:30:06Z, before any B49
code**. Precondition: only the companion and `privyhub-diag` active; the tree clean (HEAD `f3f912c5`).

## 0. Settled

1. **The onn's games list:** the host's `GamesPlugin.SYSTEMS` → `_scan` → `systems`' node tree (one lazy category per
   system). The onn renders the host's nodes and has **no hard-coded system set**, so `ps2` needs no client change and
   no APK. `details` needed one host change: `controller_profile` refused a system missing from `emulators.json`, and
   it now returns "Core default" for `ps2`.
2. **Pause / resume.** Today: the launch's paused handoff (`PAUSE_TOGGLE` until `GET_STATUS PAUSED`) → the stream's
   start → the client's ready → `resume()`; Back → `native-stream-stop` → `pause()`; Resume → a new start + ready; the
   recovery and stall paths use the same two calls. PCSX2 has no UDP command port. **Built:**
   - the `TogglePause` hotkey (`Keyboard/Space`) is sent with `xdotool windowfocus --sync <wid>` + `key space`, but
     only when PINE answers, and it counts only when PINE's status then reads the wanted state within 1.5 s;
   - otherwise SIGSTOP / SIGCONT;
   - the method is kept, so a SIGSTOP pause is always undone by SIGCONT;
   - the paused handoff after the launch goes the same way, after the launch waited ≤ 30 s for the PID's window.
   - PINE's protocol (opcode 0x0F, status 0 / 1 / 2, the socket `$XDG_RUNTIME_DIR/pcsx2.sock`) is **recalled**,
     tested only against a fake socket. If it is wrong on the hub, every pause is a SIGSTOP (the game log says which).
3. **The save-state behaviours, each off for a PS2 session** (disclosed per behaviour):
   - **the hold's rewind / state load** (`hold_rewind.Rewinder.rewind`): skipped, with a `rewind_skipped` row,
     `reason: "ps2_mode: no save states"` and `ps2_mode: true`. The hold itself still freezes the picture and resumes
     the game;
   - **the slot-9 scratch save** (`rewind_cores.Cores.save`): never sent (`saves_skipped_ps2`);
   - **the stall resume's load:** it goes through `Rewinder.rewind`, so the same skip; a stall resumes with no rewind;
   - **the link-drop give-up save** (`save_recovery_state`): skipped. `gave_up_saved` carries `ps2_mode: true,
     save_skipped: true`, and no recovery prompt follows;
   - **the player's slots and the recovery load / copy:** refused ("Save states are not available for a PS2 session").
4. **The pads:** the companion's uinput pad (0x1209 / 0x5048, version 1, USB; ten buttons, six axes and a hat) maps to
   one exact SDL line, passed to PCSX2 as `SDL_GAMECONTROLLERCONFIG`, with no file written. Its GUID is checked
   against `native_session_io`'s constants in a test.
   - `[Pad1..8]` use the DualShock 2 layout (`SDL-k/A` … the clickable sticks), with P1-P4 = SDL-0..3 in creation
     order. **The SDL open order and PCSX2's binding names are recalled;** A reads PCSX2's log of the opened
     controllers at H3-P2.
5. **The multitap:**
   - `players_chosen` 4 → `[Pad] MultitapPort1 = true`, players on 1A-1D = Pad1 / 3 / 4 / 5 (PCSX2's numbering,
     recalled), Pad2 none;
   - 1 / 2 / none → false, Pad1 (+ Pad2);
   - at launch only (B46's rule). `players_session.plan("ps2", n)`.
6. **The metadata default:** a PS2 title with no entry → 2 (B41's rule); no pick → Pad1 + Pad2.

## 1. Built (`b49.diff`, 10 files)

- **`companion/ps2_session.py`** (new):
  - **the folders:** `BIOS_DIR` / `GAMES_DIR` from the file `PRIVYHUB_PS2_PATHS` names, else `runtime/h3_p1_paths.txt`.
    Only those two keys are read, at run time.
  - **the AppImage:** exactly one in `runtime/emulators/pcsx2/`.
  - **the read-only list:**
    - `.chd` / `.iso` / `.cue`, one per folder + stem, `.chd` > `.iso` > `.cue`;
    - a `.bin` only through its `.cue`, and a `.cue` with a missing file skipped;
    - hidden names skipped; no `mkdir` on the drive.
  - **the title resolver:** refuses escapes and missing files.
  - **the BIOS copy:** once to `data/games/ps2/bios/`, never overwritten, so PCSX2's NVRAM write lands on the hub.
  - **the ini merge** (PCSX2's other keys kept):
    - fullscreen, no wizard, no shutdown prompt;
    - the hub folders and the BIOS name;
    - Discord off, PINE on, no save on shutdown;
    - Vulkan at 1x, the AMD / RADV adapter (the existing value, else `vulkaninfo --summary`), the performance overlay
      off;
    - no update check, SDL on;
    - the pause hotkey, the multitap and the pads.
  - **the command:** `-datapath <data/games/ps2/config> -nogui -fullscreen -- <title>`, `start_new_session`.
  - **`Session`:** pause / resume / exit (SIGTERM, 5 s, then SIGKILL).
- **`EmulatorManager`:** the import under the flag, the `pcsx2` launch branch, the pause / resume / stop branches, the
  six save-state guards, the controller catalog for `ps2`, and `_launch_kind` / `_ps2` (class defaults and resets).
  - **The game log** `logs/games/<ts>-ps2.log` has **no id, path or title** (a test checks), and its lines:
    - `PS2 launch: pcsx2 players=<n> multitap=<bool> adapter=named|unset`;
    - `PS2 pause: hotkey|sigstop`, `PS2 resume: hotkey|sigcont`;
    - `PS2 exit: sigterm <s>s|sigkill`.
  - Each line starts with a UTC timestamp, so A can time the pause / resume against the recovery log's
    `session_ended` / `session_started`. **Disclosed:** the prefix was added after the mutation runs; the suite was
    re-run ×3 (35 / 35) and the diff regenerated.
- **`plugins/games.py`:**
  - `SYSTEMS` + `ps2` ("PlayStation 2") per instance;
  - the scan's `ps2` branch;
  - `ps2_mode` in the start response and a `ps2_session` recovery row (`save_states: off`, the four behaviours);
  - `ps2_mode` on every heartbeat row.
- **`hold_rewind.py`, `rewind_cores.py`, `games/link_drop_recovery.py`:** the skips (§0.3).
- **`games/native_stream_heartbeat.py`:** `ps2_mode` is copied.
- **`players_session.py`:** `ps2` in the multitap systems, with no `--device` arguments.
- **`tools/ps2_p2_frames.py`** (new): H3's P2 metric.
  - **The input:** ffmpeg's `showinfo` of a capture with every frame, `format=yuv420p` first. Packed `bgr0` is
    refused: its padding byte made a black frame read mean 64 in a synthetic check.
  - **Excluded from the minimum:** black / static seconds (≥ 90 % of frames at Y ≤ 24, or ≤ 2 unique).
  - **The beat:** at most **one** isolated single repeat per second is forgiven.
  - **Beside it:** `--pcsx2-fps`.
  - **Bars:** median ≥ 59, corrected minimum ≥ 55.
  - **Disclosed, refined after the hash:** the design forgave every isolated repeat. A test then showed a real 30-fps
    drop (every frame doubled) read as 60, so the cap of one per second was added. A is told to capture an NTSC title
    at `-framerate 60000/1001`, so the beat barely arises.

## 2. Tests (`tests/ps2_session`, 35; fakes only; no real folder, BIOS or title in any test or fixture)

- **Setup:** the flag; the paths file; the AppImage pick.
- **The list:** dedupe, the `.bin` / `.cue` rules, hidden files, nothing written; the resolver's refusals.
- **The ini:** our keys, foreign keys kept, idempotent, the overlay off; the adapter rules.
- **The pads:**
  - 2 / 4 (multitap: Pad1 / 3 / 4 / 5 = SDL-0..3) / 1 player;
  - the DS2 layout;
  - the exact SDL line, and its GUID against the companion's pad constants;
  - `plan("ps2")`.
- **The BIOS and the command:** the BIOS copied once and not overwritten, the source unchanged; the command.
- **Pause / resume:**
  - the hotkey confirmed by PINE;
  - PINE unreachable → SIGSTOP / SIGCONT, with no hotkey sent;
  - an unconfirmed hotkey → SIGSTOP, and no second signal;
  - the exit by SIGTERM (SIGCONT first after a SIGSTOP), else SIGKILL;
  - PINE on a fake Unix socket (request bytes, answer, path).
- **The hooks** (fresh interpreters, the flag off / `0` / on): the import, `SYSTEMS`, the scan, the catalog; the
  drive's tree and `data/games/ps2/` untouched by a listing.
- **The launch** (a fake Popen, a fake xdotool and fake signals, a temp project):
  - absent → today's refusal, nothing written;
  - on → the command, `start_new_session`, the SDL env, the ini (multitap true, Pad5 = SDL-3, the adapter, the BIOS
    name), the hub BIOS copy;
  - the lifecycle: SIGSTOP → SIGCONT → SIGTERM, the save-state refusal, the kind cleared;
  - the log's four lines and no title / id / path; the drive's folders unchanged;
  - no pick → 2 ports; unconfigured folders → refused, no Popen.
- **The save states off:** the hold rewind's row, the slot-9 save not sent, the recovery save and slots refused, the
  give-up row (and the RetroArch row unchanged).
- **The rows:** `ps2_mode` on the start, the `ps2_session` row and the heartbeat; none for a RetroArch session or with
  the flag absent.
- **The P2 metric:** black seconds excluded, the beat corrected, a real drop kept, packed RGB refused.

**Mutations** (`tests_mutations.txt`):
- M1, the hold-rewind skip removed → 1 fail;
- M2, the plugin imports without the flag → 2 fail;
- M3, the hotkey sent with PINE unreachable → 2 fail, 1 error;
- M4, an incomplete `.cue` listed → 1 fail.

**Regression:** every `tests/` suite as the baseline copy (45 suites, plus `ps2_session`). Six `tools/` tests fail in
a copy, identically in the baseline copy. From the tree after the apply: the seven touched suites OK
(`tests_tree_after_apply.txt`). No JVM run: no client file changed.

## 3. Known limits (for A and the user)

- **Recalled, read back at H3-P2:**
  - PINE's opcode / status values (else every pause is a SIGSTOP, still correct);
  - PCSX2's SDL binding names and pad numbering;
  - SDL's open order of the four pads.
- **A SIGSTOP pause:** the picture stands and PCSX2's audio stream underruns while stopped. The stream's own pause
  covers both.
- **The hotkey path needs X focus** (`windowfocus`); on the hub's X display with no user it should hold, unverified.
- **Not built:** PS2 save states (the hold / stall / recovery saves) — a later item through PINE's save / load if the
  user wants them; the drive keep-awake (not needed on H3-P1's evidence).

## 4. Files

`b49_2026-11-08/`:
- `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`, `units_before_apply.txt`,
  `applied_to_tree_at.txt`;
- the design + `.sha256` + `design_hashed_at.txt`;
- `predecessors/` + `predecessor_sha256.txt`, `after_sha256.txt`;
- `b49.diff`;
- `proof_flag_absent.md`;
- `tests_ps2_session_x3.txt`, `tests_mutations.txt`, `tests_host_b49.txt`, `tests_host_baseline.txt`,
  `tests_tree_after_apply.txt`;
- `redact_check.txt`, `manifest.sha256`.

Patch note: `patches/B49_PS2_LAUNCH_KIND.md`.
