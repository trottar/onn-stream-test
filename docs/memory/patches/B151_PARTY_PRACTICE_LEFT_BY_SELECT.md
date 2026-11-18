---
memory_schema: 1
as_of: 2026-11-18
baseline_commit: 58bc6c42 (this repo)
---

# B151 — a practice is left by Select, not Start (PRIVYHUB_PARTY=1)

**Result:** `evidence/B151_PARTY_PRACTICE_LEFT_BY_SELECT_2026-11-18.md`.

- **Files:** `companion/party_minigame.py` (`_select_hook` in place of `_start_hook`: a Select press on any pad →
  `"by": "select_button"`; Start not looked at), `companion/native_session_io.py` (`_party_select_down`, written only
  while B141's Select hold is on; `party_select_down(player)`; `set_party_route` keeps it across its own neutral
  writes), `companion/native_stream.py` (`PARTY_BANNER_TEXT` = "PRACTICE — press Select (Share) to go back");
  `tests/b151_party_select_leaves/` (new), `tests/b114_party_minigame_hang/b114_scenario.py` (the practices left by
  Select; the new `select151` mode; the `b143` mode's practice by Select + Start, so its HEAD runs still leave it),
  `tests/b134_party_practice/test_b134.py`, `tests/b145_party_small_things/test_b145.py`,
  `tests/b144_party_practice_banner/test_b144.py`, `tests/b147_party_band_inside/test_b147.py` (the new words; the box
  inside a 4:3 picture's columns in place of "under half the frame"); `evidence/b151_2026-11-18/b151.diff`.
- **Switch:** behind `PRIVYHUB_PARTY=1` (and `PRIVYHUB_H7=1`); absent = today (the users' own sessions byte for byte
  with the flags set: the hook and the record exist only inside a held party mini game).
- **The board's repo:** not touched (the PC side's `674407d` already says Select on the load screen).
- **Rollback:** `git apply -R evidence/b151_2026-11-18/b151.diff`.
