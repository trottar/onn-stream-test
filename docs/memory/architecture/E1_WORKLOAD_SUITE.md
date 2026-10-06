---
memory_schema: 1
as_of: 2026-10-05
baseline_commit: f60234e
status: FROZEN 2026-10-05 (E1-S1). Changes only by a dated amendment at the end of this file.
---

# The E1 workload suite — the frozen definition

The measurement base for Phase E (`docs/ROADMAP.md`, E1). E2's
measurements, E3's optimization loop and E4's floor all compare against
these workloads, run as defined here. Phase E's scope is NES / SNES /
Genesis / PS1; N64 and above are excluded.

- Record: `../evidence/E1_S1_WORKLOAD_SUITE_2026-10-05.md`.
- Inventory, pre-registration, runs: `../evidence/e1_s1_2026-10-05/`.

## 1. How it runs

One command, no hands:

```bash
python3 tools/e1_suite.py run --out <dir> --prereg <preregistration.txt> [--only ID[,ID]] [--runs 2] [--window 300] [--gap 120]
python3 tools/e1_suite.py compare <dir>     # the repeatability table -> repeatability.{json,md}
python3 tools/e1_suite.py manifest <dir>    # then: --check <dir>
```

- `--prereg` is required, and its `.sha256` must match. The suite runs
  only against a hashed pre-registration.
- **E1 uses 300-s windows. E2 uses 1200 s (`--window 1200`), with a new
  pre-registration.**
- Everything else is fixed here.

**Every run follows these steps:**

1. **Preflight.**
   - No `PRIVYHUB_*` in the user manager.
   - The companion's environ is exactly `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`.
   - The drop-in is present.
   - No game is active.
   - adb is up.
2. The row's flags, if any. Only E1-PS1-1080P has flags.
3. `systemctl --user restart privyhub-companion`, then confirm MainPID
   owns 8765.
4. **An idle gap of 120 s.** The sampler runs through it, and the gap gets
   its own summary.
5. Launch, then warm-up.
6. **The window.** This is the summary's span.
7. **Teardown to idle.**
   - Every path: flags unset (with a restart when any were set), the
     counter override removed, the adopted PS1 files checked.
   - Stream rows also: BACK, the decoder report, `POST stop`, the NOW
     PLAYING banner cleared, the APK hash.
8. A failing launch is retried at most twice. A run that cannot reach its
   steady state is recorded FAILED.

## 2. The workloads

| id | what | launch | fixture | warm-up | steady state | main process |
| --- | --- | --- | --- | --- | --- | --- |
| **E1-IDLE** | idle Linux + PrivyHub | nothing | — | 60 s | companion idle after restart, no game / stream, onn not driven | companion |
| **E1-PS1-LOCAL** | PS1 local emulation, no stream | counter override; `POST /plugins/games/launch` from the host; RetroArch `PAUSE_TOGGLE` on its command port (loopback, the port in `privyhub-input.cfg`), `GET_STATUS` PLAYING | Tekken 3 (USA) `game_ps1_b0a5986638f61a11`, the adopted 4x source | 60 s after PLAYING | the attract loop | retroarch |
| **E1-SNES-STREAM** | SNES through the companion with the onn | counter override (`config/bsnes/<rom>.cfg`); launch; the onn: force-stop, wake, `MainActivity`, tap `now_playing_preview_host`, `NativeStreamActivity`, recovery PLAYING | Super Mario World (USA) `game_snes_c6fecdcdddb35398`, core bsnes | 90 s after PLAYING | the title-screen demo loop | retroarch |
| **E1-PS1-STREAM** | PS1 + native streaming = **the 720p60 reference profile** (adopted, live default) | as SNES-STREAM | Tekken 3 | 90 s | the attract loop at 7000 / 1280×720 | retroarch |
| **E1-PS1-1080P** | the higher Phase-C profile: the 1080p rung (not adopted) | as PS1-STREAM with `PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p PRIVYHUB_ADAPTIVE_BITRATE_INJECT=1` for this row only; `inject?class=INCREASE_1080P` 75 s after PLAYING; 1920×1080 confirmed (one retry at +15 s) | Tekken 3 | 60 s after the switch | the attract loop at 12,600 / 1920×1080 | retroarch |
| **E1-META** | metadata / storage: the EPG grab | forced refreshes `POST /plugins/epg/refresh` in order over `ComedyCentral.us@East`, `CNBCUK.uk@SD`, `10Bold.au@Sydney`, `FoxSports1.us@HD`, `NBC.us@East`, `FilmBox.nl@Netherlands`, cycling; `GET /plugins/games/games` (library scan) every 30 s | the six channels | 60 s | grabs back to back | companion (the grabber child: `epg`) |
| **E1-CONC** | concurrent: PS1 streaming + the EPG cycle | E1-PS1-STREAM, with the E1-META cycle started 30 s after PLAYING | Tekken 3 + the six channels | 90 s | stream + grabs | retroarch |

