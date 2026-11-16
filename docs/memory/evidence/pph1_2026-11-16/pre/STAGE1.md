# PP-H1 stage 1 (2026-11-16 16:02:59-16:05:29Z, unattended; outside 04:30-05:30Z and not within 45 min of it)

- **This repo** (`head.txt`, `git_status_before.txt`): HEAD **`a302339b`** (H7-V4 committed; the PP-H1 task in it); the
  tree clean but for this record's folder. Only `privyhub-companion` and `privyhub-diag` (`units_before.txt`); no
  game, no stream (`status_before.txt`); no emulator, encoder or Godot process (`processes_before.txt`). **Eighteen
  lines; `--check` ok** (adb up; the APK `ca53df0d…` CONFIRMED) (`check_before.json`, `eighteen.txt`).
- **The board game's repo** (`board_repo_before.txt`): HEAD **`21e7e44f`** (2026-11-12, "Hand-back note for the hub
  side"); `git status --short` empty, also with `--ignored`; 282 tracked files; `checks/` **25 scripts**
  (step0-step24, each with its `.uid`); Godot's cache `.godot/` absent and **git-ignored** (its `.gitignore`, line 2).
- **The owner's pictures folder** (`pictures_before.txt`): exists; **116 files, 15,039,288 bytes** (a listing hash of
  names and sizes kept off the repo's view as a 16-character hash only).
- **The hub** (`hub_facts.txt`): AMD Ryzen 5 PRO 4650G, 12 threads; memory 15,300 MB, 11,109 MB available; home disk
  134 GB free; the graphics device AMD Radeon (Renoir, integrated) on `amdgpu`; **Vulkan** offered (instance 1.4.309;
  RADV Renoir, Mesa 25.0.7; llvmpipe also listed) and **OpenGL** 4.6 core / ES 3.2 (radeonsi, direct rendering) —
  read with `vulkaninfo --summary` and `glxinfo -B`, both already on the hub; the X display the emulators use **`:0`**
  (the companion's environ), **1920 × 1080 at 60 Hz** on one output, a window manager (xfwm4) and the desktop panel
  running; at rest: load 0.15, graphics busy 0 %, VRAM 219 MB, CPU 31-34 °C, graphics 27 °C. The kernel offers the
  graphics busy share and memory (`gpu_busy_percent`, `mem_info_vram_used`). Godot's own folders under home absent.
- **The hub's saves** (`saves_before.txt`): 161 files (H7-V2's rule), no `.state8`.
- **Pre-registration hashed 16:05:29Z** (`758e0a0d…`), before the fetch.
