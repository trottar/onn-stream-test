# PrivyHub capability model (E5)

**Status: DRAFT v1 (E5-S1, 2026-10-15).** Drafted from E4's measurements on
one host, the reference (HP EliteDesk, Ryzen 5 PRO 4650G, 6 cores / 12
threads, 16 GB, NVMe, wired). Probe: `tools/capability_probe.py`. Close-out
the thresholds come from: `docs/memory/evidence/E4_CLOSEOUT_2026-10-15.md`.

**Rules of the model.**

- **Every threshold below is an E4 (or E2 / C5 / D-BASE) number, with its
  record.** Where no record has a number, the class says **"not measured;
  E5-S2"** and the verdict is `unknown`. No figure is invented here.
- **Two caveats inherited from E4**, binding on every CPU and memory
  threshold: **CPU-time ≠ slow-core** (the floors are CFS bandwidth on the
  reference's full-speed cores) and **cgroup ≠ host** (the floors exclude
  Xorg, pulseaudio, the desktop, the OS).
- **Speed class.** E4 measured one per-core speed: the reference's. A CPU
  is in the **reference speed class** only if its model string is the
  reference's. Any other CPU is `unknown` on every core-count threshold
  until E5-S2 measures it; the probe still prints its counts against the
  floors, marked "if equally fast".
- A feature is enabled only where the host is known to support it
  (ROADMAP §E5). `unknown` enables nothing beyond what is already the
  default; it is a prompt to measure.

**Verdicts** (the probe prints the threshold each one used, beside it):

| verdict | meaning |
| --- | --- |
| `known-good` | meets the recommended alpha's **today** column (grabs may run under a stream) |
| `deferral-only` | meets the alpha's **with deferral** column only: guide grabs must wait while a stream is live (`PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1`, built, **not adopted**, E4-S4) |
| `below-alpha` | meets a measured floor but not the alpha's margin |
| `below-floor` | under a measured floor, or missing a requirement (e.g. no VAAPI H.264) |
| `unknown` | no E4 number applies: **not measured; E5-S2** |

## 1. CPU / RAM / storage

