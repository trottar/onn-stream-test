---
memory_schema: 1
as_of: 2026-11-08
status: DESIGN (B60, session B queue V) — the GameCube feasibility probe H2-P1. NO code; nothing fetched or installed; no title, serial, path or folder name of the user's files written (the drive's folders by role only). The A run is sketched in §5; Dolphin is fetched only with the user's go. The streamed play waits for the launch kind (B61)
---

# H2-P1 — the GameCube feasibility probe (design)

**The user (2026-11-08):** "I'd rather do the PS2+ ones I have already in there (e.g. n64 and GameCube)". N64 goes
through RetroArch (B59). GameCube is this probe: the titles already on the external drive, listed in place like PS2.

**The question H2-P1 answers:** on this hub (Ryzen 5 PRO 4650G, 6 cores / 12 threads, the Vega 7 iGPU with RADV;
14 GB RAM; Debian 13; X11), does a GameCube title run at its own rate, with what CPU / GPU / thermal margin and what
shader-compilation stutter? Does the movies drive keep up? Later (B61), does it stream with the onn's pads with a hitch
rate near a PS1 session's? The answer is yes / no / where it breaks, not a product.

**Read for this design (on the hub, read-only):**
- `H3_P1_PS2_PROBE_DESIGN_2026-11-07.md`, `evidence/H3_P1_PS2_PROBE_2026-11-07.md` (its reading),
  `B49_PS2_LAUNCH_KIND_2026-11-08.md` and `B52_…` (the launch kind, the pause without a command port, the picture
  check), B59's design (the in-place listing generalised);
- `companion/native_stream.py`, `companion/native_session_io.py`, the RetroArch autoconfig of the virtual pads;
- the hub's packages, by `apt-cache` and `command -v` (no install, no fetch);
- the drive's GameCube folder, counted by extension and size only.

## 1. The emulator: standalone Dolphin

**Standalone Dolphin**, not the `dolphin-libretro` core:
- **the libretro core is unmaintained.** It trails upstream by years: no RVZ in old builds, missing fixes, old
  shader-compilation modes. A feasibility answer must measure the emulator, not a stale fork of it;
- **upstream Dolphin** is the maintained one: the Vulkan / OpenGL backends on RADV, the ubershader / async shader
  compilation that decides the stutter on an iGPU, RVZ, and the per-title fixes (`GameSettings`);
- as H3-P1 put it for PCSX2: if the emulator cannot hold the rate standalone, no core will.

**How the hub can run it, without root** (read on the hub: no `dolphin-emu`, no `flatpak`; Debian 13's
`dolphin-emu` candidate is **2503+dfsg-1+deb13u1**; of its 44 direct dependencies **10 are not installed**, and
`dolphin-emu-data` is one of the 10):

| way | root? | verdict |
| --- | --- | --- |
| **an upstream AppImage for the current stable** | no | **preferred if it exists**: one file in `runtime/emulators/dolphin/`, as PCSX2's. Upstream is recalled to publish Windows / macOS / Android builds only, with Linux through Flathub and the distributions; A checks the download page at the fetch |
| **Debian 13's packages, extracted in user space** | no | **the fallback (recommended):** `apt-get download` of `dolphin-emu`, `dolphin-emu-data` and the 9 missing libraries (Debian-signed; each `.deb`'s sha256 against the repository's index), `dpkg -x` each into `runtime/emulators/dolphin/root/`, launched with `LD_LIBRARY_PATH` set to that tree's library folders. Nothing system-wide; `ldd` must show no "not found" (P0a) |
| Debian's package, system-installed (`sudo apt install dolphin-emu`) | **yes** | **the user's own option** (A has no sudo): the simplest and most robust; pulls the same 11 packages (with any further dependencies apt resolves) |
| the Flatpak (`org.DolphinEmu.dolphin-emu`) | **yes, once**: `flatpak` itself is not installed, and installing it is a system `apt` install (then `--user` installs need no root) | **not chosen:** besides the root step, the sandbox puts a `bwrap` process between the companion and the emulator. That reopens the PID question for the capture and the audio (§2), and the uinput pads need `--device=all` |

**The version is Dolphin's, not Debian's alone:** 2503 is the 2025-03 upstream release (Dolphin numbers releases by
year and month). If the user prefers a newer stable, that is the AppImage row, or a later Debian update.

## 2. The parts, as H3-P1's table

