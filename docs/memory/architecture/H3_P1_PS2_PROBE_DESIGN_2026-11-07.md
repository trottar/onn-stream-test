---
memory_schema: 1
as_of: 2026-11-07
status: DESIGN (B48, session B queue O) — the PS2 feasibility probe H3-P1. NO code; nothing fetched or installed; no BIOS or game touched or named. Paths for the user's files are placeholders. The A run is sketched in §5; PCSX2 is fetched only with the user's go
---

# H3-P1 — the PS2 feasibility probe (design)

**The user (2026-11-06 / 07):** "I would like to do the PS2 setup first before user control import. It makes more
sense to even see if these things work first"; "I will put the PS2 bios and games onto the external hard drive that
the movies are on … We can copy a few games over until we have a better solution". N64 stays RetroArch (not this
probe). Read for this design (all on the hub, read-only): `companion/games/emulator_manager.py` (the launch),
`companion/native_stream.py` (the capture), `companion/native_session_io.py` (the audio sink and the controllers),
`companion/storage_presence.py` and `architecture/TV_MEDIA.md` (the movies drive), `ROADMAP.md` §H0 / §H3,
`architecture/H0_IMPORT_CONTRACT_DESIGN_2026-11-06.md`, B46's settled ports. The hub: Ryzen 5 PRO 4650G (6 cores /
12 threads, Vega 7 iGPU, RADV present), 14 GB RAM, Debian 13, X11 (`xdotool` capture).

**The question H3-P1 answers:** on this hub, does a PS2 title run at its native rate in the emulator, with what CPU /
GPU / thermal margin, does the movies drive keep up, and (later, B49) does it stream with two pads with a hitch rate
near a PS1 session's? A yes / no / where-it-breaks, not a product.

## 1. The emulator, and what today's path does that it would not

**The probe uses standalone PCSX2** (the upstream Qt build, the Linux x86-64 AppImage), not a libretro core:
- the upstream emulator is the maintained one, with the hardware renderers (Vulkan via RADV, OpenGL), the per-title
  fixes database and the compatibility the probe is meant to measure. The libretro PS2 core lagged upstream for years
  (the old `pcsx2_libretro` was abandoned; whether a newer libretro fork is current is **not checked here — nothing was
  fetched**; A may check before asking the user, and the answer does not change the probe: it measures the emulator);
- a feasibility answer should not depend on a frontend's wrapper. If PCSX2 cannot hold the native rate standalone, no
  core will; if it can, the core question can be asked later against a known-good number.

**Today's RetroArch path, part by part, and what PCSX2 needs instead:**

| part | today (read from the code) | PCSX2 standalone | gap |
| --- | --- | --- | --- |
| **launch wrapper** | `EmulatorManager.launch`: the RetroArch command, a session cfg, the input cfg (`privyhub-input.cfg`), the per-content `.opt` (B46), `--device` args, a per-launch network-command port, the paused handoff (`PAUSE_TOGGLE` right after launch), the game log | none: a PCSX2 command line (`pcsx2-qt -batch -nogui -fullscreen -- <game>` as recalled; confirmed from `--help` at the run) and an ini written per session | **code (B49):** an emulator kind beside RetroArch in the launch |
| **capture** | `native_stream`: `xdotool search --onlyvisible --pid <managed pid>` → the window id → `ffmpeg -f x11grab -window_id` | the same, **emulator-agnostic** (X11, any window) | the **PID**: an AppImage's window may belong to a child of the PID the companion started. The probe reads `xdotool search --pid` against the started PID (§4 row P0b); if it misses, B49 runs the extracted binary or searches the PID's children |
| **audio** | `native_session_io`: a **dedicated per-session PulseAudio null sink**; the managed PID's sink-input is moved into it (`move-sink-input`, matched by `application.process.id`; more or fewer than exactly one is refused) | PCSX2 plays through cubeb → PulseAudio (pipewire-pulse); one stream expected | **per-app, by PID**: the same PID caveat as the capture; exactly one sink-input to be read at the run (P0c) |
| **input** | the companion owns **four uinput pads** ("PrivyHub Virtual Gamepad P1-P4", vendor 0x1209 / product 0x5048), created before the launch (`ensure_game_controller`); **RetroArch reads them itself** through its `udev` joypad driver; the onn's pad packets drive them | PCSX2's SDL input source reads evdev devices too: **the same four uinput pads, no transport bridge** | **config, not a bridge:** SDL must map 1209:5048 as a game controller (SDL may map an evdev pad with standard buttons by itself; if not, one mapping line in PCSX2's controller database or `SDL_GAMECONTROLLERCONFIG`), and Pad1-Pad4 bound to the four in creation order. **None of today's devices needs a bridge** |
| **pause / resume / exit from the onn** | RetroArch's network commands on loopback: `PAUSE_TOGGLE` + `GET_STATUS` (the stream's stabilization pause, Back on the onn, Resume), save / load state (the hold, the rewind, the stall resume), `QUIT` | **no UDP command interface.** PINE (PCSX2's IPC socket, when enabled) gives the status (running / paused), save / load state and the title's serial, but (as recalled) no pause command | **a design for B49:** pause / resume by PCSX2's own pause hotkey, injected into its window (`xdotool`, focus then key), read back through PINE's status; fallback SIGSTOP / SIGCONT (emulator-agnostic; the picture freezes, which a pause allows). Exit: the shutdown hotkey or SIGTERM with `-batch`. The hold / rewind / stall-resume (RetroArch save states) **off for PS2** until PINE's save / load is shown working |
| **per-title metadata / players** | `player_mode`, `max_players`, the PS1 multitap override, B46's `players_chosen` → the `.opt` / `--device` at launch | PCSX2's multitap: `[Pad] MultitapPort1` / `MultitapPort2` (true / false) in its ini, read at start | **the same rule as B46:** set per session at launch from `players_chosen` (multitap → port-1 tap on; 1 / 2 → off), never mid-session; the four pads' order on the tap's sub-ports is read from PCSX2's own controller settings at the run (B49's map) |

