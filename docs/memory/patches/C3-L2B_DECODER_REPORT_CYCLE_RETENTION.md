---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: e220d3e39c896bac89bc8d286279b480cba50669
durable_memory_updated: true
---

# C3.L2b — decoder-report cycle retention

## Purpose

`C3.L2a` E1 found that the decoder session report's slow-event list is a
128-entry flat ring: in the `C3.L1R1` session it was full and retained only
elapsed 35,421-64,813 ms of a 64,842 ms session, so the row explaining
`max_output_gap_ms` 287 was gone before the report was written. Any session
with more than 128 slow events after an actuator cycle discards the cycle's
own evidence. `C3.L2a`'s question — why the receiver's first accepted IDR is
late after an encoder-only cycle — cannot be answered until the report
survives the cycle. This patch is that instrumentation.

Diagnostic-only client work. It changes what the decoder session report
retains and records; it does not change decoder configuration, resolution,
frame rate, GOP, B-frames, FEC wire format, RTP payload type, packet size,
ports, process audio, controller transport or emulator lifecycle.

## Expected predecessor

`e220d3e39c896bac89bc8d286279b480cba50669`

Stacks on `STREAMLINE_REPOSITORY_LAYOUT` and `C3-L2A-E1_FIRST_IDR_EVIDENCE_PASS`,
both installed. Predecessor identity is enforced by per-file SHA-256, not by
the commit hash.

## What changed, and why it satisfies the three E1 requirements

**1. Marked-window retention on the decoder's slow-event buffer, instead of
one flat FIFO ring.** `AvcLowLatencyDecoder`'s single 128-entry
`ArrayDeque<DecoderSlowEvent>` becomes two: a 64-entry `recent` segment (the
old behavior, just at half capacity) and a 64-entry `marked` segment that is
only written to while a cycle window is open, and is otherwise untouched by
ordinary-play eviction. `RtpH264Receiver` calls a new
`onStreamDiscontinuity` hook on every SSRC change and sequence resync;
`NativeStreamActivity` wires that hook to `decoder?.markCycleWindow(nowNs)`,
which opens a 2000 ms protected window (generous against the measured cycle
terms: encoder spawn 115-215 ms, RTP silence ~152 ms, decoder output gap
287-318 ms, resync-to-IDR 191-241 ms). The report still emits one
chronological `slow_events_ge_50_ms` array in the unchanged 7-column shape
(merged and sorted by `elapsed_ms`), so no existing reader of that field
breaks; `slow_event_retained` / `slow_event_capacity` keep their old
whole-report meaning, and four new fields
(`slow_event_retained_marked`, `slow_event_capacity_marked`,
`slow_event_retained_recent`, `slow_event_capacity_recent`) make the
segmentation visible.

**2. `elapsed_ms` anchors for the SSRC change and the sequence resyncs.**
`RtpH264Receiver` now records a bounded (64-entry) list of
`StreamDiscontinuityEvent { elapsedMs, type, jumpPackets }` inside
`beginStreamResync`, emitted as `stream_discontinuities` /
`stream_discontinuity_capacity`. `type` is `"ssrc_change"` or
`"sequence_resync"`, set explicitly at each of `beginStreamResync`'s two call
sites rather than inferred from `jumpPackets`.

**3. Per-event IDR context for the first accepted IDR after a discontinuity.**
`completeStreamResync` (called exactly when `waitingForIdr && isIdr`) now
records a bounded `FirstIdrAfterDiscontinuity { elapsedMs, resyncToIdrMs,
auComplete, auFecRecovered, auFecUnrecoverableGroup }` — only when it follows
an actual discontinuity (`resyncStartedNs > 0`), not the very first IDR at
session start. `auComplete` is `!currentCorrupt` at delivery (by construction
always true for a delivered frame under current drop rules; kept as a real
field rather than assumed, in case delivery rules change). `auFecRecovered`
and `auFecUnrecoverableGroup` are new per-access-unit flags, correctly
threaded through the packet-hold/drain path: `heldPackets` changed from
`HashMap<Int, ByteArray>` to `HashMap<Int, HeldPacket>` so a packet's
FEC-recovery provenance survives being held for reordering, not just its
bytes. `auFecUnrecoverableGroup` is set when an unrecoverable-group event's
timestamp matches the access unit under assembly, checked at both failure
paths (`attemptRecoverGroup`'s direct failure, `pruneCaches`'s timeout
eviction). `trimFecGroups`'s capacity eviction (>96 concurrently buffered
groups) is deliberately **not** correlated — reaching that needs loss well
past anything in C3 evidence, and leaving it out can only under-report the
flag, never over-claim recovery. Emitted as `first_idr_after_discontinuity` /
`first_idr_after_discontinuity_capacity`.

## Changed scope

**Replaced, 3 files** (Android/Kotlin source):

