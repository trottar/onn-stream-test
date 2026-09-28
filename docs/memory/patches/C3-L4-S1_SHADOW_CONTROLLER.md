---
memory_schema: 1
as_of: 2026-09-24
baseline_commit: 05aac43
durable_memory_updated: true
---

# C3-L4-S1: the shadow adaptive-bitrate controller (flag default off)

## Purpose

This builds the `C3.L4` policy engine in a mode that cannot act. It
watches the 2 s client telemetry and logs what it would have done. Task:
`handoffs/C3-L4-S1_SHADOW_CONTROLLER_TASK.md` (weekend queue item 4,
authorized by the user 2026-09-24). Design:
`architecture/ADAPTIVE_BITRATE.md` §"C3.L4 shadow controller — S1".
Record: `evidence/C3_L4_S1_SHADOW_CONTROLLER_2026-09-24.md`.

## Change

- **New** `companion/adaptive_bitrate.py`:
  - `ShadowPolicy`, the pure engine (no clock, no I/O, no actuator);
  - `AdaptiveBitrateShadow` (mode from `PRIVYHUB_ADAPTIVE_BITRATE_MODE`,
    `off` by default and for any unknown value; `shadow` evaluates and
    logs to `logs/games/adaptive_bitrate_shadow.jsonl`, rotated 4 MiB × 3);
  - `get_shadow()`, one per process.
  - There is no acting mode and no actuator import.
- `companion/privyhub_service.py`: in the `/diagnostics/client-health`
  POST, the telemetry snapshot that `STREAM_TELEMETRY_STORE.accept` returns
  is passed to `observe()`, inside the existing never-disturb `try`. The
  native status is read once and shared by both.
- `companion/plugins/games.py`: `native-stream-status` carries
  `adaptive_bitrate` (`privyhub_adaptive_bitrate_v1`), which reads `mode:
  off, acted: false` with the flag unset.
- **New** `tools/test_adaptive_bitrate_shadow.py`: 21 unit tests on
  synthetic telemetry.

No client, profile, encoder, route-shape or transport change.

## Validation

- `py_compile` and `git diff --check` are clean. `python3 -m unittest
  tools/test_adaptive_bitrate_shadow.py -v`: **21 / 21 OK**, run before
  any restart with the flag (`evidence/c3_l4_s1_2026-09-24/unit_tests.txt`).
- **Flag off**, after a restart through the unit (MainPID owns 8765, no
  `PRIVYHUB_*` in its environ): `native-stream-status` gained exactly one
  key, `adaptive_bitrate: {schema, mode: off, acted: false}`, and nothing
  else changed. The profile is adopted (`status_flag_off.json`).
- **Shadow**: the four-hold night, in the record.

## Files (SHA-256 after)

```
d66211b38175b8c5d11305964e5fa060a21854e3acb559d22d2eb63c33b924ec  companion/adaptive_bitrate.py
7022dd994aa30204f1109fea40b0276487a1558a7506211c20c2ac3a8377501d  companion/privyhub_service.py
206a9497210b273e5f8366f491403cfe99589628e1918ad65d139f784b94396f  companion/plugins/games.py
62e1a011799982bf2a9a1ffa020053187fc1da2a4f139d4cbadc57d5db68b809  tools/test_adaptive_bitrate_shadow.py
```

Before: `evidence/c3_l4_s1_2026-09-24/pre_patch_sha256.txt`. The diff of the
two edited files is `companion_patch.diff`. The new module and the tests
are copied into the same directory.

## Rollback

Delete `companion/adaptive_bitrate.py` and revert the two hunks
(`companion_patch.diff`), then `systemctl --user restart
privyhub-companion`. With the flag unset, the module already evaluates
nothing.
