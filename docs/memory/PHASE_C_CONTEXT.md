---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 094b638a575d0f1acd141193d52a136af39248a2
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
| `C3.L2` Linux actuator classification | **NEXT** |
| `C3.L3` Linux fixed-bitrate envelope revalidation | PENDING, conditional on `C3.L2` |
| `C3.L4` fast-down/slow-up controller | BLOCKED |
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

**Where the gap comes from:** `max_resync_to_idr_ms` 191-241 ms with 118-123
packets dropped waiting for IDR, against 0 on both Windows runs. GOP 15 at
60 fps is a 250 ms keyframe interval, so the wait is roughly one full GOP. The
interruption is dominated by waiting for the replacement encoder's first usable
IDR, not by process spawn (115-215 ms).

**Focused gameplay observation (2026-09-18, user):** "pretty good... occasional
stutter that happens, but definitely playable... still obvious that it is a
streamed game which I would like to minimize as much as possible."

The occasional stutter is the pre-existing baseline behavior, not attributed to
the actuator cycle.

---

## 5. The open question — `C3.L2`

Classify the Linux actuator: `live_bitrate_reconfigure`, `video_only_restart`,
or `unsupported`, and decide whether `video_only_restart` is acceptable for
**automatic mid-game adaptation** on Linux.

What is settled: the mechanism works, preserves lifecycle, and costs ~287-318 ms
of decoder output gap. Windows rejected its ~1 s equivalent (D-070).

What is not settled: whether ~290 ms — roughly 17 frame intervals at 60 fps — is
acceptable to trigger automatically during play. The user's standing preference
is to **minimize** perceptible streaming artifacts, which argues for caution.

The strongest identified lead, **not yet authorized or investigated**: the gap is
mostly IDR wait, so requesting an immediate IDR on the replacement encoder could
shrink it materially. Nothing in current evidence authorizes implementing that;
it would be its own narrow hypothesis and its own probe.

A defensible `C3.L2` outcome may be to accept `video_only_restart` for
**startup, manual and fallback** use while keeping automatic in-game adaptation
blocked pending the IDR question. That mirrors the Windows disposition without
copying its numbers.

---

## 6. Rules that bind Phase C work

Do not change: resolution, frame rate, GOP, B-frames, FEC wire format, RTP
payload type, packet size, ports, process audio, controller transport, emulator
lifecycle, Android streaming constants, or any non-loopback control surface.

Do not reopen: D4 Games, D5 media/server, the Windows-era C3 record (D-063,
D-067, D-068, D-069, D-070, D-071), or the deferred UDP burst/gap pathology.

The Windows 5500/6000/7000 bitrate ladder is **evidence, not a Linux constant**.
`C3.L3` must revalidate it on Linux before any level is treated as portable.

Adaptation stays frozen during `STABILIZING` and `PAUSED`
(`LAUNCHING → STABILIZING → READY → PLAYING`, D-067/D-068).

Never ask the user for IP addresses; redact network identity in diagnostics.

---

## 7. Operational facts

- Companion: `python3 ./companion/privyhub_service.py`. **Restart it whenever
  companion Python changes** — D-068 durable rule; stale-process behavior is not
  evidence.
- Continuity probe, trigger phase takes **no flag**:
  `python3 tools/probe_c3_actuator_continuity.py`
  then after normal Back: `... --finalize`.
  A `--trigger` flag does not exist.
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

## 8. Open debt, recorded and not blocking

- `_host_telemetry.start()` is never called on the Linux path; sender-side host
  resource telemetry is inactive on Linux. Phase E prerequisite.
- `_patches/` and `_probes/` are not covered by `.gitignore` (patterns are
  `privyhub_*`; directories are `PrivyHub_*`, which does not match on a
  case-sensitive filesystem). Both are untracked; confirm before committing.
- The Windows probe shares the `C3.L1` stale-baseline pattern. Its evidence
  never recorded `ffmpeg_spawn_ms`, so it cannot be checked retrospectively.
  Treat Windows "first RTP resume" figures as pipeline re-establishment time.
  Not fixed; Windows is outgoing.

## 9. Pointers, for detail only

- `investigations/C3_LINUX_ACTUATOR_BOUNDARY.md` — full boundary map and
  `C3.L1` history.
- `evidence/C3_L1_LINUX_ACTUATOR_RUNTIME_2026-09-18.md` and
  `evidence/C3_L1R1_LINUX_ACTUATOR_RUNTIME_2026-09-18.md` — raw runs.
- `evidence/C1_C2_LINUX_REVALIDATION_2026-09-18.md` — Linux baseline.
- `architecture/ADAPTIVE_BITRATE.md` — adaptation architecture and Windows-era
  history.
- `architecture/STREAM_TELEMETRY.md` — the C2 measurement contract C3 consumes.
- `CURRENT.md` — active bootstrap. `roadmap/STATUS.md` — roadmap position.
- `docs/KNOWN_ISSUES.md` — open gaps. `LEARNINGS.md` — durable lessons.
