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