| part | today (RetroArch / PCSX2, read) | Dolphin standalone | gap (B61) |
| --- | --- | --- | --- |
| **launch** | RetroArch: the command, the session cfg, `--device`, a command port, the paused handoff. PCSX2 (B49): `-datapath … -nogui -fullscreen -- <title>`, the ini merged per launch | `dolphin-emu-nogui -p x11 -u <user dir> -e <title>` (a single X11 render window, no Qt main window), else `dolphin-emu -b -u <user dir> -e <title>` (`-b` exits with the emulation). **As recalled; confirmed from `--help` at the run** (P0a). The user dir is `data/games/gamecube/user/`, so nothing lands in `~/.local/share` | **code (B61):** a `dolphin` launch kind beside `pcsx2`; the ini files written per launch |
| **capture** | `xdotool search --onlyvisible --pid <pid>` → x11grab of that window | the same. The **PID**: an AppImage runtime or a `bwrap` would sit between (the extract has none). The Qt build's render window may be a second top-level (or a child) of the main window → `nogui` first; else `[Display] RenderToMain = True` and the largest visible window of the PID | P0b reads it; B61 takes the PID's children if it misses (PCSX2's rule) |
| **audio** | one sink-input by `application.process.id`, moved to the session's null sink | Dolphin's Cubeb (or Pulse) backend → one stream by PID (`[DSP] Backend` written per launch) | P0c: exactly one sink-input of the started PID |
| **input** | the four uinput pads (1209:5048, "PrivyHub Virtual Gamepad P1-P4"); RetroArch reads them by udev, PCSX2 by SDL (one mapping line) | **Dolphin's evdev backend** reads the same four pads, with no bridge. `Config/GCPadNew.ini` is **written per launch**: `[GCPad1-4] Device = evdev/<n>/PrivyHub Virtual Gamepad P<n>`, `SIDevice0-3 = 6` (a standard controller, in `Dolphin.ini [Core]`). The evdev device and input names are **recalled** (`evdev/0/…`; buttons as `SOUTH`, `EAST`, `NORTH`, `WEST`, `TL`, `TR`, `START`; axes as `Axis 0+` / `Axis 0-`); A reads them back from Dolphin's log at the streamed run (P0d) | B61 writes the file, the device names from the log |
| **the layout** | — | **GameCube, positional:** **A** ← south (onn A / Cross), **B** ← west (X / Square), **X** ← east (B / Circle), **Y** ← north (Y / Triangle); the **main stick** ← the left stick; the **C-stick** ← the right stick; **L / R** ← the left / right triggers, analog (axes +2 / +5), the digital click at full travel; **Z** ← the right bumper; **Start** ← Start; the **D-pad** ← the hat. The left bumper is unbound | the user's line at P7 |
| **pause / resume / exit** | RetroArch's `PAUSE_TOGGLE` + `GET_STATUS`; PCSX2's hotkey confirmed by PINE, else SIGSTOP / SIGCONT | **No IPC socket.** Pause: the *Toggle Pause* hotkey (`F10`, written into `Hotkeys.ini` per launch) injected with `xdotool windowfocus --sync <wid>` + `key F10`. **Confirmed by a standing counter:** the emulation thread's CPU time (`/proc/<pid>/task/<tid>/stat`, the thread Dolphin names for the CPU / JIT core) stands still over 0.5 s; resumed, it grows ~0.5 s per 0.5 s. The picture standing in two grabs is a second check. Unconfirmed in 1.5 s → **SIGSTOP / SIGCONT** (the method kept, so a SIGSTOP is always undone by SIGCONT). **Exit:** SIGTERM (Dolphin stops the emulation and exits; `-b` / nogui), then SIGKILL after 5 s | B61: PCSX2's pattern, PINE replaced by the thread counter |
| **save states** | RetroArch's slots (PrivyHub's SAVE / LOAD 1-3; the hold's slot 9; the recovery's slot 8); PCSX2's through PINE (B51-B57) | Dolphin's **Save / Load State Slot n** hotkeys (`Shift+F<n>` / `F<n>`, written per launch). PrivyHub's slots 1-3 → Dolphin 1-3; the hold / stall scratch → 9; the give-up save → 8. **Read back by the state file's mtime:** `<user dir>/StateSaves/<game id>.s0<n>` (`.s10` for 10) newer than the press and its size stable for 0.5 s, within 10 s. **After a load: B52's picture check** (≥ 3 distinct grabs, not black, within 5 s). **`confirmed`** means both (the file for a save; the picture for a load); otherwise the row says which part failed and the session goes on | B61; A measures the write time at P0f |
| **ports / players** | PS1 / PS2 multitap at launch (B46); N64 four always (B59) | **four native ports, no multitap.** All four set at launch, as N64's, so hold-to-join fills P1-P4 with **no relaunch** ("Setting up 4 players…" never on GameCube) | B61: `ports_set` 4 / `multitap_available` false |
| **per-title metadata** | `player_mode`, `max_players`, B41's default 2 | the same keys; Dolphin's own `GameSettings` per game id apply by themselves (the fixes database) | none |

## 3. The files

