---
memory_schema: 1
as_of: 2026-09-21
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
durable_memory_updated: true
---

# D-BASE-T1 — thermal telemetry, both ends

## Purpose

The host is to be an always-on server and the eventual PS2 / GameCube work
will need thermal headroom, so both ends' temperatures have to be on record
before any of it (user, 2026-09-21). Host thermals existed only as figures
in `D-BASE-S1` and `D-BASE-S2`, each taken by a sampler written for that
run and discarded; **the onn had never been measured at all.**

Diagnostic instrumentation only. No streaming, decoder, audio, emulator or
recovery behaviour changes, and **nothing acts on a temperature** — a
thermal pause on the recovery state machine is deferred with its reopen
condition in `investigations/DEFERRED.md`.

## Changed scope

**New: `PrivyHub/app/src/main/java/streaming/ThermalSampler.kt`**
-> `53eab0c1d96e958890f363622a919e1eeb49df20e5b4a7a9e56b3faf16cd8e88`.
Reads at most every 10 s however fast the caller ticks:
`PowerManager.getCurrentThermalStatus()` (the 0-6 NONE..SHUTDOWN scale),
`getThermalHeadroom(10)` (NaN when the device does not forecast — **carried
as NaN, never replaced**), and each readable `/sys/class/thermal/thermal_zoneN`
`temp` with its `type`. Registers a `OnThermalStatusChangedListener` and
counts changes. Keeps status and headroom min/max/end, per-zone
start/min/max/end, and a per-minute series capped at 240 entries.

**`NativeStreamActivity.kt`**
-> `e0c013f6ddcc37b0031a59d2e412925b0aa5dfd531fe7246f8afbc7210673dda`.
Five touch points: the sampler field; `start()` in `startSession`;
`sample()` on the existing metrics tick; `stop()` in `stopSession` after
the report is cached; `thermalQuery()` appending the three fields to the
heartbeat URL; and the `thermal` block in `buildSessionReport`. **Each
field is omitted when the device does not report it** — an absent field is
the finding, and a substitute number would not be.

**New: `tools/host_resource_sampler.py`** — `D-BASE-S1`/`S2`'s ad-hoc
sampler as a permanent tool. One JSON line every `--interval` seconds
(default 30) to `logs/games/host_resource_samples.jsonl`: `hwmon`
temperatures by sensor name, GPU power, load average, and CPU %, RSS,
RssAnon, RssFile, swap and threads for RetroArch, the companion, the
encoder, the audio ffmpeg and the FEC relay. `--once` prints one sample and
writes nothing. Rotated at 4 MiB keeping 3 by the same
`games.log_rotation.append_line` the heartbeat log uses.

**New: `companion/games/host_resource_sampling.py`** — starts and stops the
sampler with the stream. Separate process at `nice 10`, idempotent (the
recovery path may call `start()` on a running session), and **every failure
swallowed**: if the sampler will not start the session starts anyway and
`status` reports the error.

**`companion/native_stream.py`**
-> `11a182e7993f47891111018d40ef84342c1a2a018d1c890094df6857729d1162`
(from `c5f12e8f76f4cef2f6c04b2e19abc48b8133cbde538dad5a8457ad62b9a0e406`).
`start()` / `stop()` hooks for the sampler, and `host_thermal_c` plus
`host_resource_sampler` on `native-stream-status`. `host_thermal_c` reads
hwmon directly rather than the sampler's log, so `status` is answerable
whether or not a session is running.

**`companion/games/decoder_session_log.py`**
-> `a4815182eb66bb1ad2eedecfa87a0775ffabadf5d4607a9317c484479a997c5f`.
Each written session log gains a sibling `host` block carrying
`host_thermal_c` at the moment the report landed, so one file holds both
ends: the onn's in `report.thermal`, the host's beside it.

**`companion/games/native_stream_heartbeat.py`**
-> `8fb47b11998d75a485a8dfec4f6889e7a94da6e2686a1bef846a8ad4f545287d`, and
**`companion/plugins/games.py`**
-> `9545f03939c36a07323071ae75a1c0a991887bf2d71b4b5cb90f5ca5635bd928`.
`thermal_status` (int), `thermal_headroom` (float) and `thermal_zones_c`
(string, capped at 512 chars) are accepted and recorded per heartbeat, each
optional and each absent rather than defaulted.

**`companion/diagnostics/retention.py`**
-> `b3e2b71cc5887cdc69c67fbc547814ab0f7f1effbd2387de135f5cd1e7c79665`.
**Comment only.** The sampler rotates into `logs/games/stream_log_archive/`,
which the existing `stream_log_archive` family already bounds, so the
family's note now says so. Comments sit outside `POLICY`, so **the policy
SHA-256 is unchanged at `b13fbc32…71b5`** — verified by recomputing it.

APK: `1bc95f0ab2526ece25610bcc1f1c1500926ab0c34c3cd42fa4f4872616d212f0`.

**Unchanged:** every streaming constant, the decoder, the audio path, the
FEC wire format, the recovery state machine, the emulator lifecycle, and
the retention policy's content.

## One correction during the work

The first build's per-minute series came out **empty on this device**. The
spec's fallback chain is hottest zone, else headroom — and the onn reports
*neither*: `/sys/class/thermal` is permission-denied even to the adb shell,
and `getThermalHeadroom` returns NaN on SDK 34. Nothing continuous was left
to record.

Rather than ship an empty artifact or fake a number, the chain was extended
one step to `thermal_status`, the only signal this device does report, and
`series_columns` names which of the three a given report used
(`seriesSource()`). The two sessions were re-run on the corrected build;
the first pair is kept as `V1_preseries` / `V2_preseries` because they are
the evidence for the device finding.

## Validation performed

- real `sh ./gradlew :app:assembleDebug --no-daemon`; `adb install -r`;
  `python3 -m py_compile` on all six touched or added Python files;
  companion restarted with 8765 checked free (D-068); `git diff --check`
  clean;
- two 10-minute attract sessions of the PS1 reference title, zero input,
  BACK to end, teardown between, per `TOOLS.md`;
- `tools/diagnostic_retention.py` listing the `stream_log_archive` family
  and reporting the unchanged policy SHA-256.

## Result

See `evidence/D_BASE_T1_THERMAL_TELEMETRY_2026-09-21.md` for the numbers
and the classification.

**The onn reports status only.** `thermal_status` is available and reads
**0 (NONE)** throughout; `getThermalHeadroom` returns NaN, recorded as NaN;
`/sys/class/thermal` is permission-denied, so `zones_readable` is 0. That
is a property of the device, not of the code, and it is exactly what the
task asked to be stated plainly rather than worked around.

**No threshold is set and nothing acts on any reading.**
