---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 41bbc6acd3534f79283e328596115a02c3acc296
phase: C
scope: phase_c_linux_streaming_continuation
---

# Phase C continuation context

Read this file alone to resume Phase C. It is self-sufficient: it carries the
state, the constraints, the measurements and the open question. Do not re-read
the whole memory hierarchy to start work.

Pull a specific record only when the task needs its detail. Pointers are at the
bottom.

**Maintenance rule:** update this file whenever the phase or sub-phase advances.
When Phase C closes, create `PHASE_D_CONTEXT.md` (or the next phase) the same
way and leave this one as history.

---

## 1. Where the project is

Local repo `/home/privyhub/Projects/onn-stream-test` is authoritative. GitHub is
history unless stated otherwise. Platform is Linux; the Windows prototype is
outgoing.

Complete and runtime validated, **do not reopen without new evidence**:
Phase A, Phase B, D1-D5 (including D4 Games and D5 media/server restoration),
C1 Linux profile/backend, C2 stream telemetry.

Phase C is active. Sub-phase state:

| Item | State |
| --- | --- |
| `C3.L0` actuator boundary audit | COMPLETE |
| `C3.L1` Linux encoder-only seam and probe | COMPLETE / RUNTIME VALIDATED |
| `C3.L1R1` RTP baseline correction | COMPLETE / RUNTIME VALIDATED |
| `C3.L2` Linux actuator classification | COMPLETE |
| `C3.L2a` first-IDR acceptance investigation | **ANSWERED**; IDR wait falsified |
| `C3.L2b` decoder-report cycle retention | COMPLETE / RUNTIME VALIDATED |
| `C3.L2c` low-latency decode candidate | **FALSIFIED / ROLLED BACK**; see section 6 |
| `C3.L3` Linux fixed-bitrate envelope characterization | **COMPLETE / RUNTIME VALIDATED**; see section 6a |
| `C3.L3a` gameplay acceptance probe | **REGISTERED / NEXT**; the `C3.L4` gate, see section 6b |
| `C3.L4` fast-down/slow-up controller | BLOCKED; gate is `C3.L3a` |
| C4 adaptive FEC | DEFERRED |

Phase E does not begin until the streaming architecture is stable. It measures a
finalized architecture, not a partial one.

---

## 2. The validated stream

Path: managed RetroArch X11 window → x11grab → h264_vaapi → RTP/UDP → 8+1 XOR
FEC → Android hardware AVC.

Profile `native_game_720p60_reference`: 1280x720, 60 fps, 7000 kbps target and
max, GOP 15, B-frames 0, FEC group 8, RTP payload type 96, 1200-byte packets.

Linux is **single-process video**: x11grab is an FFmpeg input format, so
`_capture_process is None` and `_running_locked()` asserts it. Windows used a
separate WGC bridge feeding FFmpeg over an inherited pipe. This is why Windows
timing does not transfer.

C2 Linux baseline: ~5.94 Mbps, ~59.45 fps, 0.337 ms jitter, 0 loss, 0 FEC
recovery, 91 ms control RTT, 31 ms receive-to-decode, queue depth 0.
Delivered bitrate varies with scene content (5.1-7.4 Mbps observed); the 7000
target is a ceiling, not a floor.

---

## 3. Actuator boundary (from `C3.L0`)

| Parameter | Runtime mutable? | Restart required? | Safe? |
| --- | --- | --- | --- |
| bitrate | No | Encoder-process restart | Measured; see section 4 |
| resolution | No | Restart **plus APK change** | No; C3 non-goal |
| FPS | No | Restart **plus APK change** | No; C3 non-goal |
| FEC group size | Structurally yes | No | Unvalidated; **C4 owns it** |
| pacing | No actuator exists | N/A | Out of C3 scope |

Key facts:

- **`live_bitrate_reconfigure` is foreclosed** by the current architecture. The
  encoder is an external FFmpeg CLI launched with `-nostdin` and
  `stdin=DEVNULL`, bitrate baked into argv at `Popen` time. No control socket,
  no in-process handle. Reaching it needs an in-process encoder or a
  controllable encoder host — an architecture change, not a patch. This is a
  statement about the architecture, not about VAAPI hardware.
- Resolution and FPS are **client-pinned, not negotiated**.
  `NativeStreamActivity` holds `VIDEO_WIDTH`/`VIDEO_HEIGHT`/`VIDEO_FPS` as
  compile-time constants; `AvcLowLatencyDecoder` configures MediaCodec once,
  never reads the in-band SPS, and ignores `INFO_OUTPUT_FORMAT_CHANGED`. Host
  and client can silently diverge.