## 2. The files

- **BIOS and games on the external drive the movies are on, placeholder paths only:**
  `<MOVIES_DRIVE>/PrivyHub/ps2/bios/` and `<MOVIES_DRIVE>/PrivyHub/ps2/games/`. **The user names the real folders at the
  run;** A writes them into the session's ini only, never into git or a record. "Copy a few games over" = one or two
  titles to start.
- **Memory cards, saves and PCSX2's config on the hub disk**, inside the companion's gitignored data tree:
  `data/games/ps2/memcards/`, `data/games/ps2/sstates/`, `data/games/ps2/config/` (PCSX2 pointed there by its ini's
  `[Folders]` and a portable / settings-dir option, read from `--help` at the run, so nothing lands in `~/.config`);
  `runtime/emulators/pcsx2/` for the AppImage (gitignored). Nothing on the drive is written by PCSX2 (the game files
  are read-only for it; the BIOS folder only read).
- **The drive's spin-down is a hitch risk.** A USB disk that stands by after idle needs seconds to spin up; a PS2 title
  reads the disc in bursts (a load, a streamed area, an FMV), so an idle spell then a read is a stall in play. The
  movies drive is a systemd automount (`storage_presence`, `TV_MEDIA.md`); an idle unmount, if configured, is a second
  risk. **Designed, not built (B49 if the probe shows stalls):** a per-session keep-awake in the companion — a small
  uncached read (4 KiB at a random offset of the running title's file, `O_DIRECT`) every 30-60 s, below the drive's
  standby timer, from launch to stop; it also keeps an automount from idling out. The alternative, read-ahead (pull the
  whole image into the page cache at launch), costs up to ~4.7 GB of a 14-GB hub and is kept as option 2. No root, no
  `hdparm`.
- **ROADMAP §H3's "User-supplied PS2 BIOS should enter only through the G0 import boundary" is DEFERRED by the user's
  decision** (2026-11-07: feasibility first). For H3-P1 the BIOS stays where the user puts it on the drive and is read
  in place; H0's import (B45's `PrivyHub-Import/` layout, the `ps2/` folders it reserves) later moves the files, and the
  boundary then applies. The deferral is written into ROADMAP §H3 as such.
- **The privacy rule, unchanged:** no BIOS or game file, name, title, serial, hash or path in git or any record; a
  title is `T1` / `T2`; the BIOS is "present" or "absent" (its region may be written as a class: NTSC-U / PAL / NTSC-J,
  no version or hash). Logs PCSX2 writes stay under `data/games/ps2/` (gitignored); A copies only counts out of them.

## 3. The metrics

Each read with tools present on the hub (`mpstat`, `pidstat`, `iostat`, `ffmpeg`, `xdotool`, `sensors`, sysfs), no new
code; one run per title per row unless written.

