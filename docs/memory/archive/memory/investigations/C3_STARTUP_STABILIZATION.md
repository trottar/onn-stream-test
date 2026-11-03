---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: b2f752223d0bd7617a7f7ef75c9618202d2372fa
status: development_patch_runtime_validation_pending
---

# C3 startup stabilization and shared stream-status UI

## Question

Can PrivyHub hide native-stream startup instability behind the already-paused
game launch, release gameplay only after measured receiver/decoder stability,
and reuse the same basic stream metadata in the paused Game Session UI?

## D-067 implementation

This is a startup readiness gate, not a multi-second playback buffer.

State model:

`LAUNCHING -> STABILIZING -> READY -> PLAYING`

Companion:
- `native-stream-start` guarantees the active emulator is paused and no longer
  resumes gameplay automatically;
- `native-stream-ready` is the explicit release boundary after Android
  readiness succeeds;
- `native-stream-stop` remains the existing pause-on-exit path.

Android:
- full-screen `Stabilizing game…` overlay;
- game title, resolution/FPS, bitrate, FEC, video/audio/controller state;
- controller gameplay input consumed while stabilizing; Back still works;
- six consecutive clean 500-ms local checks are required:
  host metadata complete, receiver/decoder active, not waiting for IDR,
  rendered frames advancing, no new decoder drops/overflows, queue depth zero,
  recent FPS >=45, output gap <=120 ms, receive-to-decode <=150 ms, host audio
  and controller active;
- a failed check resets the consecutive-clean counter;
- 15-second ceiling fails closed and leaves gameplay paused.

Pause UI:
- existing Back -> paused-frame -> MainActivity lifecycle is preserved;
- `GameStreamStatusUi` is a pure in-process snapshot/formatter reused by
  NativeStreamActivity and the existing Game Session banner;
- no IPs, endpoints, ports, SSRC or sequence identifiers are presented.

Adaptive controller:
- still not enabled by this patch;
- future controller must freeze while STABILIZING or PAUSED and require fresh
  post-transition evidence before another bitrate decision.

## Runtime validation required

Validate overlay/readiness/release, input gating, Back/pause metadata reuse,
Resume/Save/Load/End regression, and fail-closed behavior.

## Runtime validation — accepted

After a clean companion restart:
- stabilization GUI appeared;
- release succeeded;
- gameplay was normal;
- no initial lag was observed.

The first failed attempt was classified as mixed-version runtime evidence:
Android had D-067 while the live companion process still had predecessor Games
plugin behavior. Existing RetroArch lifecycle evidence proved a real pause and
later old-path resume. Restarting the companion fixed the same installed source.

Status: **COMPLETE / RUNTIME VALIDATED**.

Paused Game Session metadata is implemented; it was not separately promoted by
instrumented evidence in this acceptance.
