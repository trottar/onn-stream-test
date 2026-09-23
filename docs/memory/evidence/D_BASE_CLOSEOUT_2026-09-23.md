---
memory_schema: 1
as_of: 2026-09-23
status: D-BASE CLOSE-OUT — BASELINE MET (pre-registered): every numeric-target row passes in both a cold and a warm 20-minute session on the build as adopted; max output gap 163 / 110 ms, the transport's open row, inside the 250 ms verdict bound; the client decision is NOT triggered; D-BASE CLOSED, Phase C RESUMES
---

# D-BASE close-out — the baseline, scored as it stands

Task: `handoffs/D-BASE-CLOSE_TASK.md` (authorized by the user 2026-09-23).
Evidence: `d_base_closeout_2026-09-23/`, SHA-256 of every file in
`d_base_closeout_2026-09-23/closeout_sha256.txt`. **No code change, no
profile change.**

## The build scored

`native_game_720p60_reference` as adopted, every field `source: profile`,
nothing in the environment (`PRIVYHUB_*` 0 in the companion's environ and
the user manager's), `any_override: false`:

- frame cap **90,000 B** (`P6a`), cushion **12 / 17** (`P9`/`P9a`, `T2`),
  audio redundancy **2 / 4** (`P10`);
- host headless behind the DisplayPort dummy plug (`H2`), companion as
  the systemd user unit (`H3`), host wired to the Opal, onn on its 5 GHz
  (`B2`); APK `f31b1c18…8ae7`.

## The sessions

| session | condition | PLAYING (UTC) | onn cpu mean / max | onn thermal status |
| --- | --- | --- | --- | --- |
| **C** | cold: 41 min after the last `session_ended` (the user's listen, 21:49:25) | 22:31:20 | 67.6 / 69.5 °C | 0 |
| **W** | 1 min after C (warm throughout) | 22:52:31 | 68.0 / 69.2 °C | 0 |

20-minute attract-mode holds of the PS1 reference title, zero input,
RESUME PLAYING, BACK to end, `p9_run.sh` copied byte-for-byte, `T2`'s
thermal sampler at 10 s, sampler off, heartbeat default, **0 foreign adb**
in either hold. Scored by `closeout_score.py` (verdict fixed in its
docstring before the data) → `closeout_score.txt`, `closeout_summary.json`.

## The table, raw first

Each row from its source counter as `investigations/BASELINE_STREAM_HEALTH.md`
defines it (rendered fps = `rendered_frames / duration`, not `recent_fps`).

| row | target | corpus (Group A, 127) | 2026-09-20 "now" | **C (cold)** | **W (warm)** | pair |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| spikes ≥ 20 ms / min | < 200 | 2,535 | 15-245 | **32.8** | **26.0** | 29.5 |
| rendered fps | ≥ 59.5 | 55.5 | 59.65 | **59.90** | **59.91** | 59.91 |
| received-AU fps | — | 59.2 | 59.8 | 59.92 | 59.92 | 59.92 |
| max output gap (ms) | ≤ 100 | 287 | 123-463 | **163** | **110** | 163 |
| stale output drops / min | < 20 | 193 | 9.3 | **1.14** | **0.80** | 0.97 |
| lost packets / min — **video, post-FEC** | < 10 | 197 (2-3x under) | 109-144; 5-20 capped | **8.67** | **8.40** | 8.53 |
| lost packets / min — audio, after de-duplication | — | — | — | 0.25 | 1.44 | 0.84 |
| audio underruns — per session (per min) | < 5 / min (note) | 207 | 13-20 | **17 (0.84)** | **14 (0.70)** | 31 (0.77) |
| `prolonged_starvation_events` / min | — | — | — (32-42 at 3/8, `P7`-`P9a`) | 0.35 | 0.05 | — |
| frames under 20 ms rx → output | — | 28.4 % | 98.4 % | 99.12 % | 99.30 % | 99.21 % |
| client fps deficit (received − rendered) | — | 3.5 | 0.08-0.28 | 0.02 | 0.01 | 0.02 |

Beside them: video `fec_recovered` 14.7 / 16.2 per min; audio recovered
by its copy 590 / 1,081; `avg_queue_residence_ms` 67.9 / 62.4.

## Caveats, one paragraph each

**Max output gap is the transport's, and no `D-BASE` item moved it below
~100 ms.** Measured on the capped build: this close-out 163 / 110 ms;
`P10` 105-168; `P9a` 157-329; `H2` 93-184; pre-cap `S1` 279-722. It
follows single transport events (a burst of loss or a late IDR), not the
decode path. It is recorded as **the one open row**, with its value — not
as a failure of the client or the encoder.

**The video loss row is post-FEC.** `lost_packets` counts what the 8+1
XOR could not recover; 14.7-16.2 packets/min were recovered here. 8.4-8.7
passes the < 10 target, **close to it**; at the warm state the path drops
more and FEC hides most of it (`T3` correction).

**The warm-state loss is covered, not cured.** From ~7 minutes into a
cold stream the path starts dropping single packets between the host's
NIC and the onn's IP stack (`T2`, `T3`); audio redundancy recovers them
(590 / 1,081 here, audio loss 0.25 / 1.44 per min) at +1.6 Mbps. The cause
between the ends is open for `host_link`.

**The synthetic UDP pathology stays PAUSED** (`M1`): reproduced from a
Linux sender, never on the post-`B2` topology; separate from in-session
loss.

**The onn's thermal status never left 0** — here (max 69.5 °C against
HAL thresholds of 95 / 125 °C) or in any session since `T1`.

## Verdict — BASELINE MET

Every numeric-target row other than max output gap passes in **both**
sessions (spikes, rendered fps, stale drops, video loss, audio
underruns), and max output gap is **≤ 250 ms in both** (163, 110).

- **`D-BASE` CLOSED.**
- **Phase C RESUMES.** **C1 is done**: the reference profile
  (`companion/native_stream_profiles.py`) declares every stream parameter
  explicitly, now including `max_frame_size_bytes`,
  `audio_queue_target_packets` / `audio_queue_capacity_packets` and
  `audio_redundancy_copies` / `audio_redundancy_offset_packets`, validated,
  reported with their source in `native-stream-status` —
  `C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA` is effectively complete.
  **The next technical item is where Phase C was suspended: `C3.L3a`
  Part 2** (gameplay acceptance of the Linux actuator; fix the probe's
  three recorded defects before any rerun), then `C3.L4` (the automatic
  controller), per the roadmap's Linux order C3 → C4 → C5 → C6 → C7.

**The client decision (`D-BASE` Step 5) is NOT triggered**: on the
production link, a healthy decode path reaches spikes 32.8 / 26.0 per min
(< 200) and 59.90 / 59.91 fps (≥ 59.5). The onn is not the ceiling.

## State at the end

Companion under systemd (MainPID owns 8765), the profile as adopted, 0
`PRIVYHUB_*`, `any_override: false`, game inactive, banner cleared,
thermal sampler stopped, no live `.state.recovery`. Nothing on the Opal
touched.

## Privacy

Private addresses in the companion journals / reports / status replaced
with `<IP_REDACTED>`; no MAC; `h2_prep_redact.py --check` passes on the
thermal jsonl.
