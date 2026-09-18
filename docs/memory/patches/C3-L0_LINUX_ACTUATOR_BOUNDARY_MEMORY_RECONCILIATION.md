---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 310596dd0cc3ff22f3fe46e2eb025d052da90ec0
durable_memory_updated: true
---

# C3.L0 — Linux actuator boundary audit and memory reconciliation

## Purpose

Record the `C3.L0` Linux actuator boundary audit in durable memory, restore the
C1/C2 Linux baseline measurements that the 2026-09-18 checkpoint dropped,
regenerate the patch index, and make recording failures alongside successes an
explicit memory policy.

Documentation and durable memory only. No production source change, no new
diagnostic tool, no runtime execution.

## Expected predecessor

`310596dd0cc3ff22f3fe46e2eb025d052da90ec0`

## Changed scope

Replaced with fixed content:

- `docs/KNOWN_ISSUES.md`
- `docs/memory/CURRENT.md`
- `docs/memory/MEMORY.md`
- `docs/memory/LEARNINGS.md`
- `docs/memory/MAINTENANCE.md`
- `docs/memory/2026-09-18.md`
- `docs/memory/handoffs/CURRENT_HANDOFF.md`
- `docs/memory/roadmap/STATUS.md`
- `docs/memory/investigations/ACTIVE.md`
- `docs/memory/architecture/ADAPTIVE_BITRATE.md`
- `docs/memory/evidence/C1_C2_LINUX_REVALIDATION_2026-09-18.md`

Added:

- `docs/memory/investigations/C3_LINUX_ACTUATOR_BOUNDARY.md`
- `docs/memory/patches/C3-L0_LINUX_ACTUATOR_BOUNDARY_MEMORY_RECONCILIATION.md`

Generated at install time and validated:

- `docs/memory/patches/PATCH_INDEX.md`, built by scanning
  `docs/memory/patches/*.md`. Generated rather than transcribed because hand
  transcription of a ~70-entry directory is the known failure mode.

## Intentionally unchanged scope

- all companion production source, including `native_stream.py`,
  `native_stream_profiles.py`, `native_fec_relay.py`, `native_host_telemetry.py`
  and `plugins/games.py`;
- all Android source;
- all existing diagnostics and probes;
- `.gitignore`, including the `_patches/`/`_probes/` coverage gap, which is
  recorded as a known issue rather than fixed here;
- the Linux host-telemetry gap, recorded rather than fixed;
- all D4/D5 evidence and all Windows-era C3 evidence and investigations;
- `docs/ROADMAP.md` and `docs/PROJECT_STATUS.md`.

## Audit result summary

Boundary map, with full detail in
`docs/memory/investigations/C3_LINUX_ACTUATOR_BOUNDARY.md`:

| Parameter | Runtime mutable? | Restart required? | Safe? |
| --- | --- | --- | --- |
| bitrate | No | Encoder-process restart | Unknown on Linux |
| resolution | No | Restart plus APK change | No; C3 non-goal |
| FPS | No | Restart plus APK change | No; C3 non-goal |
| FEC | Structurally yes | No | Unvalidated; C4 owns it |
| pacing | No actuator exists | Not applicable | Out of C3 scope |

## Negative results recorded by this patch

- existing C3 probes cannot run on Linux and fail closed with
  `wgc_runtime_unavailable`;
- `_host_telemetry.start()` is never called on the Linux start path;
- `_patches/` and `_probes/` are not covered by `.gitignore`;
- the 2026-09-18 checkpoint dropped the C1/C2 Linux baseline measurements and
  the patch index;
- `live_bitrate_reconfigure` is foreclosed by the current external FFmpeg CLI
  architecture on Linux.

## Validation performed

Recorded in the package manifest and reported by `install.py --self-test`:

- installer Python compile;
- installer self-test on a synthetic fixture repository covering correct
  install, wrong-state rejection before modification, idempotent reinstall,
  generated-index correctness, and forced-rollback byte restoration;
- payload SHA-256 manifest generated and verified against installed output;
- predecessor SHA-256 verification for every replaced file;
- LF line endings and trailing newline preserved on every file;
- `git diff --check` executed by the delivery block;
- ZIP integrity verified by the delivery block before extraction.

No runtime or E2E validation applies; this patch changes no executable
behavior.

## Result

`INSTALLED SUCCESSFULLY` on the run recorded in `docs/memory/2026-09-18.md`.

## Next

`C3.L1` — Linux encoder-only restart continuity probe.
