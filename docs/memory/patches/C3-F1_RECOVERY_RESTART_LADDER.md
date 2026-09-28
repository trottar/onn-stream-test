---
memory_schema: 1
as_of: 2026-09-25
baseline_commit: 05aac43
durable_memory_updated: true
---

# C3-F1: recovery's encoder restart, level-preserving at any ladder level

## Purpose

`C6-D1` finding 7: recovery's restart was the continuity diagnostic, which
refuses off 7000. Task: `handoffs/PHASE_C_PRECONDITIONS_2026-09-25_TASK.md`
§1. Record: `evidence/C3_F1_RECOVERY_RESTART_LADDER_2026-09-25.md`.
**Outcome: WORKING.**

## Change

- **`companion/diagnostics/c3_linux_actuator_probe.py`**:
  `_run_c3_linux_bitrate_cycle(..., same_level_restart=True)` restarts at
  the current validated level. There is a new
  `run_c3_linux_recovery_restart`, schema
  `privyhub_c3_recovery_restart_v1`.
- **`companion/native_stream.py`**: `recovery_restart_encoder()`. At 7000
  it is the unchanged continuity cycle; off 7000 it is the
  level-preserving restart.
- **`companion/plugins/games.py`**: recovery's `restart_encoder` is now
  `recovery_restart_encoder`, and there is a loopback-only diagnostic
  route `c3-recovery-restart`.
- **`tools/test_c3_f1_recovery_restart.py`** is new (8 tests).
  `tools/test_native_source_contract.py`'s import check now runs in a
  fresh interpreter.

## Files (SHA-256 after)

```
1c629dfae5e54652f7a23ea59da761d3da1ff6b4bb603137e7edf32fc2fcbfa9  companion/diagnostics/c3_linux_actuator_probe.py
07f8736ecf473159a606b91e1096dd63962d387d8812e833b61101f38e3d92a1  companion/native_stream.py
64180e90516d70919f916842e11a6bd5944e163622d540cf48bbad6d912e63fc  companion/plugins/games.py
6d5634daaf8126a84aebb15c0f558cb7f28df7a82ace11a6e6b2ec42c1b5c467  tools/test_c3_f1_recovery_restart.py
43e8c2ac7643b748b8ed5c1b2da1fa0e5cacd65add0c90077121fbfc3900fc65  tools/test_native_source_contract.py
```

Before: `evidence/c3_f1_2026-09-25/pre_patch_sha256.txt`. The diff is
`c3_f1_patch.diff`.

## Rollback

Revert the three hunks and restart the companion through its unit.
Recovery is then again refused off 7000.
