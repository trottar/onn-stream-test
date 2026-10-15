---
memory_schema: 1
as_of: 2026-10-10
status: TASK HANDOFF — E4-S5, queue item 3: the SNES capture fault E4-S1 found (the encoder output exactly 59.0 fps with one dropped frame per second for a whole window, intermittent: 4 of 10 windows on 10-09, 0 of 3 in E3). Locate it from the recorded windows first, then three fresh 10-min SNES sessions with per-second logs; one change behind a flag only if the cause is named. Nothing adopted; nothing committed
---

# E4-S5 — the SNES 59-fps capture fault

**What was seen (E4-S1 §4, E4-S2 §2).** On SNES-STREAM the encoder's
capture ran at exactly 59.0 fps with one frame dropped every second,
from the first minute to the last, while RetroArch held 59.999 fps at
8 % of a core and the Snes9x core logged 60.0988 Hz as always. It is
not load (0.6 cores, 0 throttling). It recurred whole-window at
`CPUQuota=400%`, partly at 150 % and 4G, and never in E3's three
Snes9x windows or in E4-S2's other SNES runs. It probably explains the
row's 58.74 rendered fps. PS1 rows never show it.

**Hypothesis space (the offline pass decides).** Something settles
differently at session start and then holds for the window: (a)
RetroArch's estimated monitor refresh / dynamic rate control for the
Snes9x core (60.0988 Hz content on a 60 Hz capture; the PS1 core's
NTSC rate is different and never shows it); (b) the capture's own
clock vs the X window's update cadence (x11grab at 60 against a window
repainting at 59.x after a particular vsync state); (c) the encoder's
`-r`/vsync handling when the first frames arrive late. A whole-window,
exactly-1-per-second signature points at a rate mismatch set once at
start, not at jitter.

Read first: `e4_s1_2026-10-09/e4_s1_snes.md` and the SNES run
(`encoder.jsonl` per-second progress, RetroArch's session log,
`title.txt`), the same for E4-S2's 10 SNES windows and E3-A2's /
E3-S4's three (clean), `TOOLS.md` (the capture and encoder command, the
RetroArch config the suite writes, `video_refresh_rate`, vsync, the
Snes9x override), `e3_s4_2026-10-07/inventory.txt`.

## 1. Offline pass (no runs; before the pre-registration)

For every recorded Snes9x window (13) and, as the contrast, three PS1
windows: per second, the encoder's capture fps and drop counter; from
RetroArch's log, the estimated refresh rate line, any "frame timing" /
"audio sync" / vsync lines, the core's reported rate; from the suite's
config, `video_refresh_rate`, `video_vsync`, `video_swap_interval`,
`audio_sync`, `video_frame_delay`, and the Snes9x override's lines; the
X server's refresh at the time if logged. **Reading rule, written
here:** a value that differs between every faulty window and every
clean window names the cause; if none does, the fault is not visible
in the records and the fresh sessions must add instrumentation (§2).
`e4_s5_<date>/offline.md`.

## 2. Fresh sessions (pre-registered, hashed before them)

Three SNES-STREAM sessions of **10 min**, E2's warm-up, with the
suite's instrumentation plus: the encoder's progress at 1 s with its
`dup`/`drop` counters and input/output pts; RetroArch's log at the
verbose level that prints refresh estimation and frame timing (a
per-session config override the suite removes after); the X window's
actual update rate measured independently for 60 s (a `framemd5` of
the window at 120 fps, counting distinct frames per second, as R3c
did). **Stated before the runs:** whether the fault appears (capture
59.0 ± 0.05 with ~1 drop/s for ≥ 2 min) in any of the three, and what
the instrumentation shows at that time versus a clean session.

## 3. The one change (only if §1 or §2 names the cause; otherwise none)

Behind **`PRIVYHUB_SNES_CAPTURE_FIX=<name>`** (absent = today): one of
— the Snes9x override pins `video_refresh_rate` to the capture's rate
and disables refresh estimation; or the encoder's input rate /
vsync mode for the SNES source; or the capture's framerate matched to
the core's 60.0988 with the encoder resampling — whichever the cause
names, one only. Then **SNES-STREAM ×2 at 20 min with the flag**:
ACCEPTED if capture 60.0 ± 0.1 and dup+drop ≤ 0.2/min in both, rendered
≥ 59.5, RetroArch ≥ 59.9, and the row within E1's bands of its E4-S1
reference on host CPU. If the cause is not named, the task ends at §2
with the fault characterized and the next step proposed.

## 4. The record

`evidence/E4_S5_SNES_CAPTURE_59FPS_<date>.md` + `e4_s5_<date>/` (the
offline tables, the pre-registration + `.sha256`, the sessions, the
`framemd5` counts, the diff if any, `manifest.sha256`, `--check`,
`validity.json`, `redact_check.txt`); `docs/KNOWN_ISSUES.md` (the fault:
located / characterized); `patches/` if a tool changed;
`logs/e4_s5_git_status.txt`. Any flag absent; the adopted state
restored; no `e4_constraint.conf`; then the queue's close.
