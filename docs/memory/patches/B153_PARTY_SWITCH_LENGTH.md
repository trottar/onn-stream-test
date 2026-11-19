---
memory_schema: 1
as_of: 2026-11-18
baseline_commit: d7a99b62 (this repo)
---

# B153 — the planned switch's length (PRIVYHUB_PARTY=1)

**Result:** `evidence/B153_PARTY_SWITCH_LENGTH_2026-11-18.md`.

- **Files:** `companion/native_stream.py` (`party_switch_next` / `_take_party_switch`; `_stop_locked(fast)`;
  `_kill_managed_process_now`; `_start_session_io_locked`, called before the encoder's check when armed, after it
  otherwise), `companion/native_session_io.py` (`stop_stream(now)`, `NativeAudioStreamer.stop(now)`,
  `_stop_linux_locked(now)`, `_kill_process_now`), `companion/party_minigame.py` (`_arm_fast` around every planned
  switch; the layer's docstring); `tests/b114_party_minigame_hang/b114_scenario.py` (the `b153` mode),
  `tests/b153_party_switch_length/` (new); `evidence/b153_2026-11-18/b153.diff`.
- **Switch:** behind `PRIVYHUB_PARTY=1` (and `PRIVYHUB_H7=1`): only the party layer arms it, around its planned switch.
  Absent = today; with the flags set every other start (the users') takes HEAD's calls in HEAD's order.
- **Rollback:** `git apply -R evidence/b153_2026-11-18/b153.diff` (after B155's, if applied).