- **Titles in place on the drive** (the GameCube folder, the sibling of the PS2 one): **27 `.rvz` (150 MB to 1.1 GB,
  median ~620 MB)** and **one small `.bin` in a subfolder whose name reads as a BIOS / region folder. It is not a
  title, and is not listed or read.**
  - **The listing:** B59's `inplace_library`, with a `GAMECUBE_DIR=` key in the same gitignored paths file;
  - **the extensions:** `.rvz` > `.gcm` > `.iso` > `.ciso`, one entry per stem, `.rvz` preferred;
  - **read-only; nothing ever written to the drive** (the folder is not writable by the hub's user anyway).
  - **Not decided here, for B61:**
    - whether the list reads each file's 128-byte disc header (RVZ keeps it uncompressed) to leave out Wii discs (the
      GameCube magic `0xC2339F3D` at 0x1C; Wii's `0x5D1C9EA3` at 0x18);
    - a two-disc title as one entry through an `.m3u` made on the hub (Dolphin reads one), as B56 does for PS1.
- **On the hub, under the gitignored `data/games/gamecube/`:**
  - `user/Config/` (`Dolphin.ini`, `GFX.ini`, `GCPadNew.ini`, `Hotkeys.ini`, merged per launch, other keys kept);
  - `user/GC/` (memory cards, Dolphin's GCI-folder mode, per region);
  - `user/StateSaves/`; `user/Cache/` (the shader cache, which makes the second run of a title smoother than the first:
    P4 reads both); `user/Logs/`;
  - `runtime/emulators/dolphin/` for the program (gitignored).
  - The state files carry the disc's game id in their names: on the hub only, never in a record.
- **No BIOS needed:** Dolphin boots a GameCube title by HLE (`[Core] SkipIPL = True`). A real IPL is optional; Dolphin
  reads it from `user/GC/<region>/IPL.bin` only if the user puts their own there. **Nothing is fetched for it.**
- **The config written per launch** (recalled keys, read back at P0a from the files Dolphin writes after its first
  start):
  - `[Core] CPUThread = True` (dual core), `SkipIPL = True`, `SIDevice0-3 = 6`;
  - `[Interface] ConfirmStop = False`, `UsePanicHandlers = False` (no dialog can block an unattended run);
  - `[Analytics] PermissionAsked = True`, `Enabled = False`; `[AutoUpdate] UpdateTrack =` (empty);
  - `[DSP] Backend` (Cubeb);
  - `GFX.ini [Settings] InternalResolution = 1` (native, 640×528), `ShaderCompilationMode = 2` (asynchronous with
    ubershaders), `WaitForShadersBeforeStarting = True`;
  - the backend **Vulkan on RADV** first, OpenGL recorded as the fallback.
- **The drive's spin-down, as before:** H3-P1 read no spin-down in 12 idle minutes (a direct read after 12 min took
  0.32 s), and the one slow second was a load. Keep-awake is not built; P5 reads it again, because an `.rvz` decompresses
  in blocks and a large title reads more scattered than a PS2 `.chd`.

## 4. The metrics and the pass rows (pre-registered for A; hashed by A before its run)

**The metrics** (H3-P1's tools: `mpstat`, `pidstat`, `iostat`, `ffmpeg`, `xdotool`, `sensors`, sysfs; and B59's
`tools/n64_frames.py`, whose rates 20 / 30 / 60 serve GameCube titles too):

| # | metric | how (A) | unit |
| --- | --- | --- | --- |
| M1 | fps vs 60 / the title's internal rate | a 60-s x11grab capture of the window with `format=yuv420p,showinfo` → `tools/n64_frames.py` (distinct frames per second, static / black excluded, the internal rate snapped to 30 / 60) | median and minimum distinct fps; the internal rate |
| M2 | CPU per core and the JIT thread | `mpstat -P ALL 1`; `pidstat -t -p <pid> 1` (the CPU / JIT thread, the GPU thread, the others by name) | per-core %, per-thread % |
| M3 | GPU busy | `/sys/class/drm/card0/device/gpu_busy_percent` at 1 Hz | % |
| M4 | frame-time p95 and the shader stutter | the distinct-frame intervals of M1; the count of gaps > 100 ms in the first 5 min of a title's first run vs the same span of its second run (the shader cache) | ms p50 / p95 / p99; count |
| M5 | disc-read stalls | `iostat -x 1` on the drive's block device; a stall = a second with a read wait > 500 ms; M4's gaps > 100 ms beside it | count, longest, coincident gaps |
| M6 | thermals | `sensors` k10temp Tctl at 1 Hz | °C max / median |
| M7 | streamed (B61) | 1080p60 through the companion, the onn's pads, 10 min | UX-R3's hitch seconds per 10 min beside a PS1 session's; `n64_frames`' internal hitch rate |

**The pass rows:**

| row | stage | pass when |
| --- | --- | --- |
| P0a | setup | Dolphin starts from `runtime/emulators/dolphin/` with the user dir under `data/games/gamecube/` (`ldd`: nothing "not found"); `--help` read and the launch flags confirmed; the version recorded; nothing written to the drive (the folder's file list and mtimes before = after) |
| P0b | setup | `xdotool search --onlyvisible --pid <started pid>` returns the render window (else: B61's PID item, not a fail of the probe) |
| P0c | setup | exactly one sink-input whose `application.process.id` is the started PID (else: B61's audio item) |
| P0e | unattended | the pause hotkey injected by `xdotool` stops the CPU thread's time within 1.5 s and the resume restarts it (else: SIGSTOP / SIGCONT recorded as the method) |
| P0f | unattended | a save by hotkey writes the slot's state file (mtime newer, size stable) within 10 s, its write time recorded; a load by hotkey passes B52's picture check within 5 s |
| P1 | unattended | T1 boots to its title / menu within 90 s of the launch; no crash and no dialog over 5 min idle at the menu |
| P2 | unattended | M1 median ≥ the internal rate − 1 and minimum ≥ the internal rate − 5, at the menu and through one attract / FMV loop, Vulkan, 1x |
| P3 | unattended | M2: no single core ≥ 90 % for 30 s running (the CPU / JIT thread named if it is the one); M3 median ≤ 80 %; M6 Tctl ≤ 90 °C |
| P4 | unattended | M4 p95 ≤ 20 ms and p99 ≤ 34 ms at a 60-fps rate (×2 at 30); the first-run vs second-run gap counts recorded (informative) |
| P5 | unattended | M5: no read stall > 500 ms after the first 60 s; a read after a 10-min idle at the menu recorded with its time (informative: decides a keep-awake) |
| P0d | streamed (B61) | the four virtual pads in Dolphin's log as evdev devices P1-P4 in creation order; each GameCube input pressed once on the onn does what §2's layout says (the user's line) |
| P7 | streamed (B61) | M7: hitch seconds per 10 min ≤ the PS1 session's + 2; the internal hitch rate recorded; the user's line on feel |

**The titles:** T1 (light) and T2 (heavy):
- by the user's word, by their position in the onn's GameCube list (A never names one);
- else A takes the smallest and the largest `.rvz` by file size. Size only loosely tracks load, and the rows record
  which rule picked them.

A title failing P2 at 1x is recorded as its tier (H4's "selected GameCube"), not retried with hacks in H2-P1.

## 5. The A run, sketched (H2-P1)

**Preconditions (A):** the adopted lines and `--check` as at that sitting; only the companion and `privyhub-diag`
active; **no game and no movie running** (the probe uses the CPU, the GPU and the movies drive); `/tmp` ≥ 1 GB free;
no companion restart (nothing of the companion is used until B61).

1. **YOU, now:** say whether A may fetch Dolphin.
   - The way: the upstream AppImage for the current stable if upstream publishes one; else Debian 13's 2503 packages
     extracted into `runtime/emulators/dolphin/` (11 packages at least — `dolphin-emu` and the 10 missing; their own dependencies read at the fetch — no system change);
   - or install it yourself with `sudo apt install dolphin-emu`.
   - **Nothing is fetched without this go.** A records the version and each file's sha256 (the emulator's, never
     content), runs nothing as root and installs nothing system-wide.
2. **A, unattended:**
   - the fetch;
   - `ldd` and `--help`;
   - the `GAMECUBE_DIR=` line in the gitignored paths file;
   - the user dir with §3's config;
   - **the pass rows hashed**.
3. **A, unattended, T1 then T2** (from a shell on the hub's display; the pads not needed; no title named anywhere):
   - P0a-P0c;
   - P1 (the boot to the menu);
   - P0e (pause / resume at the menu);
   - P0f (a save and a load at the menu);
   - P2-P5, with the 10-min idle for P5;
   - each title run twice for M4's cache comparison;
   - Dolphin exited; the rows recorded with T1 / T2 only.
4. **The streamed play, once the launch kind exists (B61):**
   - at the TV, **the user's pads on the onn over Bluetooth, never on the hub**, every reply starting "YOU, now:";
   - P0d (the layout, the user's line), then 10 min of T1 with two pads (P7), then T2 as far as the user likes;
   - the hitch rate beside a PS1 session's of the same evening.
5. **Close (A):**
   - nothing left running; the drive as the user left it; `data/games/gamecube/` and `runtime/emulators/dolphin/`
     stay (gitignored);
   - the record `evidence/H2_P1_GAMECUBE_PROBE_<date>.md` with T1 / T2 only, `redact_check` over it.

**What comes back to the user:** per title, pass / fail on P1-P5 with the margins (the internal rate held, the busiest
core / the JIT thread, GPU, Tctl, the shader stutter first vs second run, the drive's stalls), and B61's scope (the
launch kind; the PID / audio items if P0b / P0c missed; the pause method P0e chose; the save-state write time).
