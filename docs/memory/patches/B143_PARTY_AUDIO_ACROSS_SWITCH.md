---
memory_schema: 1
as_of: 2026-11-18
baseline_commit: 246c67da (this repo)
---

# B143 — the sound across a party's planned switch (PRIVYHUB_PARTY=1)

**Result:** `evidence/B143_PARTY_AUDIO_ACROSS_SWITCH_2026-11-18.md`.

- **Files:** `companion/native_session_io.py` (`NativeAudioStreamer`: each sender run records where it stopped;
  `party_continue_next(pid)`, `_audio_start_counters`, `_audio_note_sent`; both loops start from `_audio_start`),
  `companion/audio_codec.py` (`run_opus_sender`: the same start and record), `companion/party_minigame.py`
  (`_arm_switch` around every planned switch's `ns.start`; the layer's docstring lines for B143-B145),
  `tests/b143_party_audio_switch/` (new: `receiver_model.py`, `test_b143.py`),
  `tests/b114_party_minigame_hang/b114_scenario.py` (the `b143` mode); `evidence/b143_2026-11-18/b143.diff`.
- **Switch:** only the party layer arms it (`PRIVYHUB_PARTY=1` and `PRIVYHUB_H7=1`); unarmed, every start begins at
  sequence 0 and timestamp 0 as today (the datagrams byte for byte).
- **Rollback:** `git apply -R evidence/b143_2026-11-18/b143.diff` (after B145's and B144's).