| # | metric | how (A) | unit |
| --- | --- | --- | --- |
| M1 | fps vs the title's native rate | a 60-s `x11grab` recording of the window at its native size → unique frames (`mpdecimate`) per second; PCSX2's own on-screen performance figures beside it as a cross-check | median and minimum fps over 60 s, against 60 (NTSC) / 50 (PAL) |
| M2 | CPU per core | `mpstat -P ALL 1` and `pidstat -t -p <pid> 1` (PCSX2's threads: the EE / VU / GS threads by name) | per-core busy %, per-thread % |
| M3 | GPU busy | `/sys/class/drm/card0/device/gpu_busy_percent` at 1 Hz | % |
| M4 | frame-time p95 | the unique-frame intervals of M1's recording | ms, p50 / p95 / p99 |
| M5 | disc-read stalls | `iostat -x 1` on the drive's block device (r_await, %util) + `/sys/block/<dev>/stat` read-time; a stall = a second with a read wait > 500 ms; M4's frame gaps > 100 ms laid beside it | count, longest, coincident frame gaps |
| M6 | thermals | `sensors` k10temp Tctl at 1 Hz | °C max / median |
| M7 | streamed (B49) | 1080p60 through the companion's stream, two pads, 10 min | UX-R3's hitch seconds per 10 min, beside a PS1 session of the same length on the same evening |

**Pass rows, pre-registered for A** (to be hashed by A before its run; unchanged by A once hashed):

| row | stage | pass when |
| --- | --- | --- |
| P0a | setup | the BIOS found by PCSX2 (its BIOS list non-empty) from `<MOVIES_DRIVE>/PrivyHub/ps2/bios/`; nothing written to the drive (the folder's file list and mtimes before = after) |
| P0b | setup | `xdotool search --onlyvisible --pid <started pid>` returns PCSX2's window (else: recorded as the B49 PID item, not a fail of the probe) |
| P0c | setup | exactly one PulseAudio sink-input whose `application.process.id` is the started PID (else: the B49 audio item) |
| P1 | unattended | T1 boots to its title / menu within 90 s of the launch; no crash or emulator error dialog over 5 min idle at the menu |
| P2 | unattended | M1 median ≥ native − 1 fps (59 / 49) and minimum ≥ native − 5 at the menu and through one attract / FMV loop, renderer hardware, internal resolution native (1x) |
| P3 | unattended | M2: no single core ≥ 90 % for 30 s running; M3 median ≤ 80 %; M6 Tctl ≤ 90 °C |
| P4 | unattended | M4 p95 ≤ 20 ms and p99 ≤ 34 ms (60 Hz; ×1.2 for 50 Hz) |
| P5 | unattended | M5: no read stall > 500 ms after the first 60 s; a spin-up after a 10-min idle at the menu recorded with its duration (informative: decides the keep-awake) |
| P6 | attended | the user plays T1 for 10 min with two pads; M1-M6 as P2-P5 in play; the user's line on feel (smooth / stutters / unplayable) |
| P7 | streamed (B49) | M7: hitch seconds per 10 min ≤ the PS1 session's + 2, the user's line on input feel |

T2 (if the user copies a second, heavier title) repeats P1-P6; a title failing P2 at 1x is recorded as its tier
(H4's "selected PS2"), not retried with hacks in H3-P1.

## 4. Risks the probe reads first (P0)

The PID behind the window and the audio stream (an AppImage runtime between the companion and the emulator); SDL's
mapping of the virtual pads (only for B49: the attended step uses pads plugged into the hub); RADV / Vulkan on the
4650G's iGPU (OpenGL as the fallback renderer, recorded); the drive's spin-up.

## 5. The A run, sketched (H3-P1)

**Preconditions (A):** fifteen adopted lines, `--check` ok, the CONFIRMED APK on the onn; only the companion and
`privyhub-diag` active; **no game and no movie running** (the probe uses the hub's CPU and the movies drive); no
companion restart needed (nothing of the companion is used until B49).

1. **YOU, now:** put the PS2 BIOS file(s) into a folder on the movies drive, and one (or two) PS2 games into another
   (the design's names are `<MOVIES_DRIVE>/PrivyHub/ps2/bios/` and `<MOVIES_DRIVE>/PrivyHub/ps2/games/`; any folders
   work). Then tell A the two folder paths (A writes them only into the session's ini, never into a record).
2. **YOU, now:** say whether A may fetch PCSX2 (the official Linux AppImage, the current stable release) into
   `runtime/emulators/pcsx2/`, **or** download it yourself and put it there. **Nothing is fetched without this go.** A
   records the release's version and the file's sha256 (the emulator's, not the content's), runs nothing as root,
   installs nothing system-wide.
3. **A, unattended (no user needed):** writes PCSX2's ini under `data/games/ps2/config/` (the BIOS / games folders from
   step 1, the memory cards / save states under `data/games/ps2/`, the hardware renderer at 1x, multitap off); hashes
   the pass rows; starts PCSX2 from a shell on the hub's display with T1; reads P0a-P0c; leaves T1 at its menu and runs
   P1-P5 (the 10-min idle for P5's spin-up); exits PCSX2; records the rows (T1, no title).
4. **YOU, now (attended, ~15 min):** two pads plugged into the hub (USB or paired to the hub, not the onn), the hub's own
   screen. A starts T1; you play 10 minutes. A reads P6; you send one line on how it felt.
5. **The stream (P7):** **not in H3-P1** — the companion's launch is RetroArch-only (§1's first row is code), so the
   stream over PCSX2 is **B49** (the launch kind, the PID / audio items if P0b / P0c missed, the SDL mapping, the pause
   design, the keep-awake if P5 showed stalls). P7 runs at the A run after B49.
6. **Close (A):** PCSX2 exited; nothing left running; the drive's folders as the user left them; `data/games/ps2/` and
   `runtime/emulators/pcsx2/` stay (gitignored); the record `evidence/H3_P1_PS2_PROBE_<date>.md` with T1 / T2 only;
   `redact_check` over it (no address, no title, no path from step 1).

**What comes back to the user:** per title, pass / fail on P1-P6 and the margins (fps, the busiest core, GPU, Tctl, the
drive's stalls), and B49's scope for the stream.
