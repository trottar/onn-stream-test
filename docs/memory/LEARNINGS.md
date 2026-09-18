---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Durable Learnings

## State and patching

Git history is not a substitute for the actual validated working tree. A previous A8 installer reconstructed expected bytes from Git and rejected the correct local state. Prefer exact local receipts/hashes when they exist.

A failed installer can still have side effects before a production write. Always distinguish project-file modification state from other runtime cleanup actions.

## Validation

Never equate “planned validation” with “validation passed.” A previous package hit a permission failure before synthetic compilation but was initially described as compiled; that must not recur.

Validate the exact generated output, not only the generator. Validate the exact command-construction path, not merely the intended command.

## PowerShell/Windows compatibility

The prototype uses a Windows PowerShell/.NET environment where newer APIs may not exist. `[System.IO.Path]::GetRelativePath` caused a real installer failure. Prefer compatible path logic. PowerShell syntax must be parsed before execution; multiline boolean formatting previously caused a parser failure.

Use absolute paths in installer/staging logic where relative .NET process working directories can diverge. A documentation-bootstrap command also demonstrated that a `finally` block cannot be pasted after its `try/catch` has already executed; user-facing PowerShell blocks must keep cleanup inside one syntactically complete construct or perform cleanup explicitly after the guarded command.

## Android UI

`AlertDialog` paths using both message content and selectable item lists repeatedly hid the list on the Android TV UI. Probes must test the actual reachability/failure condition, not merely source-string presence.

## Terminology

“A/B swap” is ambiguous. Say whether the operation is physical BUTTON A/B remapping, internal RetroPad A/B mapping, or Player 1/Player 2 assignment.

## Diagnostics

Know the lifecycle of each diagnostic artifact. A live status file and a final session-history file are not interchangeable. One A4 probe falsely failed because it required a final audio timing log before shutdown.

When a classifier contradicts raw measurements, investigate the raw measurements first.

## Scope control

Working subsystems should not be “improved” during unrelated fixes. This project has benefited most from contained probes, reversible patches, and stopping feature polish after runtime success.

## Negative results are results

Durable memory records what failed as well as what worked. A record that keeps
only successes teaches nothing and invites repeated attempts down paths already
known to be dead. Rejected candidates, rolled-back installers, wrong-state
rejections and probes that could not run are all results and are written down in
the same work that produced them.

State explicitly when a run was clean. An absent failure section must mean "none
occurred", never "none were recorded". The 2026-09-18 C1/C2 checkpoint recorded
a bare `PASS` with no measurements and no failure section, leaving the Linux
baseline outside the repository entirely; `C3.L0` had to reconstruct it.

## Compression must not destroy measurements

Memory maintenance that shortens active files must first verify the canonical
evidence record holds the detail. The 2026-09-18 checkpoint reduced `CURRENT.md`,
`roadmap/STATUS.md`, `investigations/ACTIVE.md`, the dated file and
`patches/PATCH_INDEX.md` to single-line assertions. `PATCH_INDEX.md` lost its
index of roughly seventy patch records that still existed on disk.

Prefer a generated index over a hand-transcribed one where the source of truth is
a directory. Transcription is the failure mode; generation plus validation is
not.

## Cross-platform evidence does not transfer by default

Windows-era C3 measured a 0.84-0.95 s RTP interruption for a video-only encoder
restart and rejected it for automatic adaptation. That figure is a property of
the Windows two-process topology (WGC bridge feeding FFmpeg over an inherited
pipe), not of the actuator strategy. Linux runs a single FFmpeg process with
x11grab as an input format.

Carry the *strategy* and the *capability model* across platforms. Re-measure the
*numbers*. A validated ladder from one backend is a hypothesis on another.

## Audit the client when auditing a stream parameter

Stream parameters can be owned jointly by host and client without any
negotiation between them. Resolution and FPS are FFmpeg arguments on the
companion *and* independent compile-time constants in the Android activity, with
the decoder ignoring `INFO_OUTPUT_FORMAT_CHANGED`. A host-only audit would have
classified them as restart-mutable; they are actually APK-mutable, and the two
sides can silently diverge.

Conversely, check whether a wire format is self-describing before assuming a
parameter is pinned. FEC group size looked like a fixed constant on both ends
but is carried per-group in the header and validated by the receiver.

## Inspect the repository's own validators before rewriting what they validate

`C3.L0` rewrote `docs/memory/CURRENT.md` wholesale without first reading
`tools/check_memory_health.py`, which requires seven exact section headings, each
present exactly once. The rewrite used different names and casing, so the
checker still reported `maintenance_required` after a patch whose stated purpose
included memory reconciliation.

The pre-existing 182-byte `CURRENT.md` had no headings at all and was already
failing the same check, so `C3.L0` did not introduce the regression. It
inherited it and failed to fix it, which is worse in one specific way: the patch
looked like it had addressed memory health.

The project instruction to inspect existing tools and probes before creating
anything new applies to validators too, not only to diagnostics. A validator in
the repository is a specification of the file it checks.

## A validation step that is only documented is not a gate

`MAINTENANCE.md` already listed running `tools/check_memory_health.py` as step 9
of the maintenance procedure. It was documented and still skipped, because
nothing enforced it and the installer's own validation did not include it.

Where a repository ships a checker for state a patch modifies, the installer
runs it and treats a reported problem as a post-write validation failure with
rollback. Documented intent does not survive; executed gates do.
