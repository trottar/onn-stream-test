---
memory_schema: 1
as_of: 2026-11-09
status: H2-P1 DONE (session A, unattended, 2026-11-09 01:07-01:57Z; no TV, no pads). Dolphin 2609b, the upstream Linux x64 AppImage from the official download page (the user's "Yes to dolphin"), Vulkan on RADV at 1x. Both titles at full speed with wide margins; every row met on every run except P2's minimum on T2 run 1 (50 vs 55: single repeated frames on the capture side, Dolphin's own frame times clean). P0d / P7 not this run (streamed, after B69). Nothing written to the drive; nothing adopted; nothing installed system-wide; nothing committed
---

# H2-P1: the GameCube probe (Dolphin standalone on the hub)

Task: `handoffs/H2-P1_GAMECUBE_PROBE_RUN_TASK.md`. The spec: `architecture/H2_P1_GAMECUBE_PROBE_DESIGN_2026-11-08.md`.
§4's rows are pre-registered verbatim in `h2_p1_2026-11-09/preregistration.md` (sha256 `a2c16376…8f21`, hashed
01:09:46Z, before the fetch). P0d and P7 are marked "not this run".

Directory `h2_p1_2026-11-09/`:
- `stage1/` (preconditions, the fetch, `--help`, the AppImage's per-file hashes, `check_before.json`);
- `t1_r1/`, `t1_r2/`, `t2_r1/`, `t2_r2/` (numbers-only CSVs and `summary.json` per run);
- `t1_segments.json`, `check_end.json`, `scripts/`, `redact_check.txt`, `manifest.sha256`.

The titles are **T1** (the smallest `.rvz`, 158 MB) and **T2** (the largest, 1,177 MB), picked by file size (the
design's "else" rule). Both are NTSC-U: native 60 (59.94 Hz). Times UTC. The raw files (screenshots, logs, showinfo)
stay under the gitignored `data/games/gamecube/probe/`.

## Setup

- **Preconditions met** (`stage1/preconditions.txt`):
  - HEAD `7d0056b4` (queue X committed), the tree clean;
  - seventeen drop-ins, `--check` ok, `9aa00ba2…` CONFIRMED, the eleven properties empty;
  - only `privyhub-companion` and `privyhub-diag` running; no game, no movie;
  - `/tmp` 6.3 GB free, home 137 GB free;
  - the drive mounted read-only (`sda`, USB, rotational).
- **The GameCube folder** (`GAMECUBE_DIR=` added to the gitignored paths file, the only change there): 27 `.rvz`
  (17.99 GB; median 647 MB) and the one small `.bin`, which was not read. Not writable by the hub's user. Listing
  sha256 `a51c1f21…1146`.
- **The fetch** (`stage1/fetch.txt`): **way (a), OFFERED.**
  - The official page (behind a JavaScript shield; rendered in the hub's Firefox) lists **2609b** ("Second hotfix for
    2609") with **"Linux x64 (AppImage)"**. Earlier releases list Flatpak only.
  - Fetched from the project's download host at the release path: `dolphin-2609b-x64.AppImage`, 100,022,776 B, sha256
    `05521082…6c4d`. No published digest; the page's href was not machine-read (the shield, not bypassed).
  - `--version` "Dolphin 2609b". Every file inside is hashed: 3,005 files, `dolphin-emu` `916d4c99…87df`.
  - `AppRun` is a symlink to `usr/bin/dolphin-emu`: no wrapper and no `bwrap`.
  - `ldd`: 164 libraries, **0 "not found"**.
  - Way (b) was not needed; no Flatpak; nothing as root or system-wide.
- **The flags** (`stage1/help.txt`):
  - `-u`, `-e` and `-b` are confirmed.
  - **The config flag is corrected:** `-C <System>.<Section>.<Key>=<Value>`.
  - **No `dolphin-emu-nogui` in the AppImage**, so the design's second form ran: `-b -u <user dir> -e <title>`.
- **The user dir** `data/games/gamecube/user/` (gitignored). §3's keys were written before the first start and read back
  after the runs, unchanged:
  - `Dolphin.ini`: `CPUThread`, `SkipIPL`, `GFXBackend = Vulkan`, `SIDevice0-3 = 6`, `SlotA = 8` (the GCI folder),
    `RenderToMain = True`, `Fullscreen = True`, `ConfirmStop` / `UsePanicHandlers` off, the analytics asked and off,
    `UpdateTrack` empty, the DSP `Cubeb`;
  - `GFX.ini`: `Adapter = 0` (RADV RENOIR; `vulkaninfo`'s GPU1 is llvmpipe), `InternalResolution = 1`,
    `ShaderCompilationMode = 2`, `WaitForShadersBeforeStarting`, `ShowFPS`, `LogRenderTimeToFile` (Dolphin's own
    `render_times` / `vblank_times`, the counter beside the capture);
  - **the pads:** the four virtual pads did not exist, so Dolphin's keyboard default was used (no pad was used);
  - the hotkeys are Dolphin's defaults: F10 pause, Shift+F1 / F1 save / load slot 1.
  - Nothing was written outside the user dir (no `~/.local/share`, `~/.config` or `~/.cache` entry) and nothing to the
    drive.
- **The renderer:** Vulkan, adapter 0 (RADV), every run. The process had no `llvmpipe` thread in any run, and the GPU
  was busy 10-19 %. **Valid.** Audio: "Cubeb initialized using pulse backend".

## The rows per title and run

Run 2 repeats run 1 with the shader cache and the page cache warm.

| row | T1 run 1 | T1 run 2 | T2 run 1 | T2 run 2 |
| --- | --- | --- | --- | --- |
| **P0a** start from `runtime/`, user dir on the hub; flags; nothing on the drive | met | met | met | met |
| **P0b** the window by the started PID | **met** (4.0 s; the PID's one visible window, fullscreen 1920×1080) | met (4.0 s) | met (4.0 s) | met (4.0 s) |
| **P0c** one sink-input of the started PID | **met** (1, by 12.6 s) | met (1) | met (1) | met (1) |
| **P0e** pause / resume by hotkey | **met, hotkey** | met, hotkey | met, hotkey | met, hotkey |
| **P0f** save (file ≤ 10 s) / load (picture ≤ 5 s) | **met**: 0.21 s, 30.6 MiB / 3 distinct by 0.2 s | met: 0.21 s, 30.4 MiB / 0.2 s | met: 0.21 s, 18.2 MiB / 0.2 s | met: 0.21 s, 18.3 MiB / 0.2 s |
| **P1** menu ≤ 90 s; idle clean | **met**: the title by ~15 s; 5 min, 1 window, no dialog | met: ~9 s; 5 min | met: first screen ~18 s (below); 3 min, 1 window | met: 3 min |
| **P2** median ≥ rate − 1, min ≥ rate − 5 | **met** (60-fps title: median 60 / min 56; 30-fps demo: 30 / 28) | met (60 / 56; 30 / 29) | median 60 met; **min 50 NOT MET** (by 5) | met (60 / 59) |
| **P3** no core ≥ 90 % 30 s; GPU ≤ 80 %; Tctl ≤ 90 °C | **met**: longest 4 s (boot pre-compile); GPU 10 %; 52.9 °C | met: core max 53 %; GPU 10 %; 54.5 °C | met: longest 1 s; GPU 17 %; 60.9 °C | met: core max 65 %; GPU 19 %; 61.5 °C |
| **P4** p95 ≤ 20, p99 ≤ 34 ms (×2 at 30) | **met** (60: 16.84 / 17.03; 30: 33.56 / 33.72) | met (16.85 / 17.02; 33.58 / 33.89) | **met** 16.88 / 17.23 | met 16.84 / 17.09 |
| M4 first span: gaps > 100 ms (capture / Dolphin's frames) | 3 / 3 in 290 s | **0 / 0** | 6 / 5 in 175 s | 6 / 5 |
| **P5** no read stall > 500 ms after 60 s | **met**: max 51.6 ms after 60 s (144.5 at boot); spin-up below | met (0 reads: page cache) | **met**: none after 60 s (369.7 ms at boot) | met (0 reads) |

**The details:**
- **P0b:** the started PID's name is `AppRun` (the runtime execs it, as PCSX2's); `-b` hides the main window. On run 1
  the window shows 640×480 while the shader pre-compile progress runs, then goes fullscreen. Every capture took the
  root screen, which the fullscreen window covers.
- **P0e:**
  - The CPU / JIT thread is named **`CPU thread`**; the GPU thread is `Video thread`.
  - **Pause:** F10 by `xdotool` (`windowactivate --sync`, `windowfocus --sync`, keydown / 0.12 s / keyup). The CPU
    thread's time stood from the first poll after the injection, so in the first 0.5-s window. Two full grabs 0.5 s
    apart were identical.
  - **Resume:** F10. The thread's time grew within the first 0.5-s window.
  - Running, the CPU thread used 13-36 ticks a second. **SIGSTOP was never needed.**
- **P0f:**
  - **Save:** Shift+F1 → `StateSaves/<game id>.s01` (the id stays on the hub). Its mtime was newer and its size stable
    0.21 s after the injection (the first poll), so ≤ 0.21 s.
  - **Load:** F1 → B52's picture check. Three distinct non-black grabs by 0.2 s of a 5-s grab at 10 fps (36-51
    distinct).
- **P1, T2:** a loading screen, then a copyright card, then (by ~18 s) **the game's own memory-card notice waiting for
  a button**. T2's menu-side numbers are at that screen (animated, 60 distinct fps). No title menu was reached without a
  press, and there was no attract loop. Read as met on the first interactive screen.
- **P2, T1:**
  - The 60-s capture holds the 60-fps title screen, then the 30-fps attract demo.
  - `n64_frames` over the whole capture snaps the rate to 30 (the mode): median 50 / 29, minimum 28 / 29 → met against
    30.
  - `t1_segments.json` reads each part against its own rate; the transition seconds are dropped.
- **P2, T2 run 1:** two seconds at 49-50 (s 37, s 54), each made of ~10 single repeated frames spread through the
  second. **Dolphin's own render times show no frame over 21 ms from 186 s to the exit**, across the whole capture span
  (207-267 s). The emulator presented every frame; the repeats are on the capture side, as H3-P1's T2. Not met by the
  pre-registered number; T2 run 2's minimum is 59.
- **Dolphin's counters, all runs:**

  | | T1 r1 | T1 r2 | T2 r1 | T2 r2 |
  | --- | --- | --- | --- | --- |
  | VIs per second | 59.90 | 59.94 | 59.72 | 59.63 |
  | VI p99 (ms) | 16.69 | 16.94 | 16.69 | 16.91 |

  The run totals include the boot, the pause and the state load.
- **P3:**
  - **The busiest core** is core 0 in every run (median 11.9 / 16.5 / 16.8 / 19.1 %).
  - **The `CPU thread`:** mean 13.9 / 13.4 / 33.4 / 32.7 %, max 38 / 23 / 47 / 45 %.
  - **The `Video thread`:** mean 7.8 / 7.6 / 39.6 / 39.1 %.
  - **The only seconds with a core ≥ 90 %:** T1 run 1 at 4-8 s after the launch, the shader pre-compile spread over up
    to 9 cores, and one second on T2 run 1's boot.
  - GPU p95 17-20 %; Tctl median 44-59 °C.
- **M4, the shader cache (informative):**
  - **T1:** the first span's gaps > 100 ms go **3 → 0**, and its boot core max goes 100 % → 53 %. The title shows by
    ~9 s instead of ~15 s.
  - **T2:** 6 → 6 (5 → 5 in Dolphin's frames). These are the boot's loading screens (single 1.3-1.8-s frames at
    2-8 s), not shader stalls.
- **P5, the drive:**
  - **T1 run 1:** the drive's last read was ~62 s after the launch, and there were 0 reads in the 10-min idle at the
    menu (the attract demo runs from memory).
  - **The provoked read**, after **~15.5 idle minutes:** Start then A twice by keyboard. The game loaded: 11 reads in
    one second, 38 ms each on average (420 ms in all), the first done 3.86 s after the Start press (the load began on
    the A presses at 1.5 / 3.0 s). **No spin-up delay.**
  - **T2 run 1:** 154 reads, all at the boot; 0 in the 3-min idle.
  - Run 2 of each title read nothing (the page cache).
  - **The drive's writes:** 0 since boot.

**Exit**, every run: SIGTERM to the started PID, gone in **0.31-0.47 s**, rc 0. The AppImage's FUSE helper outlived it
by a few seconds (1 process at +2 s and +5 s, 0 at the next check). B69 should wait for it.

**Validity:** every run read Dolphin. The window, the sink-input and the threads (`CPU thread`, `Video thread`) were
the started PID's, Vulkan on RADV, with no `bwrap` or wrapper process. **All four runs valid.**

## Disclosed

- **The fetch's href:** read from the rendered page and the host's release path, not from the HTML; a `curl` of the
  page meets the shield, and it was not bypassed.
- **T1 run 1's exit count "2":** two `--appimage-mount` processes left from the setup's `dolphin-tool` header read
  (01:14Z; that `kill` hit their subshell, not the runtime), with a stale FUSE mount from the first setup mount. Both
  were ended by PID and the mount unmounted with `fusermount -u` as the user, before T1 run 2. The run's own Dolphin
  left nothing.
- **The render-time logs:** Dolphin 2609b names them `render_times.txt` / `vblank_times.txt`, not the harness's
  `render_time.txt`. Run 1's were moved by hand at 01:35Z (no data lost), and the harness was fixed before run 2. A
  second leftover count (+5 s) was added after run 2.
- **`slot_existed_before`** in P0f counts any title's slot-1 file. The match is the newer mtime.
- **The first span:** the window → the end of P1's idle. That is 290 s for T1 and 175 s for T2 (T2's P1 idle is 3 min,
  as pre-registered), not the design's 5 min for T2.
- **The region:** read with `dolphin-tool header` (class only).
- **The AppImage's per-file list:** Dolphin's own `Sys/` database names files by game id. In git
  (`stage1/appimage_files.sha256`) the 2,626 `Sys/` paths below its second level are replaced by a hash of the path;
  every file's sha256 is kept. The unredacted list is `runtime/emulators/dolphin/appimage_files.full.sha256`
  (gitignored; its sha256 is in the file's header).
- **`redact_check.txt`:** the one remaining hit is the checker's own mount-path pattern in its source (as H3-P1's). The `__pycache__`
  from compiling the scripts was this session's own byproduct and was removed.

## The result per title

| | T1 (light) | T2 (heavy, measured at its first screen) |
| --- | --- | --- |
| P0a / P0b / P0c | met / met / met (the started PID) | met / met / met |
| P0e | met: hotkey F10, stood in the first 0.5 s, resumed in 0.5 s | met (the same) |
| P0f | met: save 0.21 s (30.6 MiB), load picture by 0.2 s | met: 0.21 s (18.2 MiB), 0.2 s |
| P1 | met: title ~15 s / ~9 s (cached) of 90 | met: first screen ~18 s |
| P2 | met: 60 / min 56 (title), 30 / min 28 (demo); both runs | run 1 median 60, **min 50 not met**; run 2 60 / 59 met |
| P3 | met: CPU thread mean 14 % max 38 %; GPU 10 %; Tctl max 54.5 °C | met: CPU thread 33 % / 47 %, Video 40 %; GPU 17-19 %; Tctl max 61.5 °C |
| P4 | met: p95 16.84 / p99 17.03 (60), 33.56 / 33.72 (30) | met: 16.88 / 17.23 |
| M4 (cache) | gaps > 100 ms 3 → 0 | 6 → 6 (loading screens) |
| P5 | met; no spin-up after ~15.5 idle min (11 reads, 38 ms avg) | met |
| P0d / P7 | not this run (streamed, after B69) | — |

**Reading:**
- The hub runs both GameCube titles at full speed in Dolphin 2609b, in hardware Vulkan at 1x, with wide margins. The CPU
  thread peaks below half a core, the GPU sits under 20 % and Tctl under 62 °C.
- The shader cache removes T1's few boot stalls.
- The drive neither stalled nor spun down.
- The one miss is the capture metric's (T2 run 1's minimum), not the emulator's.
- T2's gameplay, like T1's, is not measured here: that is P7's, streamed.

## B69's items (from P0b / P0c / P0e / P0f / P5)

- **The `dolphin` launch kind:** needed.
  - The command: `runtime/emulators/dolphin/dolphin-2609b-x64.AppImage -b -u data/games/gamecube/user -e <title>`.
  - The ini keys above, written per launch (or as `-C` per key).
  - Exit by SIGTERM to the started PID (0.3-0.5 s), then wait for the AppImage helper.
  - The PID's name is `AppRun`.
- **PID (capture):** not needed. The started PID's one visible window, fullscreen.
- **Audio:** not needed. One sink-input on the started PID (Cubeb / pulse).
- **Pause:** the F10 hotkey with the window focused by `xdotool`, confirmed by `CPU thread`'s time. SIGSTOP stays as
  the coded fallback; it was never needed.
- **States:** Shift+F<n> / F<n>. The file `StateSaves/<id>.s0<n>` is written and stable in ≤ 0.21 s (18-31 MiB). A
  load passes B52's picture check by 0.2 s.
- **The pads:** `GCPadNew.ini` for the four virtual pads (evdev; the device names read from Dolphin's log at P0d), and
  §2's GameCube layout. Untested here (no pads).
- **Keep-awake:** not needed on this evidence (no stall, no spin-up after ~15.5 idle minutes).
- **The metric for P7:** a title can switch between 60 and 30 (T1's title and demo). `n64_frames` per segment, or
  Dolphin's `vblank_times` / `render_times` beside it.
