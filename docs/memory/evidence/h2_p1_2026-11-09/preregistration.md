# H2-P1: pre-registration (written and hashed before the fetch, 2026-11-09)

Sources: `architecture/H2_P1_GAMECUBE_PROBE_DESIGN_2026-11-08.md` (the spec; its §4 verbatim below), the task
`handoffs/H2-P1_GAMECUBE_PROBE_RUN_TASK.md`, the user's "Yes to dolphin" (2026-11-09). Titles are T1 and T2 only.

**Not this run:** P0d and **P7** (both "streamed (B61)": the onn's pads over Bluetooth, after B builds the GameCube
launch kind). M7 is P7's metric and is not measured here. Every other row (P0a, P0b, P0c, P0e, P0f, P1-P5) is this run's.

---

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

---

## This run's rules (the task's additions; fixed before the fetch)

**The titles, by size (the design's "else" rule; the user named none):** T1 = the smallest `.rvz` in the drive's
GameCube folder (158 MB), T2 = the largest (1,177 MB). 27 `.rvz` counted; the one small `.bin` is not a title and is
not read. The rule that picked them is this one.

**Each title is run twice** (run 1, run 2), the second for M4's shader-cache comparison (the first 5 min of run 1 vs
the same span of run 2; informative). Every row is read on every run; the record gives run 1 and run 2.

**Per run, in order:** the launch (the started PID; P0a's start, P0b, P0c) → the boot to the menu (P1: ≤ 90 s from
the launch command to the first title / menu screen) → idle at the menu (P1: 5 min for T1, 3 min for T2) → P0e (the
pause hotkey by `xdotool`, the CPU / JIT thread's CPU time standing ≥ 0.5 s within 1.5 s; the resume restarting it;
else SIGSTOP / SIGCONT, the method recorded) → P0f (a save-state hotkey: the slot file's mtime newer and size stable
0.5 s within 10 s, the write time recorded; a load hotkey: B52's picture check, ≥ 3 distinct grabs not black within
5 s) → the 60-s `x11grab` capture of the window (P2 / P4; `format=yuv420p,showinfo` → `tools/n64_frames.py`;
Dolphin's on-screen FPS counter beside it) → the idle for P5 (T1 run 1: 10 min at the menu, then one provoked read
and its spin-up seconds; T2 run 1: 3 min; run 2: the P1 idle stands as the P5 window) → a clean exit (SIGTERM, then
SIGKILL after 5 s; no process left). `mpstat -P ALL 1`, `pidstat -t -p <pid> 1`, `iostat -x 1` on the drive,
`gpu_busy_percent` and k10temp Tctl at 1 Hz run through the whole run (P3 / P5).

**The native rate:** NTSC titles 60 (59.94 Hz), PAL 50 (×1.2 on P4's bars, P2's "−1 / −5" against 50); the region
class is read from Dolphin, never the game id. P2's internal rate snaps to 20 / 30 / 60 (`n64_frames`); P2 and P4's
static / black seconds are excluded as `n64_frames` excludes them, and the raw unique-frame figures (H3-P1's
`mpdecimate` reading) are given beside.

## Validity

A run is **invalid** (not failed) if:
- Dolphin was not the process read (the PID / window / threads measured were not the emulator's);
- the renderer was a software one (llvmpipe / the software renderer) — invalidates P2-P4; OpenGL in hardware after a
  Vulkan failure is valid, recorded;
- a `bwrap` (or any sandbox / runtime process) sat between the started PID and the emulator.

Also recorded, not invalidating: the window found by a child PID if `--pid` missed (P0b → B69's PID item); the audio
stream not on the started PID (P0c → B69's audio item); the pause by SIGSTOP (P0e's method); the drive's first read
after an idle (P5, informative).

A title failing P2 at 1x is recorded as its tier (H4's "selected GameCube"), not retried with hacks.
