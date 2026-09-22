---
memory_schema: 1
as_of: 2026-09-21
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-T1 — thermal telemetry, both ends

## Classification

**RUNTIME VALIDATED**, with one device limitation stated plainly rather
than worked around: **the onn reports thermal *status* only.** Its
headroom reads NaN and its `/sys/class/thermal` is permission-denied, so
two of the three client fields have nothing behind them on this hardware.
That is a property of the device, and the task asked for it to be said
rather than filled in.

Four of the five checks pass literally; the fifth — "heartbeats must carry
the three thermal fields" — carries the one field the device supplies, in
all 600 heartbeats across the two sessions, and omits the other two
because the device returns nothing for them. No number was invented.

## Why this exists (durable)

The host is to be an **always-on server**, keeping it and the onn cool
matters so nothing burns out, and the eventual **PS2 / GameCube** work will
need thermal headroom (user, 2026-09-21). Host thermals had been measured
twice — `D-BASE-S1` (CPU 42-44 → 57-59 °C plateau, GPU 38-40 → 46-49 °C,
encoder CPU flat at 26-27 %) and `D-BASE-S2` — each with a sampler written
for that run and thrown away. **The onn had never been measured at all.**

## What the onn reports — the answer to "which readings are available"

| reading | available? | evidence |
| --- | --- | --- |
| `getCurrentThermalStatus()` | **yes** | 61 samples per session, all **0 (NONE)** |
| `getThermalHeadroom(10)` | **no** | returns NaN on SDK 34; `headroom_supported: false`, `headroom_samples: 0`, min/max/end all recorded as the string `"NaN"` |
| `/sys/class/thermal` zones | **no** | `zones_readable: 0`. Checked directly: `adb shell ls /sys/class/thermal/` returns **`Permission denied`**, so SELinux blocks it for the shell user, let alone the app |

**The onn ran at thermal status 0 (NONE) for the whole of both sessions**,
which is the lowest of the seven levels — no throttling, not even LIGHT.
`status_changes` reads 1 in each session, which is the listener's
registration callback, not a transition: `status_min` and `status_max` are
both 0, so nothing moved.

The per-minute series therefore carries `thermal_status`, not a
temperature. `series_columns` names which of the three signals a given
report used, so a future device that does expose zones will produce a
temperature series in the same field without any reader change.

## Side by side over ten minutes

Both sessions, PS1 reference title, attract mode, zero input.

| | V1 | V2 |
| --- | --- | --- |
| duration | 603,813 ms | 603,839 ms |
| **onn** thermal status min/max/end | 0 / 0 / 0 | 0 / 0 / 0 |
| onn status samples | 61 | 61 |
| onn headroom | NaN (unsupported) | NaN (unsupported) |
| onn readable zones | 0 | 0 |
| onn series entries | 11 | 11 |
| **host** hottest sensor (`host_thermal_c`) | **54.38 → 60.50 °C** | **53.75 → 60.25 °C** |
| host `k10temp` Tctl | 54.38-60.50 °C | 53.75-60.25 °C |
| host `amdgpu` edge | 45.0-50.0 °C | 45.0-50.0 °C |
| host CPU sensor at report time | 60.12 °C | 60.25 °C |

**The host warms and the onn does not report warming.** Over ten minutes
the host's hottest sensor climbs ~6 °C to about 60 °C — the same ramp-to-
plateau shape `D-BASE-S1` recorded over 30 minutes (42-44 → 57-59 °C) —
while the onn sits at status NONE throughout. Whether the onn is actually
cool or merely silent cannot be told from status alone; **this device gives
no way to distinguish those**, and that is the finding.

`k10temp` is the hottest sensor in every sample, so `host_thermal_c` tracks
the CPU package rather than the GPU or the NVMe.

## Host resource sampler

20 lines per session at the 30 s default, both sessions, with `k10temp`,
`amdgpu` **and** `nvme` present in every one.

| role | V1 RSS (kB) | V2 RSS (kB) | CPU % |
| --- | --- | --- | --- |
| retroarch | 157,740 → 250,228 | 157,616 → 251,804 | 26.8-38.8 |
| companion | 48,052 → 51,744 | 51,808 → 51,860 | 23.1-24.7 |
| encoder | 120,060 → 120,512 | 120,044 → 120,504 | 26.2-27.4 |
| audio ffmpeg | 50,480 | 50,596 | 0.8-0.9 |
| fec_relay | *shares the companion's* | *shares the companion's* | — |

