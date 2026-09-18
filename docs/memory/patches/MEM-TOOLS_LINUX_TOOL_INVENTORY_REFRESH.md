---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 6abe47d2f7adf1eae847d3b23b12b760586f6d41
durable_memory_updated: true
---

# MEM-TOOLS — Linux tool inventory refresh

## Purpose

`docs/memory/TOOLS.md` was still the 2026-09-10 Windows-era file. It gave
`L:\Projects\onn-stream-test` paths, PowerShell entry points and
`python .\companion\privyhub_service.py`, and listed none of the Linux probes
under `tools/probes/`. A memory file that names the wrong platform's commands is
worse than an absent one, because it is followed.

Durable memory only. No production source change, no tool change, no probe
change, no new runtime evidence.

## Expected predecessor

`6abe47d2f7adf1eae847d3b23b12b760586f6d41`

This patch touches no file that `C3.L2` touches, so it installs cleanly whether
or not `C3.L2` has been installed first. Predecessor identity is enforced by
per-file SHA-256, not by the commit hash.

## Changed scope

Replaced:

- `docs/memory/TOOLS.md` — rewritten against the current `tools/` tree.

Added:

- `docs/memory/patches/MEM-TOOLS_LINUX_TOOL_INVENTORY_REFRESH.md` — this record.

Generated and validated: `docs/memory/patches/PATCH_INDEX.md`.

## What the refreshed file now records

- Linux entry points: `python3 ./companion/privyhub_service.py`, the Gradle and
  `adb install` path, and the D-068 companion-restart rule.
- `tools/check_memory_health.py` as the required memory gate, and
  `tools/audit_repo_checkpoint.py` as the checkpoint audit.
- `tools/collect_game_session_diagnostics.py` with its nine bundle sections and
  its IPv4 redaction.
- Two retention limits that decide how the bundle may be read: the host-log
  section is the last 500 lines only, and the decoder session's slow-event list
  is a fixed-capacity ring that reports `slow_event_retained` and
  `slow_event_capacity`. Also that whole-session fields are not per-event
  measurements.
- The streaming probes, including that `probe_c3_actuator_continuity.py` takes
  no flag on trigger and dispatches by platform.
- **The four Windows-only C3 probes that fail closed on Linux with
  `wgc_runtime_unavailable`.** Recorded so a future session does not mistake a
  fail-closed refusal for a broken Linux backend.
- The `tools/probes/` Linux inventory grouped by subsystem, the storage
  administration tools, and the Phase A games probes.
- The Windows-era scripts retained as history, and the Opal router-boundary
  branch closed by D-083.

## Negative result recorded

The stale file is itself the negative result: `C3.L0` through `C3.L2` all ran
without consulting `TOOLS.md`, because its first line was a Windows path. A
reference that is wrong in its first line stops being read, and nothing in the
memory health check covers content accuracy.

## Validation performed

- installer Python compile;
- installer self-test against a fixture: wrong-state rejection before
  modification with a byte-identical snapshot, clean install, installed-hash
  verification, generated-index correctness and exclusions, idempotent
  reinstall, memory-health gate failure forcing rollback, forced-validation
  rollback restoring exact predecessor bytes and removing added files;
- every path, flag and filename named in the new `TOOLS.md` checked against a
  live listing of `tools/`, `tools/probes/` and `tools/storage/`, and against
  the argparse definitions of `collect_game_session_diagnostics.py` and
  `probe_c3_actuator_continuity.py`;
- `tools/check_memory_health.py` executed as a post-write gate;
- payload and installed SHA-256 verification;
- LF line endings and trailing newline preserved;
- `git diff --check` and ZIP integrity executed by the delivery block.

No runtime validation applies; this patch changes no executable behavior.

## Result

Recorded on install.