Order: as listed. Each workload runs twice, back to back. Nothing is tuned
between runs.

**ABSENT. These rows are skipped and listed, with what would fill each:**

| row | why | what fills it |
| --- | --- | --- |
| Live TV | the video goes upstream → the onn, with no host share beyond TV-state and the EPG; no intent, extra or deep link starts a channel | a channel extra in a later APK, or a hand-tuned channel in E2; the host share is E1-META |
| browser source | Windows-only (PowerShell, ddagrab); no Linux implementation | a Linux source (Phase G/I) |
| camera source | Windows-only; no camera attached | a camera and a Linux source |
| NES, Genesis | no fixtures | the user supplies ROMs |
| metadata reconcile | it writes library metadata | the user's word to run it as a workload |

## 3. The sampler set

`tools/e1_sampler.py run <dir> [--telemetry] [--title]` at 1 s, plus:

- **Host:**
  - per-CPU busy, mean and max; iowait; PSI;
  - memory, swap and swap rates;
  - `/proc/diskstats` for `nvme0n1`: IOs, kB/s, await, util;
  - `eno1` bytes, packets and drops;
  - `gpu_busy_percent`;
  - `gpu_metrics` v2.2: gfx and VCN activity, socket / CPU / SoC power,
    clocks, temperatures, `throttle_status`;
  - hwmon PPT, Tctl, nvme temperature;
  - cpufreq.
- **Processes:** % of one core, RSS, PSS, RssAnon, threads and IO for
  companion, range_server, encoder, ffmpeg_other, retroarch,
  host_resource_sampler, epg, xorg, pulseaudio and e1_sampler.
  - RetroArch is found as `retroarch`, `RetroArch-Linux` or the
    AppImage's `AppRun`.
  - `other` is everything else: CPU only, plus its top three by `comm`.
- **Workload telemetry:**
  - C2 `/diagnostics/stream-telemetry` every 2 s (`--telemetry`);
  - RetroArch's window-title frame counter (`--title`), through the
    measurement-only counter override;
  - the runner adds the heartbeat log, `native-stream-status` every 10 s,
    the decoder report's fields, and the EPG cycle's log.
- **Not available on this host:**
  - RAPL (root-only);
  - wall power (no meter);
  - Intel-style throttle counters;
  - glass-to-glass latency (needs a camera).
  - `gpu_metrics`' VCN activity reads ~0 at 1 s even while encoding, so
    **encoder % of a core** stands in.

## 4. The summary schema (`<dir>/<id>/run<n>/summary.json`)

| field | contents |
| --- | --- |
| `workload`, `run`, `kind`, `main_process` | the run's identity |
| `started_utc`, `ended_utc` | timestamps |
| `window_s`, `gap_s`, `warmup_s` | the run's timing |
| `status` | `OK` or `FAILED` (+ `error`, `trace`) |
| `preflight` | manager, environ, game active, adb, drop-in, ok |
| `restart` | `mainpid_serves_8765`, manager, environ |
| `profile_at_start`, `profile_at_playing` | profile id, bitrate, size, `any_override`, adaptive mode |
| `launch` | HTTP result; the unpause or the stream open |
| `rung_injection` | 1080p row only |
| `gap`, `window` | `{from, to}` UTC |
| `host` | the sampler summary over the window: `host.<metric> = {n, mean, p95, max, min}`; `retroarch.frames_per_s`; `throttled_samples`; `missed_samples` |
| `key.heartbeat` | rendered fps, video loss/min, audio underruns, resyncs |
| `key.telemetry` | max output gap, control RTT, receive→decode, receiver loss/min |
| `key.status_poll` | share at 1920×1080 / 1280×720, bitrate min/max |
| `key.retroarch` | frames/s |
| `key.epg` | grabs, ok, failed, median / max grab s, scans, median scan s |
| `teardown` | report and fields, stopped, processes left, override removed, banner, `flags_absent`, `apk`, `ps1_files_identical`, `game_active` |

The idle gap's summary is in `sampler_summary_gap.json`.

## 5. The repeatability bar (run 1 vs run 2, the same window)

