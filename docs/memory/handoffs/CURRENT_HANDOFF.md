# Current Handoff

The authoritative resumable state is `../CURRENT.md`.
The compact Phase C brief is `../PHASE_C_CONTEXT.md`; **start there**. It is
self-sufficient and does not require reading the wider hierarchy.

D5 media/server restoration remains COMPLETE / RUNTIME VALIDATED.
D4 Games remains COMPLETE / RUNTIME VALIDATED.

## Where Phase C stands

- C1 profile/backend and C2 telemetry are complete on Linux.
- `C3.L0` boundary audit, `C3.L1` and `C3.L1R1` encoder-only actuator runs are
  complete. The actuator preserves FEC, process audio, controller and emulator
  lifecycle across a cycle, reproduced twice with zero errors.
- `C3.L2` classified Linux as `video_only_restart`: authorized for start-time
  profile selection, manual and loopback-only diagnostic changes, fallback and
  recovery, and `C3.L3` characterization; **not** authorized for automatic
  adaptation during play. `C3.L4` stays blocked.
- `C3.L2a` E1 read the existing evidence and could not answer its question.

## The one thing a new session must not get wrong

**287-318 ms is not established as the cost of the actuator.**

The decoder session report's slow-event list is a 128-entry ring. In the
`C3.L1R1` session it was full and retained only the last 29.4 s of a 64.8 s
session, so the row explaining `max_output_gap_ms` 287 was already gone. In the
window that did survive — ordinary play, no actuator — `output_gap_ms` tracks
`codec_ms` one-to-one and reaches 238 ms and 200 ms, with feed delay near zero
and an empty app queue.

So the cycle's figure sits on top of a baseline that reaches 238 ms unaided. The
attributable actuator cost is either ~50 ms or not separately visible, and this
evidence cannot tell which. Quote the figure with that qualification or not at
all.

Two earlier framings are also corrected and must not be revived: a fresh FFmpeg
RTP stream already begins with in-band parameter sets and an IDR, so "request an
immediate IDR on the replacement encoder" has no premise; and
`max_frames_between_idr` is 27 against GOP 15, so the worst-case keyframe wait
is ~450 ms rather than the 250 ms the one-GOP reasoning assumed.

## Next work item

`C3.L2b` — decoder-report cycle retention.

Make the decoder session report retain the cycle: marked-window retention or a
segmented slow-event buffer, `elapsed_ms` anchors for the SSRC change and the
sequence resyncs, and per-event IDR context for the first accepted IDR after an
SSRC change.

Diagnostic-only client work: it changes the report, not decoder configuration,
resolution, frame rate, GOP or any streaming constant. It carries a real
`sh ./gradlew :app:assembleDebug --no-daemon`, an `adb install -r`, and one
clean actuator cycle afterwards to produce evidence that survives.

**Do not re-run `tools/probe_c3_actuator_continuity.py` before `C3.L2b` lands.**
The existing report would evict the same row again.

Registered, not scheduled, **not authorized**: `C3.L2c`, enabling MediaCodec
low-latency decode. `low_latency_enabled` is false on
`c2.realtek.video.avc.decoder` while 2,696 of 3,847 frames took 20 ms or more to
decode. It is a production client behavior change needing its own hypothesis and
its own focused gameplay acceptance, and it must not ride along inside
`C3.L2b`. The user decides whether it or `C3.L2b` runs first; only `C3.L2b`
unblocks `C3.L2a`.

Also standing: do not begin D7 as the next major development item, and do not
begin Phase E — it measures a finalized architecture.

D6 UDP replay remains historical; active ownership is Phase C transport
validation.

## C3 entry conditions

Read `../decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`,
`../evidence/C3_L2A_E1_DECODER_EVIDENCE_PASS_2026-09-18.md` and
`investigations/C3_LINUX_ACTUATOR_BOUNDARY.md` before proposing any actuator
work. They record what is classified, what is authorized, what is foreclosed and
what is merely assumed.

Do not rebuild the Windows-era C3 record. D-063, D-067, D-068, D-069, D-070 and
D-071 are closed and remain authoritative as history.

Tool inventory and the two diagnostic retention limits are in `../TOOLS.md`.

## Patch Procedure

Meaningful updates use the standard PrivyHub patch workflow:
- ZIP delivered into repository root;
- predecessor state/hash verification;
- wrong-state rejection before modification;
- backups under archive/patch_backups;
- one coherent change;
- validation, including `tools/check_memory_health.py` as an installer-enforced
  post-write gate;
- exact rollback on failure;
- git diff validation;
- commit and push;
- runtime validation when applicable.

Durable memory is part of the patch, not after-the-fact prose. Every patch
records failures, rejections and rollbacks alongside successes; see the
negative-result policy in `../MEMORY.md`.

Local testing directories such as `_patches/` and `_probes/` are development-only
and are not part of pushed changes unless explicitly intended. They are not
currently covered by `.gitignore`; confirm with `git status --short` before
committing.