- `PrivyHub/app/src/main/java/streaming/AvcLowLatencyDecoder.kt` — segmented
  slow-event buffer, `markCycleWindow` / `markedSlowEventsSnapshot`;
- `PrivyHub/app/src/main/java/streaming/RtpH264Receiver.kt` —
  `StreamDiscontinuityEvent` / `FirstIdrAfterDiscontinuity` tracking,
  `HeldPacket` FEC-provenance wrapper, `onStreamDiscontinuity` callback;
- `PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt` — wires the
  discontinuity callback to the decoder, merges the two slow-event segments
  and emits the new report fields.

**Replaced, 9 memory/doc files:** `docs/memory/CURRENT.md`,
`docs/memory/PHASE_C_CONTEXT.md`, `docs/memory/handoffs/CURRENT_HANDOFF.md`,
`docs/memory/2026-09-18.md`, `docs/memory/MEMORY.md`,
`docs/memory/investigations/ACTIVE.md`,
`docs/memory/investigations/C3_LINUX_ACTUATOR_BOUNDARY.md`,
`docs/memory/roadmap/STATUS.md`, `docs/KNOWN_ISSUES.md`.

**Added:** this record. **Generated:** `docs/memory/patches/PATCH_INDEX.md`.

## Intentionally unchanged scope

Every streaming constant listed in "Purpose" above; the FEC wire header and
recovery algorithm's success/failure semantics (only new read-only
observation was added); `NativeAudioReceiver.kt`, `NativeControllerSender.kt`,
`GameStreamStatusUi.kt`; all companion Python; all probes and tools,
including `tools/probe_c3_actuator_continuity.py` (per `CURRENT_HANDOFF.md`
and `PHASE_C_CONTEXT.md`, it is run again only *after* this patch, not
touched by it); the `C3.L2` decision record and every earlier evidence
record; `AGENTS.md`, `MAINTENANCE.md`, `TOOLS.md`, `.gitignore`,
`docs/memory/LEARNINGS.md`, `docs/memory/decisions/`.

## Negative results and scope decisions recorded by this work item

- `trimFecGroups`'s capacity-eviction path is not correlated into
  `auFecUnrecoverableGroup`, by choice — see "What changed" above. This is a
  known, accepted gap in the new instrumentation, not an oversight.
- The default 2000 ms cycle window is a judgment call informed by the
  measured cycle terms (max observed component ~318 ms), not itself a
  runtime-validated figure. If a future cycle's discontinuity-adjacent slow
  events land outside it, that is a finding for the next evidence pass, not
  a defect in this patch — the window only has to outlast the terms it was
  set against.
- This patch does not answer `C3.L2a`. It only removes the instrumentation
  defect that made the question unanswerable. `C3.L2a` reopens after a clean
  actuator cycle is run against the rebuilt client and its report is read.
- `C3.L2c` (MediaCodec low-latency mode) is not part of this patch, was not
  evaluated, and remains registered / not scheduled / not authorized.

## Validation performed

- installer Python compile;
- installer self-test against a fixture built from the real predecessor
  bytes: wrong-state rejection before modification with a byte-identical
  snapshot, clean install, installed-hash verification, idempotent reinstall,
  memory-health gate failure forcing rollback, forced-validation rollback
  restoring exact predecessor bytes;
- `tools/check_memory_health.py` executed as a post-write gate;
- `docs/memory/CURRENT.md` heading structure asserted: all seven required
  headings present exactly once;
- payload and installed SHA-256 verification for every touched file;
- LF line endings and trailing newline preserved;
- `git diff --check` and ZIP integrity executed by the delivery block;
- the three Kotlin files were compiled for real with the Kotlin 2.0.21
  compiler: `RtpH264Receiver.kt` has no Android dependencies and compiled
  standalone against the JDK only; `AvcLowLatencyDecoder.kt` compiled against
  minimal hand-written stubs of the exact `android.media`/`android.os`/
  `android.view` API surface it uses; the report-building logic added to
  `NativeStreamActivity.kt` was re-implemented verbatim in an isolated
  harness linked against the real compiled `DecoderSlowEvent`,
  `StreamDiscontinuityEvent` and `FirstIdrAfterDiscontinuity` classes plus a
  minimal `org.json` stub, run, and asserted to produce a chronologically
  merged, correctly labeled report fragment. **This is not a substitute for
  `./gradlew :app:assembleDebug`** — no Android SDK was available to this
  session (no shell on the linked device), so `NativeStreamActivity.kt` was
  never compiled as a whole against the real Android/Activity framework or
  the real `org.json`. That full compile is the installer's own post-write
  gate, run on your machine, where the Android SDK actually is.

Not yet performed, and explicitly not claimed: `adb install -r`, a clean
actuator cycle, or a re-run of the `C3.L2a` evidence pass. Those are the
immediate next steps after this installs, not part of it.

## Result

Recorded on install.
