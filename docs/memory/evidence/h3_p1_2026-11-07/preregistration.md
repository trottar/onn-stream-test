# H3-P1: pre-registration (written and hashed before the fetch, 2026-11-07)

Sources: `architecture/H3_P1_PS2_PROBE_DESIGN_2026-11-07.md` (the spec: §3's rows verbatim below), the task
`handoffs/H3-P1_PS2_PROBE_RUN_TASK.md` (P0d, the 90-s bound, the validity rules), the user's "Yes to both"
(2026-11-07). Titles are T1 (light) and T2 (heavy); the BIOS "present", its region a class only.

## The metrics (design §3)

| # | metric | how (A) | unit |
| --- | --- | --- | --- |
| M1 | fps vs the title's native rate | a 60-s `x11grab` recording of the window at its native size → unique frames (`mpdecimate`) per second; PCSX2's own on-screen performance figures beside it as a cross-check | median and minimum fps over 60 s, against 60 (NTSC) / 50 (PAL) |
| M2 | CPU per core | `mpstat -P ALL 1` and `pidstat -t -p <pid> 1` (PCSX2's threads: the EE / VU / GS threads by name) | per-core busy %, per-thread % |
| M3 | GPU busy | `/sys/class/drm/card0/device/gpu_busy_percent` at 1 Hz | % |
| M4 | frame-time p95 | the unique-frame intervals of M1's recording | ms, p50 / p95 / p99 |
| M5 | disc-read stalls | `iostat -x 1` on the drive's block device (r_await, %util) + `/sys/block/<dev>/stat` read-time; a stall = a second with a read wait > 500 ms; M4's frame gaps > 100 ms laid beside it | count, longest, coincident frame gaps |
| M6 | thermals | `sensors` k10temp Tctl at 1 Hz | °C max / median |

## The pass rows (design §3, verbatim; P7 is B49's, not run here)

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

**P0d (the task's addition):** the movies drive's health counters read without root (`smartctl -A` if unprivileged,
else `udisksctl info`, else `/sys/block/<dev>/device`): power-on hours, start/stop or load-cycle count, reallocated /
pending sectors, temperature — whichever are readable, and which were not. Informative; no pass bar. (Read before this
file was hashed: none of the SMART counters is readable without root on this USB disk; `p0d_drive_health.txt`.)

**T2** repeats P1-P5 (P1 with a 3-min idle instead of 5; P5 without the spin-up read, which is T1's). A title failing
P2 at 1x is recorded as its tier (H4's "selected PS2"), not retried with hacks. P6 is T1's (stage 2).

**The 90-s boot bound:** P1 counts from the launch command to the title's first menu / title screen on the window.

## Validity

A title's run is **invalid** (not failed) if:
- PCSX2 was not the process read (the PID / window / threads measured were not the emulator's);
- the renderer fell back to software (invalidates P2-P4; OpenGL after a Vulkan failure is hardware and valid,
  recorded);
- (stage 2) a pad was on the onn's path rather than a pad on the hub.

Also recorded, not invalidating: the window found by name if `--pid` missed (P0b → B49), the audio stream not
matched by PID (P0c → B49).

## The privacy rule

No BIOS or game file name, title, serial, hash or path in git or any record; T1 / T2; the BIOS "present", its region
as a class. Recordings stay in `data/games/ps2/probe/` (gitignored); only numbers and counts are copied out.
Nothing written to the drive.

Nothing adopted; nothing committed.