- GOP is expressed in frames, so changing FPS silently rescales the keyframe
  interval in seconds.
- FEC group size is the only in-place seam: the FEC header carries the real
  group length and the receiver validates 1-8. No setter exists.
- `_start_linux_locked` calls `_stop_locked()`, which stops FEC and session I/O.
  It is **not** an actuator.

---

## 4. `C3.L1` / `C3.L1R1` runtime result

The Linux encoder-only cycle works and preserves everything it must.

**Lifecycle preservation: PASSED.** Across both runs: FEC relay, process audio,
persistent controller and emulator all continued; zero FEC send errors, zero
audio write errors, zero controller send errors; exactly one SSRC change per
cycle; receiver not waiting for IDR at session end.

| Measure | Run 1 (`C3.L1`) | Run 2 (`C3.L1R1`) |
| --- | ---: | ---: |
| encoder spawn | 215.007 ms | 115.145 ms |
| first RTP resume | 215.017 ms *(defective)* | **267.069 ms** |
| video silence after spawn | not measurable | **~152 ms** |
| decoder max output gap | 318 ms | **287 ms** |
| max resync to IDR | 241 ms | 191 ms |
| packets dropped waiting for IDR | 118 | 123 |
| decoder dropped / overflow | 19 / 19 | 27 / 27 |

Run 1's resume figure was defective: the RTP baseline was taken before the old
encoder was killed, so old-encoder packets satisfied the first poll. Fixed in
`C3.L1R1`; run 2 is trustworthy.

**Authoritative comparison** — `decoder_max_output_gap_ms`, measured on the
receiver independently of the host probe:

- Windows D-062 same-bitrate cycle: 791 ms
- Windows D-070 bidirectional cycle: 1,059 ms
- **Linux same-bitrate cycle: 287-318 ms**

