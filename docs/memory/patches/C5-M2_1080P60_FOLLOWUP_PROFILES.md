---
memory_schema: 1
as_of: 2026-09-29
baseline_commit: f01c3b2
durable_memory_updated: true
---

# C5-M2: the three 1080p60 follow-up profiles and the generic C5 hold harness

## Purpose

C5-M1 found 1080p60 at parity (15,750 kbps, cap 200,000 B) NOT CAPABLE
(stream): the per-frame burst on the wireless hop, at 2.25× the frame
size. Its record named three levers. The user authorized running them
(2026-09-28): the transport will need 1080p for later cores and the
remote path.

- Task: `handoffs/C5-M2_1080P60_FOLLOWUP_ARMS_TASK.md`.
- Record: `evidence/C5_M2_1080P60_FOLLOWUP_2026-09-29.md`.

## Change

**`companion/native_stream_profiles.py`:** a `_c5_1080p60()` helper and
three named profiles in `NATIVE_STREAM_PROFILES`. Each is 1920×1080 @ 60,
GOP 15, bframes 0, FEC 8, cushion 12/17 and redundancy 2/4 as adopted.
None is ever the default.

| id | kbps | cap B |
| --- | --- | --- |
| `native_game_1080p60_c1_parity_cap90` | 15,750 | 90,000 |
| `native_game_1080p60_c2_80pct_cap160` | 12,600 | 160,000 |
| `native_game_1080p60_c3_80pct_cap90` | 12,600 | 90,000 |

- **The selector, the reference profile and every other module are
  unchanged.**
- **Golden:** with the selector unset, the argv and the profile fields
  are byte-identical before and after (`golden_before.txt` =
  `golden_after_unset.txt`). With each id set, the argv carries
  `scale=1920:1080`, the arm's `-b:v / -maxrate / -bufsize` and
  `-max_frame_size`, and `any_override` true.
- **`tools/test_c5_m1_profile_selector.py`:** 11/11 (8 + 3 `C5M2Arms`).

**The harness** (`evidence/c5_m2_2026-09-29/`). It is C5-M1's, extended,
not rewritten:

- `c5_m2_run.sh`: `ARM_PROFILE=<id>` replaces `PROFILE_ARM=A|B`. The
  profile check reads the expected id, size, bitrate and cap from the
  companion's own table.
- `c5_m2_night.sh`: the holds are arguments (`<name>:<id>`); the runs
  dir is `$RUNS`; the teardown is C5-M1's on every exit path.
- `c5_m2_score.py`: `screen` and `confirm` modes. The rows, targets and
  S1 cost rule are C5-M1's. Each hold's cap and profile come from its
  `armcheck`. It reproduces C5-M1's outcome on C5-M1's data.

No client change, no APK built, no encoder flag beyond width, height,
bitrate and cap. Nothing adopted. Nothing committed.