| sub-check | measured how | threshold (source) | enables / disables |
| --- | --- | --- | --- |
| CPU model, physical cores, threads, max MHz | `lscpu -J`, `/proc/cpuinfo` | reference speed class (model string); **physical cores ≥ 6 → `known-good`** (alpha today: 400 % floor + 50 %, E4-S2 §5); **≥ 4 → `deferral-only`** (alpha with deferral: 150 % floor, E4-S2 §5 / E4-S4); **logical CPUs × 100 % ≥ 150 % → `below-alpha`** (PS1-STREAM's floor, E4-S2); else `below-floor` | a stream at all (150 %); grabs under a stream (400 %) |
| RAM, swap | `/proc/meminfo` (MemTotal, MemAvailable, SwapTotal) | **system ≥ 8 GB** (MemTotal ≥ 8 × 10⁹ B; alpha, E4-S2 §5); **MemAvailable ≥ 1.5 GiB → `known-good`** (the stack's swap-off floor, CONC 1,166 MB peak, E4-S3B); **≥ 1.25 GiB → `deferral-only`** (a grab alone, 976 MB peak, E4-S3B §4); **≥ 384 MiB → `below-alpha`** (a stream alone, ≤ 384M, 228 MB peak, E4-S3); else `below-floor`. Swap is reported, not required (the floors are swap-off) | grabs under a stream (1.5 GB); the guide grabber at all (1G) |
| storage | `lsblk -J` (type, size, rotational, transport — no names, serials or UUIDs); free space of the media root (`<repo>/media`) and of the configured VOD root (`data/storage.json`) | **not measured; E5-S2** (E2/E4 recorded no storage latency or throughput threshold; VOD direct play costs ~0 CPU, E4-S1) | — (reported only) |

A machine with a large iGPU carve-out reads MemTotal below its nominal size
(the reference reads 14 GiB of 16 GB). An 8 GB alpha candidate may read
under 8 × 10⁹ B: **E5-S2 decides that line on the candidate itself.**

The class verdict is the worse of CPU and RAM; storage is `unknown` and
does not lower it.

## 2. GPU / iGPU

| measured how | threshold (source) | enables / disables |
| --- | --- | --- |
| render nodes under `/sys/class/drm` (`renderD*`), each node's kernel driver (the `device/driver` link's name); no `lspci`, no bus addresses | **exactly one render node** — the companion fails closed on zero or several (`companion/native_stream.py`, `_linux_vaapi_device`; Phase D validated the single-node case). Driver = the reference's (`amdgpu`) → `known-good`; another driver → `unknown` (not measured; E5-S2); no node → `below-floor`; several → `below-floor` (fail-closed) | the hardware encoder path at all |
| iGPU load at the reference stream | 18-23 % busy at PS1-STREAM (E4-S1) — **headroom not probed** (needs a load; E5-S2) | — |

## 3. Hardware encode / decode

| measured how | threshold (source) | enables / disables |
| --- | --- | --- |
| `vainfo` (profiles × entrypoints; the VA driver name) and `ffmpeg -hide_banner -encoders` filtered to `vaapi` | **H.264 `VAEntrypointEncSlice` + ffmpeg `h264_vaapi` + the reference's VA driver (`radeonsi`) → `known-good`**: the live ladder (720p60, 5000-7000 kbps, C3-L4) at the reference's cost (encoder 36 % of a core at 720p, 73 % at 1080p, E4-S1). H.264 encode present with another driver → `unknown` (the 720p60 rate not measured; E5-S2). No H.264 VAAPI encode → `below-floor` ("a host without VAAPI H.264 is out of scope", E4-S2 §5) | native game streaming; the live ladder |
| decode profiles (H.264 / HEVC / VP9 `VAEntrypointVLD`) | **not measured; E5-S2** (no host-side decode workload in E1's suite: VOD is direct play, decoded on the client) | — (reported only) |

## 4. Validated stream profiles

| measured how | threshold (source) | enables / disables |
| --- | --- | --- |
| the companion's profile table, read from the repo (`companion/native_stream_profiles.py`), **not measured by the probe** | each profile's status is its record's: `native_game_720p60_reference` **ADOPTED** (D-BASE close-out 2026-09-23; the default) with the **live ladder 5000-7000** (C3-L4, adopted); the four 1080p60 profiles **candidates, not adopted** (C5-M1/M2; the rung behind `PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p`, C5-CLOSE); the three low rungs **screened, never the default, never on the live ladder** (C5-M3, for Phase G). The class verdict is the encode class's: the profiles were validated on the reference only | enabled by default: the 720p60 reference + the live ladder, when encode is `known-good`. The 1080p rung stays a flag on every host (client-limited: the onn's spike row 317.9/min at 1080p, C5-CLOSE) |

## 5. Emulator tiers

| tier | measured how | threshold (source) | enables / disables |
| --- | --- | --- | --- |
| PS1 (`mednafen_psx_hw`, the 4x source) | the core file present under RetroArch's Linux core dir (`companion/games/config/emulators.json`, `platforms.linux.retroarch.cores_directory`) | core present + CPU ≥ the stream floor **150 %** (E4-S2) + memory ≥ **384M** (E4-S3); at the reference: stack 95 % of a core, 354 MB (E4-S1) | PS1 streamed |
| SNES (`snes9x`, adopted) | the same | core present + CPU ≥ **100 %** (SNES-STREAM ≤ 100 %, 0.61 cores, E4-S2) + memory ≥ **384M** (197 MB peak, E4-S3); reference stack 60 % of a core | SNES streamed |
| SNES heavy (`bsnes`, not the default) | the same | RetroArch alone 436-517 % of a core (E2-S1); **no floor measured** — `known-good` only on the reference speed class with ≥ 6 physical cores (where it ran at 59.7-60.0 fps, E2-S1); else `unknown` | the bsnes core by choice |
| NES (`fceumm`), Genesis (`blastem`) | the same | **not measured; E5-S2** (no fixtures, E1-S1) | — |

The class verdict is the worse of the PS1 and SNES (Snes9x) tiers; bsnes,
NES and Genesis are reported and do not lower it.

## 6. Concurrency headroom

| measured how | threshold (source) | enables / disables |
| --- | --- | --- |
| physical cores, logical CPUs, MemAvailable against the floors (the probe's own reads, §1) | **grabs under a stream: the stack's 400 % (CONC, E4-S2) with the alpha's margin → ≥ 6 physical cores at the reference speed class, and MemAvailable ≥ 1.5 GiB → `known-good`**; ≥ 4 cores and ≥ 1.25 GiB → `deferral-only` (the stack's floor drops to 150 %, CONC + deferral 0 s throttled, E4-S4); a second concurrent activity needs **2 GB for the stack** (E4-S2/S3B) — reported as `second_activity` yes / no | the EPG grab cycle while a stream is live, or its deferral; a second activity beside a stream |

## 7. Network

| measured how | threshold (source) | enables / disables |
| --- | --- | --- |
| the default-route interface (from `/proc/net/route`; **no address, no interface name, no MAC, no SSID printed**): wired or wireless (`/sys/class/net/<if>/wireless`), operstate, link speed (`/sys/class/net/<if>/speed`), duplex | **wired, up, link speed ≥ 11.6 Mb/s → `known-good` for the 720p reference** (its measured wire rate 1.45 MB/s, E2-S1 §6, with PCM 2/4 audio; since G-A2 (2026-10-19) the audio is Opus, ~2.9 Mbit/s less: ~9.0 Mbit/s at 7000 on the LAN, CL-B5 — the threshold is kept, measured on the PCM rate; the reference host is wired, D-BASE); ≥ 18.1 Mb/s also carries the 1080p rung (2.26 MB/s, E2-S1 §6). A wireless host → `unknown` (not measured; E5-S2). Down or slower → `below-floor` | native streaming from this host |
| **the client's link class** (2026-10-23): the client's own Wi-Fi reading — band, RSSI, tx link rate — in its heartbeat (B3; on by default in the client since B13; recorded on the host with `PRIVYHUB_LINK_REPORT=1`, G-A3 prepared); **not a host probe** | **5 GHz → `known-good`**: 0 uplink silences ≥ 250 ms and 0 hitch s per 10 min at −68 dBm, tx 130-260 Mbps (LINK-R1, one window). **2.4 GHz → `below-alpha`**: 16-22 silences and ~20 hitch s per 10 min in every room at the same −68 dBm (BENCH-R1 cell 8, BENCH-R3 C); the tx rate fell to 27-81 Mbps beside BENCH-R3's 42-silence cluster. **RSSI ≤ −72 dBm or tx ≤ 54 Mbps held 10 s → `below-alpha`** — the notice's thresholds (B14), chosen beyond this house's −68 / ≥ 108 Mbps normal; **not measured as a floor; E5-S2** | the on-screen link notice (B14, a flag); a ladder cap on a weak link (B13 §4, not built) |
| **the link recovery** (2026-10-24): the host's six-line stack — the input hold, B6, B8, the `state` path, the client's stall signal, the stall resume with the fast ready — as one line, `PRIVYHUB_LINK_RECOVERY=1` (B20; G-A4 prepared, not adopted); the client half on by default from APK `20e3e339…` (B19); measured on the bench shim's `blackout-4s@both` / `@down`, not a probe | **a 4-s drop → the picture held ≤ ~4.5 s (4.13-4.47 s) and 24-26 frames restored** (net, to a save ~0.40 s after the onset); the resume 133-458 ms after the link returns; 0 encoder restarts, 0 v2 handovers (CL-B11, 10 of 10 blackouts, `e2db0aa0…`). Saves: one per real stall (≥ 400 ms); none at a session's end from B18 (not yet measured, CL-B12) | a two-way or picture-only drop up to ~4 s costs ≤ ~0.5 s past its end and ~0.4 s of play; longer drops hand over to recovery v2 (its 5-s hold, its encoder restarts, the 120-s give-up) |
| **the loss row**: post-FEC video loss < 10/min on the client's link (D-BASE: 8.67 / 8.40) | **not measurable by a host probe** — a property of the client's link; reported as such. 0 of 60 stream runs met it since 2026-10-09 (E4-C1 §5); the link watch (E4-S4D) is the open item | stream quality judgements |

## What the model does not yet cover (E5-S2)

- **A second machine** (the user's choice) and **the alpha candidate**:
  the probe has run on the reference only. Every `unknown` above is a
  measurement on those machines.
- **Speed class** beyond the reference's model string.
- **Storage** throughput / latency, **iGPU headroom**, the **720p60 encode
  rate** on a non-reference VA driver, **NES / Genesis**, the **1080p
  rung's CPU floor**, **wall power**.