Linux is ~2.5-2.75x better than the directly comparable Windows run. The
`C3.L0` pre-registered boundary ("materially below 0.84-0.95 s reopens
classification") is **met**.

**Reading the interruption, with `C3.L2`'s qualifications:**

- `max_resync_to_idr_ms` and `packets_dropped_waiting_for_idr` are **whole-session
  values**. Each session recorded two sequence resyncs and one SSRC change, so
  attributing the session maximum to the cycle is an inference, not a
  measurement. `C3.L2b` gives future sessions per-event values instead of a
  session maximum; the whole-session figures above stand as the historical
  `C3.L1R1` record.
- The terms do not sum. Spawn 115 ms, RTP silence ~152 ms and decoder gap 287 ms
  overlap in time; 152 + 191 exceeds 287.
- `decoder_max_output_gap_ms` is the figure to cite. It is measured on the
  receiver, which has no stake in the host probe's result.

Process spawn (115-215 ms) is not the dominant term. Waiting for a usable IDR
still is, on the evidence available.

**Focused gameplay observation (2026-09-18, user):** "pretty good... occasional
stutter that happens, but definitely playable... still obvious that it is a
streamed game which I would like to minimize as much as possible."

The occasional stutter is the pre-existing baseline behavior, not attributed to
the actuator cycle.

---

## 5. The classification — settled by `C3.L2`

Linux is classified **`video_only_restart`**. Full record:
`decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`.

- `live_bitrate_reconfigure`: not available under the current architecture.
- `video_only_restart`: runtime validated, lifecycle preserved twice, 287-318 ms
  decoder output gap.
- `unsupported`: does not apply.

**Authorized:** session start and start-time profile selection before `READY`;
manual and loopback-only diagnostic changes; fallback and recovery, including
replacing a dead encoder; `C3.L3` characterization cycles.

**Not authorized:** automatic adaptation during `PLAYING`. `C3.L4` stays
BLOCKED.

The reasoning, in one line each: the gap is ~17 frame intervals against a
settled stream whose post-cycle gap was 5 ms; an automatic controller fires
under pressure, when a deliberate discontinuity hurts most; one accepted manual
cycle is not evidence for repeated automatic ones; and the standing preference
is to minimize perceptible artifacts while an untested lead to reduce the cost
exists.

---

## 6. `C3.L2a` — answered

**The actuator's first IDR is accepted in 27 ms.** Record:
`evidence/C3_L2A_E2_ACTUATOR_IDR_RESOLVED_2026-09-18.md`.

One encoder-only cycle against the `C3.L2b` client, session 63,719 ms:

| `elapsed_ms` | discontinuity | first IDR at | `resync_to_idr_ms` | AU complete | FEC repaired |
| ---: | --- | ---: | ---: | --- | --- |
| 22,852 | sequence resync | 23,047 | 195 | true | false |
| **43,443** | **ssrc change — the cycle** | **43,471** | **27** | **true** | **false** |
| 48,545 | sequence resync | 48,756 | 210 | true | false |

The replacement encoder's keyframe is the fastest of the three by a factor of
seven, and it arrived intact. Two explanations are now dead by measurement: the
IDR wait, and the damaged-first-keyframe candidate.

**The session's real gaps are decoder time, and they follow the resyncs, not the
cycle.** 359 ms at 23,103 against `codec_ms` 367; 352 ms at 48,808 against
`codec_ms` 361 — both with `feed_delay_ms` 0. Nothing registered at or near
43,443. `max_codec_ms` 367, `low_latency_enabled` **false** on
`c2.realtek.video.avc.decoder`.

So the 287-318 ms from `C3.L1` / `C3.L1R1` was never actuator cost. Do not cite
it as such.

**What this does not settle.** `C3.L2`'s refusal to authorize automatic in-game
adaptation stands. This is one cycle in one session. It removes the mechanism
that was assumed to make the actuator expensive; acceptance still needs
repetition and a focused gameplay observation. Note also that this session saw
530 lost packets and 38 sequence-gap AU drops against zero unrecoverable FEC
groups — transport conditions differed from `C3.L1R1`, so the two sessions are
not like-for-like.

**Open defect, not blocking:** `slow_events_marked` is emitted as an empty array
while `slow_event_retained_marked` reports 30 of 64. The marked rows are counted
and dropped. `stream_discontinuities` and `first_idr_after_discontinuity` carried
this result without them.

**`C3.L2c`**, enabling MediaCodec low-latency decode, was authorized
2026-09-18, installed, and runtime tested 2026-09-19. The capability gate
removal worked as designed: `low_latency_enabled` flipped to true and
`max_codec_ms` fell to 107 ms — the best of the eight sessions recorded on
this device that day, whose ordinary range was 140-433 ms — with
`spike_50_ms` at 19 against 91-314 in those sessions and `spike_250_ms` at
zero, the only session of the eight with none. But `max_output_gap_ms` —
the worst perceptible stall — was **385 ms, second worst of the eight**,
and the user's own report ("gameplay was trash") matched it. **FALSIFIED.**

The durable lesson is larger than the candidate: in every ordinary session
`max_output_gap_ms` tracks `max_codec_ms` to within ~10 ms; here it exceeded
it by 278 ms. **`max_codec_ms` is not a valid proxy for
`max_output_gap_ms`.** Any future candidate justified by "it lowers decode
time" must measure the gap directly before acceptance.

Reverted to the capability-gated behavior; source restored to its exact
predecessor bytes (SHA-256
`22038e355f85bb8330d900bae64c37db54c902d4affdef12be4810bb03271c07`). Do not
retry the unconditional `KEY_LOW_LATENCY` request without new evidence.
Records: `evidence/C3_L2C_LOW_LATENCY_DECODE_FALSIFIED_2026-09-19.md`,
`patches/C3-L2C_LOW_LATENCY_DECODE_ENABLE.md`.

## 6a. `C3.L3` — Linux fixed-bitrate characterization, closed

The characterization cycle was Windows-only (WGC replacement capture) and
failed immediately on Linux. It was ported by reusing the validated
`C3.L1`/`C3.L1R1` encoder-only restart primitive —
`run_c3_linux_fixed_bitrate_cycle()` in
`companion/diagnostics/c3_linux_actuator_probe.py`, driving
`_build_linux_ffmpeg_command`'s pre-existing, previously unused
`bitrate_kbps`/`max_bitrate_kbps` overrides. The Windows implementation was
not touched.

Ten trigger/finalize cycles across three runs at 5000/5500/6000 kbps, zero
cycle-level FEC/audio/controller errors in every one.

`decoder_max_output_gap_ms`, three valid samples per bitrate:

| bitrate | samples | band |
| --- | --- | --- |
| 5000 kbps | 367 / 292 / 242 | 125 ms |
| 5500 kbps | 219 / 584 / 335 | 365 ms |
| 6000 kbps | 331 / 291 / 307 | **40 ms** |

**6000 kbps is the most consistent of the three** and never exceeded 331 ms.
5500 kbps produced both the best and the worst single result in the set; its
584 ms session traces to one 417 ms resync-to-IDR event.

Every figure is transport and decoder timing. **No perceptual quality was
measured, so no bitrate is accepted as a fallback level on this data.** The
focused gameplay observation is still owed and it is the `C3.L4` gate.

Record: `evidence/C3_L3_LINUX_FIXED_BITRATE_CHARACTERIZATION_2026-09-19.md`.

## 6b. The `C3.L4` gate, and `C3.L3a`

`C3.L4` is blocked on a gameplay acceptance observation. Until 2026-09-19 that
gate was named but never defined, and sessions repeatedly proposed the wrong
thing in good faith. It now has a definition; the authoritative statement is in
`decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`, section "The `C3.L4` gate,
stated so it can be satisfied".

**Two things do not satisfy it.**

- *A manual cycle or two with a subjective read.* Performed 2026-09-18,
  reported playable, and `C3.L2` reason 3 already ruled it insufficient: it is
  acceptance of a single **operator-initiated** transition, not of an
  unannounced policy-initiated one.
- *Transport or decoder timing, at any sample size.* `C3.L3` produced three
  valid samples per bitrate and measured no perceptual quantity at all.
  `C3.L2c` is the standing proof the two come apart — best `max_codec_ms` of
  eight same-day sessions, and the verdict on the build was "trash".

**What satisfies it:** a session with several transitions, fired at intervals
the player does not know in advance, including at least one interval where
nothing fires as a control, with the player's marks compared against
`stream_discontinuities` `elapsed_ms` **after** the session rather than during
it. `C3.L2b` exists to provide that anchoring.

**Separately unmeasured:** whether 5000 or 5500 kbps *looks* acceptable. A
fast-down controller whose destination is visually poor fails even if every
transition is invisible. The observation should park at the candidate bitrates
long enough to judge the picture.

`C3.L3a` owns this. Diagnostic-only, authorizes nothing, reuses
`run_c3_linux_fixed_bitrate_cycle` unchanged. Scope in
`investigations/ACTIVE.md`.

One standing consequence of the `C3.L2a` E2 result, easy to miss: the
classification's reason 1 — the actuator inserting a ~290 ms discontinuity —
is **falsified**. Reasons 2, 3 and 4 carry the block. Do not argue for or
against `C3.L4` from the size of a transition; argue from frequency, timing,
and the unmeasured perceptual question.

## 7. Rules that bind Phase C work

Do not change: resolution, frame rate, GOP, B-frames, FEC wire format, RTP
payload type, packet size, ports, process audio, controller transport, emulator
lifecycle, Android streaming constants, or any non-loopback control surface.

Do not reopen: D4 Games, D5 media/server, the Windows-era C3 record (D-063,
D-067, D-068, D-069, D-070, D-071), the deferred UDP burst/gap pathology, or
the `C3.L2b` code design itself (marked/recent segmentation, discontinuity and
IDR-context bounded lists) without a runtime finding that it is insufficient.

The Windows 5500/6000/7000 bitrate ladder is **evidence, not a Linux constant**.
`C3.L3` must revalidate it on Linux before any level is treated as portable.

Adaptation stays frozen during `STABILIZING` and `PAUSED`
(`LAUNCHING → STABILIZING → READY → PLAYING`, D-067/D-068).

Never ask the user for IP addresses; redact network identity in diagnostics.

---

## 8. Operational facts

- Companion: `python3 ./companion/privyhub_service.py`. **Restart it whenever
  companion Python changes** — D-068 durable rule; stale-process behavior is not
  evidence.
- Continuity probe, trigger phase takes **no flag**:
  `python3 tools/probe_c3_actuator_continuity.py`
  then after normal Back: `... --finalize`.
  A `--trigger` flag does not exist. Do not run it against the pre-`C3.L2b`
  APK; it must be the rebuilt client, or the retention defect the patch fixed
  is simply re-measured against old code.
- The runner extracts only `ffmpeg_spawn_ms`, `first_rtp_resume_ms` and
  `host_verified_ms` from the host payload. `C3.L1R1`'s new fields
  (`encoder_down_ms`, `rtp_silence_after_spawn_ms`,
  `rtp_baseline_residual_packets`) are returned by the host but not printed by
  the runner. Known limitation; not worth a patch on its own.
- Every patch: ZIP into repo root, predecessor hash verification, wrong-state
  rejection before modification, backups under `archive/patch_backups`, one
  coherent change, validation, exact rollback on failure,
  `durable_memory_updated: true`. States are `INSTALLED SUCCESSFULLY`,
  `FAILED BEFORE MODIFICATION`, `ROLLED BACK`.
- Installers must run `tools/check_memory_health.py` as a post-write gate.
  `CURRENT.md` requires seven exact headings, each once — see `MAINTENANCE.md`.
- Record failures alongside successes in the same work. See the negative-result
  policy in `MEMORY.md`.

## 9. Open debt, recorded and not blocking

- `_host_telemetry.start()` is never called on the Linux path; sender-side host
  resource telemetry is inactive on Linux. Phase E prerequisite.
- `_patches/` and `_probes/` are not covered by `.gitignore` (patterns are
  `privyhub_*`; directories are `PrivyHub_*`, which does not match on a
  case-sensitive filesystem). Both are untracked; confirm before committing.
- The Windows probe shares the `C3.L1` stale-baseline pattern. Its evidence
  never recorded `ffmpeg_spawn_ms`, so it cannot be checked retrospectively.
  Treat Windows "first RTP resume" figures as pipeline re-establishment time.
  Not fixed; Windows is outgoing.
- `tools/probe_c3_fixed_*_characterization.py --finalize` has matched the
  wrong decoder-session file once, when run back to back after another
  bitrate's finalize. Intermittent, not root-caused. Always check
  `payload.decoder_session_log` and `session_duration_ms` in the written JSON
  against the intended session before using a finalize result. Companion-side
  code is not implicated. See `docs/KNOWN_ISSUES.md`.
- `C3.L2b`'s 2000 ms cycle-window default and its choice not to correlate
  `trimFecGroups`'s rare capacity-eviction path into `auFecUnrecoverableGroup`
  are judgment calls, not runtime-validated figures. See "Negative results and
  scope decisions" in `patches/C3-L2B_DECODER_REPORT_CYCLE_RETENTION.md`.

## 10. Pointers, for detail only

- `decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md` — the classification, its
  reasoning, and the pre-registered `C3.L2a` boundary.
- `investigations/C3_LINUX_ACTUATOR_BOUNDARY.md` — full boundary map and
  `C3.L0`-`C3.L2` history.
- `evidence/C3_L1_LINUX_ACTUATOR_RUNTIME_2026-09-18.md` and
  `evidence/C3_L1R1_LINUX_ACTUATOR_RUNTIME_2026-09-18.md` — raw runs.
- `evidence/C3_L2A_E1_DECODER_EVIDENCE_PASS_2026-09-18.md` — E1 pass, the
  retention defect, and the decoder-spike baseline the actuator is measured
  against.
- `patches/C3-L2B_DECODER_REPORT_CYCLE_RETENTION.md` — the retention patch
  installed this session; what changed and what is still not runtime-verified.
- `patches/C3-L2C_LOW_LATENCY_DECODE_ENABLE.md` — the `C3.L2c` install: the
  `KEY_LOW_LATENCY` capability-gate removal and why.
- `evidence/C3_L2C_LOW_LATENCY_DECODE_FALSIFIED_2026-09-19.md` — the
  falsification, measured against seven same-day baseline sessions.
- `evidence/C3_L3_LINUX_FIXED_BITRATE_CHARACTERIZATION_2026-09-19.md` — all
  three `C3.L3` runs and the corrected three-run reading.
- `patches/C3-L3_LINUX_FIXED_BITRATE_PORT.md` — the Linux port of the cycle.
- `patches/C3-L3R1_CHARACTERIZATION_CORRECTION.md` — the memory correction
  that added the omitted 6000 kbps rerun.
- `evidence/C1_C2_LINUX_REVALIDATION_2026-09-18.md` — Linux baseline.
- `architecture/ADAPTIVE_BITRATE.md` — adaptation architecture and Windows-era
  history.
- `architecture/STREAM_TELEMETRY.md` — the C2 measurement contract C3 consumes.
- `CURRENT.md` — active bootstrap. `roadmap/STATUS.md` — roadmap position.
- `docs/KNOWN_ISSUES.md` — open gaps. `LEARNINGS.md` — durable lessons.
