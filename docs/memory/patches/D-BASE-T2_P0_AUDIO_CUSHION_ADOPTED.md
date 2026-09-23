---
memory_schema: 1
as_of: 2026-09-23
baseline_commit: 3e6cde5
durable_memory_updated: true
---

# D-BASE-T2 Part 0 — the 12 / 17 audio cushion is the profile default

## Purpose

The user adopted 12 / 17 on 2026-09-23 after `P9a`
(`decisions/D-BASE-P9_AUDIO_CUSHION.md`). One value pair in the
companion's reference profile; the setting itself is `P9`'s
(`patches/D-BASE-P9_AUDIO_CUSHION_SETTING.md`). Applied directly under the
task authorization (`handoffs/D-BASE-T2_TASK.md`), not as a ZIP.

## Changed scope

**`companion/native_stream_profiles.py`**
-> `85369733bbbd9d3d2f7263d58f1e96e7108c236a11b3091293aa2ce5503d1312`
(was `11287c52c571d590aa697788599d632a89259e5b1924d5777af9e6555aecc06f`).

- `native_game_720p60_reference`: `audio_queue_target_packets` 3 → **12**,
  `audio_queue_capacity_packets` 8 → **17**; the comment now records the
  adoption and the measured cost.

**No client change and no build**: the default lives in the companion and
reaches the client in the `native-stream-start` response
(`audio_cushion`). APK stays `a9355bb0…4a72`.

## Validation performed

- `py_compile`; `git diff --check` clean.
- `systemctl --user unset-environment PRIVYHUB_AUDIO_QUEUE_TARGET_PACKETS
  PRIVYHUB_AUDIO_QUEUE_CAPACITY_PACKETS` (the user's listen had left
  12 / 17 set there), then `systemctl --user restart privyhub-companion`:
  8765 owned by the MainPID, **0 `PRIVYHUB_*`** in its environ and the
  manager's, `native-stream-status.audio_cushion` **12 / 17 source
  `profile`**, `any_override: false`.
- Runtime at the default: the four `D-BASE-T2` sessions
  (`evidence/D_BASE_T2_STREAMING_ACCUMULATION_2026-09-23.md`) ran on it.

## Status

**INSTALLED, in force.**
