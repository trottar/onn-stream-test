---
memory_schema: 1
as_of: 2026-10-15
baseline_commit: 7331184 (plus the uncommitted E4-S1..S5C work and session A's E4-S5D as it lands)
---

# E5-S1 — the capability model, drafted, and the first probe

**Classification: MODEL DRAFTED; probe v1 runs on the reference and
classifies it `known-good` on all seven classes.** No class needed a
model fix. Sub-checks with no E4 number read `unknown` ("not measured;
E5-S2"), as the model says they must.

- **The model:** `docs/CAPABILITY_MODEL.md` (new). E5's seven classes,
  each with what is measured, how, the threshold **taken from E4's
  numbers** (E2 / C5 / D-BASE where E4 cites them), and what it enables or
  disables. No figure invented.
- **The probe:** `tools/capability_probe.py` (new). Host reads only;
  prints one JSON object, each verdict with its threshold beside it. No
  MAC, IP, SSID, interface name, disk serial or UUID is ever printed.
- One run on the reference, 2026-10-15T21:03:43Z, **with a stream live
  under session A** (`stream_live_at_probe: true`; E4-S5D's SNES run).
  That is fine for a host-read probe; it lowers MemAvailable, nothing else.
- Nothing adopted, nothing committed. Session B; task
  `handoffs/E4-C1_CLOSEOUT_AND_E5_S1_CAPABILITY_PROBE_TASK.md` Part 2.

## 1. What the probe said (`e5_s1_2026-10-15/probe.json`)

| class | verdict | the reading | the threshold it used |
| --- | --- | --- | --- |
| CPU / RAM / storage | **known-good** | CPU: the reference model, 6 cores / 12 threads, max 4308 MHz; RAM: MemTotal 14.94 GiB, MemAvailable 9.78 GiB (stream live), swap 12.3 GiB; storage: NVMe 256 GB + USB rotational 2 TB, media root 149.3 GB free, VOD root present, 1852.2 GB free | ≥ 6 physical cores at the reference speed class (400 % + 50 %); MemTotal ≥ 8 GB, MemAvailable ≥ 1.5 GiB (CONC 1,166 MB); storage **unknown** (not measured; E5-S2) |
| GPU / iGPU | **known-good** | 1 render node, driver `amdgpu` | exactly one usable node (the companion fails closed otherwise); the reference's driver |
| hardware encode / decode | **known-good** | VA driver radeonsi (renoir), Mesa 25.0.7; H.264 CB / Main / High + HEVC Main / Main10 encode; ffmpeg `h264_vaapi` (+ av1, hevc, mjpeg, mpeg2, vp8, vp9 vaapi); decode **unknown** | H.264 EncSlice + `h264_vaapi` + radeonsi → the live ladder 720p60 5000-7000 |
| validated stream profiles | **known-good** | 8 profiles from the repo table: the 720p60 reference ADOPTED + live ladder; four 1080p60 candidates; three C5-M3 low rungs | the encode class's verdict (validated on the reference only); the 1080p rung flag-only, client-limited |
| emulator tiers | **known-good** | cores present: mednafen_psx_hw, snes9x, bsnes, fceumm, blastem; PS1 4x, Snes9x, bsnes known-good; NES, Genesis **unknown** | PS1 ≥ 150 %, Snes9x ≥ 100 %, ≥ 384M; bsnes on the reference class with ≥ 6 cores (E2's 436-517 %) |
| concurrency headroom | **known-good** | 1,200 % of CPU time vs the stack's 400 %; MemAvailable 9.78 GiB; grabs under a stream: allowed; second activity: yes | ≥ 6 cores + ≥ 1.5 GiB; 2 GiB for a second activity |
| network | **known-good** | default route on a wired link, up, 1000 Mb/s full duplex; carries the 1080p rung | wired, up, ≥ 11.6 Mb/s (720p wire rate 1.45 MB/s, E2-S1); 1080p ≥ 18.1 Mb/s; **the loss row is the client link's, not probed** |

- **The reference is `known-good` on every class with a number**, as the
  task requires. No threshold was moved to make it so: every one was
  written into `CAPABILITY_MODEL.md` before the run, and the probe was
  run once.
- `adopted_lines` read **five** `PRIVYHUB_*` lines from the unit's drop-ins,
  `PRIVYHUB_SNES_CAPTURE_FIX=output_rate` among them: session A's
  E4-S5D had written `snes-capture.conf` by 21:03Z. Its adoption verdict
  is session A's (no `state_at_end.json` at that time).

## 2. What the model cannot say yet (E5-S2)

- **Only one machine, the reference.** Any other CPU model is `unknown`
  on every core-count threshold (the probe prints "if equally fast"
  beside it), because E4 measured one per-core speed.
- `unknown` sub-checks: storage, decode, NES, Genesis; not probed: iGPU
  headroom, the 720p60 encode rate on another VA driver, the 1080p rung's
  CPU floor, the loss row.
- **The 8 GB line:** the reference reads 14.94 GiB of 16 GB. An 8 GB
  candidate with an iGPU carve-out may read under 8 × 10⁹ B; E5-S2
  decides that line on the candidate itself.
- **E5-S2:** run the probe on a second machine (the user's choice) and on
  the alpha candidate.

## 3. Disclosures; files

- Host reads only: `/proc` (cpuinfo, meminfo, net/route, the
  processes' cmdlines for "stream live"), `/sys/class/drm`,
  `/sys/class/net`, `lscpu -J`, `lsblk -J -d` (type, size, rotational,
  transport only), `vainfo`, `ffmpeg -hide_banner -encoders`, the repo's
  `emulators.json`, `storage.json`, `native_stream_profiles.py` (parsed,
  not imported), the unit's drop-in directory. No sudo, no nft, the Opal
  untouched; nothing fetched; nothing started, stopped or restarted.
- Before the run, `py_compile` checked the probe; it wrote a bytecode file
  into `tools/__pycache__/` (gitignored), which session B removed
  straight after — its own artifact, seconds old, no data.
- **Files** (`e5_s1_2026-10-15/`): `probe.json`, `console.txt` (the
  command, rc 0), `probe_stderr.txt` (empty), `git_status_at_start.txt`,
  `redact_check.txt` (all OK), `manifest.sha256`.
- Git status: `logs/e5_s1_git_status.txt`.
