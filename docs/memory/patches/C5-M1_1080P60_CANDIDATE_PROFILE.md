---
memory_schema: 1
as_of: 2026-09-28
baseline_commit: f01c3b2
durable_memory_updated: true
---

# C5-M1: a 1080p60 candidate profile behind `PRIVYHUB_NATIVE_PROFILE_ID`

## Purpose

C5: characterize 1080p60 as a stream/client capability. Task:
`handoffs/C5-M1_1080P60_PROFILE_TASK.md`. Record:
`evidence/C5_M1_1080P60_PROFILE_2026-09-28.md`. **Nothing adopted.** The
adopted profile's values do not change; with the selector unset the encoder
argv is byte-for-byte as before.

## Change

- **`companion/native_stream_profiles.py`**: `NATIVE_GAME_1080P60_CANDIDATE`
  (`native_game_1080p60_candidate`: 1920x1080, 60 fps, 15,750 / 15,750
  kbps, GOP 15, B 0, FEC 8, cap 200,000 B; cushion 12/17 and redundancy
  2/4 copied unchanged); `PROFILE_ID_ENV`, `NATIVE_STREAM_PROFILES`,
  `select_native_profile(environ)`.
- **`companion/native_stream.py`**: `NativeStreamManager._apply_profile_selection()`,
  called first in `__init__`, shadows `PROFILE`, `WIDTH`, `HEIGHT`, `FPS`,
  `GOP_FRAMES`, `BITRATE_KBPS`, `MAX_BITRATE_KBPS`, `BFRAMES` and
  `FEC_GROUP_SIZE` on the instance (the class keeps the adopted profile);
  `encoder_overrides()` gains `profile_id_env` / `profile_id_override` and
  counts the selector in `any_override`; `status()` gains
  `profile_selection`.
- **`tools/test_c5_m1_profile_selector.py`** is new (8 tests).
- **No client change; no APK built.** The onn's decoder delivered
  1920x1080 buffers from the unchanged adopted APK.

## Validation performed

- `py_compile` of both companion files.
- Golden (`evidence/c5_m1_2026-09-28/c5_m1_golden.py`): argv, profile and
  override fields from the real manager code; **unset after == before,
  byte-identical** (`golden_before.txt`, `golden_after_unset.txt`); the
  candidate differs only in scale/pad size, bitrate/maxrate/bufsize and
  the cap (`golden_after_candidate.txt`).
- Unit tests 8/8 (`python_tests.txt`); the five existing companion test
  files still pass.
- Runtime: both smokes and the six holds (the record).

## Files and SHA-256

Before:

- `companion/native_stream.py` `07f8736ecf473159a606b91e1096dd63962d387d8812e833b61101f38e3d92a1`
- `companion/native_stream_profiles.py` `67c12d5bb84443b342ecf5d96c55c10031110cbdd6e4bb2106a0ea1b2a8754d4`

After:

- `companion/native_stream.py` `68f7f6c8af5008e1a7562968767eef265cb93a9ae2482e3233792c28c727bee7`
- `companion/native_stream_profiles.py` `9504b22365ac53d10985b8760c050c1de748c049bb3c4a44d62f549518b1fe6d`
- `tools/test_c5_m1_profile_selector.py` `d3e83ec4fe1d219d9f7e14a40887fa69ef9a7d1cd3e406f90045d2e8160692ba` (new)

Diff: `evidence/c5_m1_2026-09-28/c5_m1_patch.diff`. Not committed.