| metric | band | applies to |
| --- | --- | --- |
| host CPU mean | ± 2 points | every row |
| GPU busy mean | ± 3 points | every row |
| main-process RSS | ± 5 % | every row |
| RetroArch frames/s | ± 0.5 fps | game rows |
| rendered fps (heartbeat) | ± 0.5 fps | stream rows |
| share of the window at 1920×1080 | ≥ 0.95 in each run (a precondition) | E1-PS1-1080P |
| median EPG grab | ± 30 % | E1-META, E1-CONC |

- **Reported, not banded:**
  - video loss/min, audio underruns and max output gap (the link's loss
    row varies by time of day);
  - grabs completed and failed.
- **REPEATABLE** if every banded metric holds. Otherwise **NOT YET
  REPEATABLE**, with the failing metric and the suspected cause.
- The bands are not changed after data.

## 6. Status at freeze (E1-S1, 2026-10-05)

| row | status |
| --- | --- |
| E1-IDLE | REPEATABLE |
| E1-PS1-LOCAL | REPEATABLE |
| E1-SNES-STREAM | REPEATABLE |
| E1-PS1-STREAM | REPEATABLE |
| E1-PS1-1080P | REPEATABLE |
| E1-META | REPEATABLE |
| E1-CONC | **NOT YET REPEATABLE**: rendered fps 53.91 / 54.95. The stream degrades under the grab cycle (loss 2,827 / 2,311 per min, 45 / 38 resyncs, the ladder at 5500-7000), so the fps follows the loss |

E1-CONC's degradation is itself E2's first concurrency finding. It is not
fixed here.

## Amendments

### 2026-10-05 — E2-S1 §1: the VOD row added; the 1080p-rung row kept; the user's answers

**E1-VOD joins the suite (REPEATABLE).** The user's answer was that the
VOD drive is attached.

- Inventory: `../evidence/e2_s1_2026-10-05/vod/e1_vod_inventory.md`.
- Pre-registration: `e1_vod_preregistration.txt`, hashed `aa3ea03f…0a6f`
  at 15:18:51Z, before any VOD suite run.
- Two dry runs: 15:28-15:47Z.

| id | what | launch | fixture | warm-up | steady state | main process |
| --- | --- | --- | --- | --- | --- | --- |
| **E1-VOD** | VOD: a local file played on the onn, **direct play** (no host transcode exists) | force-stop the app, wake, `MainActivity`; tap `VOD >`, `MOVIES >`, the title; tap "Start Over" if the resume dialog shows; NOW PLAYING shows the title; tap RESTART (0:00); read the progress; tap the preview (fullscreen). Window end: BACK, read the progress. Teardown: RESTART, STOP (`POST /stop`) | `movies/Edge Of Tomorrow.mp4` on the external drive (read-only exFAT): 720×360 H.264, 918 kbps, 1:53:29 | 60 s | the film playing fullscreen; the range server serving it | range_server |

- **Key figure:** the progress ratio, played s / wall s, from the
  launcher's progress text over warm-up + window. Band ± 0.01.
- **Reported, not banded:** stall s/min; the range server's served kB/s.
  Served kB/s is its file reads (`rchar`), because the server's socket
  `send()` is not counted in `wchar`. The pre-registration named
  `wchar`; `rchar` is reported instead (a reported, not-banded figure).

| metric | run 1 | run 2 | band | holds |
| --- | --- | --- | --- | --- |
| host CPU mean % | 0.80 | 0.85 | ± 2 points | ✓ |
| GPU busy mean % | 0 | 0 | ± 3 points | ✓ |
| range_server RSS | 24.60 MB | 24.61 MB | ± 5 % | ✓ |
| progress ratio | 0.998 | 1.001 | ± 0.01 | ✓ |
| stall s/min (reported) | 0.13 | 0.0 | — | — |
| served kB/s, rchar (reported) | 78.5 | 79.8 | — | — |

- **E1-VOD is REPEATABLE.**
- **E1-CONC-VOD is ABSENT**: no host transcode exists, and direct play
  needs a second client.

**The 1080p-rung row (E1-PS1-1080P) stays in the suite.** The user
confirmed it on 2026-10-05. The rung itself remains NOT ADOPTED.

**The user's answers against the ABSENT rows:**

| row | answer, 2026-10-05 | status |
| --- | --- | --- |
| NES, Genesis | no fixtures | ABSENT |
| camera | none | ABSENT |
| wall power | no meter | ABSENT |
| Live TV | no unattended start | ABSENT |
| VOD | the drive is attached | **filled** (above) |
| browser source | — | ABSENT |
| metadata reconcile | — | ABSENT |
