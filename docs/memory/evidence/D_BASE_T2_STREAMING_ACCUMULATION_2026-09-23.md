---
memory_schema: 1
as_of: 2026-09-23
status: D-BASE-T2 — Part 0 12/17 ADOPTED; Part 1 REPRODUCED and RESETS WITH IDLE, pre-registered reading MIXED (host NVMe temps and the Opal SoC temp reach |rho| 0.6, and every temperature resets in the idle); exploratory: audio loss steps up ~7 min into a cold stream at a slow thermal state and does not touch video loss; cause not located; thresholds proposed, none enforced
---

# D-BASE-T2 — what builds up while streaming

Task: `handoffs/D-BASE-T2_TASK.md` (authorized by the user 2026-09-23).
Evidence: `d_base_t2_2026-09-23/`, SHA-256 of every file in
`d_base_t2_2026-09-23/t2_sha256.txt`.

## Part 0 — 12 / 17 adopted

`native_game_720p60_reference` → 12 / 17 in
`companion/native_stream_profiles.py`; the user manager's
`PRIVYHUB_AUDIO_QUEUE_*` (left set by the user's listen) unset; restarted
through systemd: `audio_cushion` 12 / 17 source `profile`, 0 `PRIVYHUB_*`
in the MainPID's environ, `any_override: false`. **No client build — the
default is the companion's.** The user's listen, verbatim, user-stated,
not a gate: *"No issues from playing for a minute or two."* Decision
`decisions/D-BASE-P9_AUDIO_CUSHION.md`; patch
`patches/D-BASE-T2_P0_AUDIO_CUSHION_ADOPTED.md`. All four sessions below
ran on it.

## Part 1 — the run

| # | session | PLAYING (UTC) | before it |
| --- | --- | --- | --- |
| 1 | S-a | 15:46:01 | **42 min** since the last `session_ended` (the user's listen, 15:03:54, recovery log) |
| 2 | S-b | 16:07:12 | 1 min after S-a |
| 3 | idle | 16:27:43-16:57:43 | companion up, nothing streaming |
| 4 | S-c | 16:58:26 | the idle |
| 5 | S-d | 17:19:39 | 1 min after S-c |

20-minute attract-mode holds of the PS1 reference title, zero input,
adopted profile (`-max_frame_size 90000`, `any_override: false`), 12/17
from the profile, `p9_run.sh` copied byte-for-byte (companion restarted
through systemd per session, as in `P9a` — a restart is therefore **not**
a reset), `t2_all.sh` the timeline.

**The sampler** (`t2_sample.py`, kept as a tool) wrote **883 rows at
10 s** across all of it, 15:15-17:42 UTC: host hwmon temperatures by
label, per-core cpufreq, encoder and RetroArch CPU %, `eno1` counters;
onn in one `adb shell` — `dumpsys thermalservice`, `dumpsys battery`,
`cmd wifi status`; Opal in one read-only `ssh opal` — the onn's `wlan1`
station row, `iwinfo assoclist`, load, SoC temperature. One round cost
~0.9 s. **The only adb processes the hold monitor saw (36-39 per hold)
were the sampler's own** — the diagnostic cost `P8` cleared (-1 %).
Nothing written to the Opal.

**New readable signals.** The onn's thermal HAL answers `dumpsys
thermalservice` with a **live `cpu-thermal` temperature** (`T1` found the
status code only): 62-70 °C streaming, ~59 °C idle; its HAL thresholds
are 95 °C (severe) and 125 °C (shutdown) — **status stayed 0 throughout,
max 69.6 °C.** `/sys/class/thermal` on the onn is still `Permission
denied`; `dumpsys battery` reports a fixed 31.0 °C (no battery). The
Opal's SoC temperature (`thermal_zone0`) reads 58-63.5 °C. Its `tx
failed` copies `tx retries` (O1's trap, seen again) — rate/MCS used.

**`S3`'s three hours cannot answer the trend question**: they ran before
the heartbeat carried audio fields; the report's total is 8,543 audio
packets lost in 180 min, **47.4/min — a warm plateau's level**.

## Raw numbers first — audio loss per minute (heartbeat, 19 full minutes)

- **S-a** (578): **4 3 6 3 3 1 3** 23 12 30 31 52 28 70 77 31 88 78 35
- **S-b** (812): 42 53 43 28 37 48 47 37 60 35 24 43 26 40 40 61 85 24 39
- **S-c** (672): **1 6 5 1 3 5** 34 22 31 56 63 46 67 69 70 33 69 54 37
- **S-d** (1,381): 84 50 71 129 106 47 90 82 50 57 102 91 29 74 75 72 34 73 65

Openings (minutes 1-3) **4.3 / 46.0 / 4.0 / 68.3**; endings (last 3)
67.0 / 49.3 / 53.3 / 57.3. Video loss per session 154 / 258 / 165 / 104,
flat per minute (0-53); **video vs audio loss per minute rho −0.116**.

**`P9a`'s trend reproduced, and the idle resets it**: S-c opened at 4.0
after 30 min idle, as S-a did after 42. From cold, loss sits at 1-6/min
for **6-7 minutes and then steps up** (S-a at minute 8, 15:53; S-c at
minute 7, 17:04) to a warm level of ~30-90/min.

Timeline at the two steps (minute means; `t2_analysis.txt` has every
minute of the run, idle included):

| UTC | host Tctl °C | host NVMe S2 °C | onn cpu °C | Opal SoC °C | audio/min |
| --- | ---: | ---: | ---: | ---: | ---: |
| 15:52 (S-a m7) | 52.3 | 39.0 | 66.6 | 61.0 | 3 |
| 15:53 (S-a m8) | 52.3 | 39.4 | 67.0 | 61.0 | **23** |
| 16:06 (gap) | 47.6 | 40.9 | 64.6 | 60.3 | — |
| 16:07 (S-b m1) | 48.3 | 41.7 | 67.2 | 61.2 | **42** |
| 17:03 (S-c m6) | 51.6 | 39.5 | 66.0 | 61.0 | 5 |
| 17:04 (S-c m7) | 52.7 | 39.7 | 66.5 | 61.0 | **34** |

(Wall-clock minute means; the separation below uses the heartbeat
minutes, whose windows are offset by up to a minute — hence NVMe S2 sits
just under its 39.85 °C cut at the wall-clock step minutes.)

## Correlations (Spearman, audio loss/min vs signal, n = 76 session minutes)

| signal | rho |
| --- | ---: |
| **Opal SoC temperature** | **+0.644** |
| **host NVMe Sensor 2** | **+0.628** |
| **host NVMe Composite / Sensor 1** | **+0.607** |
| host encoder CPU % | −0.592 |
| streaming minutes since run start (context) | +0.526 |
| Opal signal avg (onn row) | −0.479 |
| onn cpu-thermal | +0.437 |
| onn RSSI / link speed | −0.433 / −0.427 |
| host Tctl / hottest | +0.423 |
| Opal tx bitrate / tx MCS | −0.295 / +0.043 |
| host CPU MHz min / mean | −0.107 / −0.014 |

**Idle recovery** (S-a opening → S-b ending → idle end → S-c opening):
**every temperature reset** — host Tctl 43.6 → 54.9 → 28.1 → 44.7, NVMe
Composite 34.9 → 38.9 → 35.1 → 35.9, amdgpu 34.6 → 44.3 → 26.8 → 35.5,
**onn cpu 63.5 → 68.7 → 58.9 → 63.3**, Opal SoC 60.1 → 62.3 → 59.0 →
60.6; **every radio signal was flat** — onn RSSI −66 throughout, link
260 Mbps, Opal signal avg −78, tx MCS 2.1-2.6, retry ratio 0.08-0.13,
Opal load 1.1-1.2; `eno1` drops/errors 0. Audio loss 4.3 → 49.3 → 4.0.

## The pre-registered reading — MIXED

- **Not reproduced**: no — S-b opened at 46.0, not within 20 % of S-a's 4.3.
- **Host thermal / clock**: host NVMe temperatures reach |rho| 0.6 and
  reset — **but so did the Opal's SoC temperature**, also implicated and
  also reset; the rule needs the host signal to be the one that reset
  while the others did not. CPU clock: rho −0.11, flat.
- **Onn-side**: thermal status never changed; RSSI / link speed flat and
  |rho| 0.43. Not met.
- **AP-side**: the Opal's rate/MCS did not fall (MCS rho +0.04); not met.
- **Time only**: no — the idle **did** reset the loss.

**MIXED.** All the temperatures rise together while streaming and fall
together at idle, so correlation cannot separate them; the radio does
not move at all.

## Exploratory, after the reading (labelled; not pre-registered)

`t2_separation.py` → `t2_separation.txt`: for each signal, the best
single threshold between LOW minutes (< 10/min, n = 13) and HIGH minutes
(≥ 30/min, n = 54):

| signal | LOW range | HIGH range | misclassified |
| --- | --- | --- | ---: |
| host NVMe Sensor 2 | 37.5-39.5 °C | 39.9-42.7 °C | **0 %** |
| host NVMe Composite | 34.9-36.9 | 36.9-38.9 | 1.5 % |
| **onn cpu-thermal** | 62.4-66.6 | 66.5-69.1 | **1.5 %** |
| host Tctl | 39.5-52.3 | 49.8-55.7 | 3.0 % |
| Opal SoC | 59.8-61.0 | 61.0-63.5 | 3.0 % |
| onn link speed, Opal load, CPU MHz | overlap | overlap | 18 % |

Three things the data does say:

1. **It is a step at a warm state, not a ramp with time.** Both cold
   sessions stepped at the same readings (onn 66.5-67.0 °C, Opal 61 °C,
   host Tctl ~52-53 °C) after 6-7 minutes.
2. **The fast host CPU temperature is not it.** After the 1-minute gap
   before S-b, host Tctl had dropped to 47.6-48.3 °C — inside its LOW
   range — and loss opened at 42/min; the **slow** signals (NVMe, onn
   SoC, Opal SoC) stayed above their cuts. What drives it cools slowly.
3. **It is audio-specific.** Video loss per minute does not follow
   (rho −0.12; video 104-258 per session with no step), and the air does
   not move (RSSI, MCS, retries flat). A path-wide cause would take video
   with it. That points at an **audio-path component that is
   temperature-sensitive** — the host's audio capture/sender or the
   onn's audio receive — not the radio.

**Not located.** The next probe, named and **not run**: repeat one cold
session with `P5`'s onn socket sampler (`p5_socket_sample.py`, the
per-socket `drops` column of `/proc/net/udp`) on the **audio** port,
plus the companion's audio-sender packet count if exposed: drops on the
onn's audio socket rising at the step = the onn's receive path; no
drops and a sequence gap already at send = the host sender; neither = the
air after all. A second, if needed: warm only one end (a local video on
the onn for 30 min with the host idle, or the reverse) and start a cold
session on the other.

## Thresholds — proposals only (the user decides)

Signal value at the first minute audio loss/min reached **30 (warn)** and
**100 (act)**:

| signal | warn | act |
| --- | ---: | ---: |
| onn cpu-thermal (exploratory; the one on the device) | 67.6 °C | 67.8 °C |
| host NVMe Composite (implicated) | 36.9 °C | 38.9 °C |
| host NVMe Sensor 2 (implicated) | 40.0 °C | 42.4 °C |
| Opal SoC (implicated) | 61.0 °C | 62.3 °C |
| host Tctl (context) | 53.9 °C | 54.7 °C |

These are a **step's location**, not a slope: warn and act sit within
0.2-2 °C of each other. "Act" would be **a `native-stream-status` flag
first** (e.g. `audio_loss_warm_state`) — nothing automatic (`C3.L2`:
Linux is `video_only_restart`, not authorized to adapt during play). The
onn's own HAL thresholds (95 / 125 °C) are far above anything seen and
are not the trigger. **None is enforced.**

## State at the end

Companion under systemd, MainPID owns 8765, **12 / 17 from the profile,
0 `PRIVYHUB_*`** in its environ or the manager's, `any_override: false`,
game inactive, launcher banner cleared. **No recovery file created.**
Nothing on the Opal changed.

*Correction (Cowork verification, 2026-09-23):* the sentence above
originally went on to say the recovery file "on disk is `R3b`'s Tekken 3
file of 2026-09-22, kept on purpose". That is out of date: `R3c` removed
it through `recovery-discard`, `R3c2` deleted each restored copy, and
`E30`'s save was discarded by the user. The states directory holds no
`.state.recovery` at all; `Tekken 3 (USA).state` there is the slot-0
scratch `R3c2` restored. The only copy of the N150 save is
`d_base_r3c_2026-09-22/recovery_copy/`. Also minor: the per-session video
loss figures in this record (154 / 258 / 165 / 104) are 19-minute
heartbeat sums; the reports' session totals are 158 / 270 / 276 / 111 —
the flatness reading is unaffected.

## Privacy

The onn's hardware address was held in the sampler's memory only (to
find its Opal row) and never written; the jsonl carries numbers and fixed
labels. Private addresses in the companion journals / reports / status
files replaced with `<IP_REDACTED>`. `h2_prep_redact.py --check` passes
on the jsonl and the analysis; on the session files it flags only
`127.0.0.1`, `0.0.0.0` and a version string `0.9.44.1` — no private
address, MAC, SSID or BSSID anywhere.
