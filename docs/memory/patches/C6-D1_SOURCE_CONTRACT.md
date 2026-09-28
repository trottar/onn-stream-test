---
memory_schema: 1
as_of: 2026-09-25
baseline_commit: 05aac43
durable_memory_updated: true
---

# C6-D1: the generalized native source contract (new files only)

## Purpose

This establishes the C6 contract without moving production code. Task:
`handoffs/C6-D1_SOURCE_ABSTRACTION_DESIGN_TASK.md` (authorized by the
user 2026-09-25). Record: `evidence/C6_D1_SOURCE_CONTRACT_2026-09-25.md`.
Architecture: `architecture/NATIVE_SOURCE_CONTRACT.md`.

## Change

New files only:

- `companion/native_source_contract.py` holds:
  - the `SourceLifecycle`, `ActuatorClass` and `AudioModel` enums;
  - `FecScheme` and `SourceCapabilities` (with `validate()`);
  - the `SourceProfile`, `NativeSource`, `Transport` and `ClientFeedback`
    protocols;
  - `GamesSourceDescription()`, filled from `native_stream_profiles`,
    `native_fec_relay` and `adaptive_bitrate`.

  **Nothing in production imports it**, and it never imports
  `native_stream`.
- `tools/test_native_source_contract.py`: 7 tests, 7 OK.

No existing file changed, no restart, no behavioural change.

## Files (SHA-256)

```
4e137b35b096d49e791eba3acb9aa61df9c741720250ad6479c54d5251b1fa83  companion/native_source_contract.py
58699cab9df243325459c141f08007b8dc13191abbabb9d854674974f4cf08fa  tools/test_native_source_contract.py
```

## Rollback

Delete both files.