All four roles the task named are sampled with non-zero RSS in all 40
lines, plus the audio ffmpeg. `cpu_pct` is absent from the first line of
each session by design: a CPU percentage needs two samples of the same pid,
and a figure averaged over a process's whole lifetime would be a different
quantity wearing the same name.

**The FEC relay is a `threading.Thread` inside the companion**
(`companion/native_fec_relay.py`), not its own process, so it has no RSS of
its own. Rather than leave a gap that reads like a failed sensor, its entry
carries `hosted_in: "companion"`, `shared_with_host: true` and the
companion's own figures. RetroArch's 157 → 250 MB climb over ten minutes is
the warm-up `D-BASE-S2` characterized as file-backed and self-limiting.

## The other checks

- **`native-stream-status` carries `host_thermal_c`** — 47.85 °C idle after
  teardown, 46.88 °C before the sessions, and the decoder session log's new
  `host` block carried 60.12 / 60.25 °C at each report's arrival.
- **`tools/diagnostic_retention.py` lists the family** the samples rotate
  into: `stream_log_archive: files=0 total_mib=0.000 limit_mib=32.000`.
  The sampler rotates into that same directory as the heartbeat log, so the
  existing family bounds it and **no new family was needed**. The policy
  SHA-256 is **unchanged at `b13fbc32…71b5`** — the only edit to
  `retention.py` was a comment, which sits outside `POLICY`.
- **The companion starts and stops the sampler by itself.** No harness
  started it in either session; after teardown no sampler process remains.

## The empty-series correction

The first build produced a `thermal` block whose series was **empty**, and
both of those sessions are kept as `V1_preseries` / `V2_preseries` because
they are the evidence for the device finding.

The cause: the specified fallback is hottest zone, else headroom, and this
device has **neither**. Nothing continuous was left to record. The chain
was extended one step to `thermal_status` — the only signal the onn does
report — and the sessions re-run. The alternative was shipping an empty
artifact or inventing a number, and neither is a measurement.

## Method

Two 10-minute attract-mode sessions of the PS1 reference title, zero input,
opened through RESUME PLAYING per `TOOLS.md`, BACK to end, game stopped and
banner checked between, ~90 s idle between runs. Sessions
2026-09-21T14:02Z and 14:14Z (the pre-correction pair at 13:37Z and
13:49Z). Client `1bc95f0ab2526ece25610bcc1f1c1500926ab0c34c3cd42fa4f4872616d212f0`;
companion restarted with 8765 checked free.

Teardown per `TOOLS.md`: game stopped, banner confirmed clear, companion
stopped last, sampler process gone with it, no process in state `T`, no
listener on 8765 / 48100-48102 / 48110.

## No thresholds

**Nothing acts on any reading, and no threshold is set** — that is the
user's decision now that numbers exist. A thermal pause on the recovery
state machine is recorded, not built, in
`investigations/DEFERRED.md` ("Thermal pause on the link-drop recovery
state machine") with its reopen condition: a recorded session showing
`thermal_status` at or above SEVERE (3), or headroom at or above 1.0, or a
zone maximum that would justify one. **On this device none of those can be
reached today**, since two of the three signals do not exist and the third
never left NONE.

## Artifacts

Under `evidence/d_base_t1_2026-09-21/`, with `t1_sha256.txt` (26 files):
both sessions' decoder reports, `host_resource_samples.jsonl` (20 lines
each), `heartbeat_lines.jsonl` (300 each), `recovery_lines.jsonl`,
`status_end.json`; the pre-correction pair under `V1_preseries` /
`V2_preseries`; `retention_plan.txt`; and copies of
`host_resource_sampler.py`, `host_resource_sampling.py` and the session
harness `t1_session.sh`.

## Privacy

No network addresses, MACs, SSIDs, ADB endpoints or device identifiers
appear here or in the artifacts. The only dotted-quad matches in the
copied files are the RetroArch core version string `0.9.44.1`.
