---
memory_schema: 1
as_of: 2026-11-17
baseline_commit: 498ff031 (this repo)
---

# B137 — nothing a player presses reaches the title before the go (PRIVYHUB_PARTY=1)

**Result:** `evidence/B137_PARTY_NO_PRESS_BEFORE_GO_2026-11-17.md`.

- **Files:** `companion/party_minigame.py` (`_prepare`: paused, the mute, the watch's load, `_advance` — 2 ×
  `FRAMEADVANCE` 60 ms apart — the mute off, the paused read; `_handover`: no second load when the title has not run
  since its begin was loaded, the label mask off before the resume; `_way_back`: paused first; the end's steps release
  the mute; the row `minigame_frame_advance`), `companion/h7_minigame.py` (`mask_label`, `LABEL_BOX`,
  `start(mask_label=)`, `label_mask(on)`), `companion/native_session_io.py` (`party_mute(on)`, `_party_mute` read in
  `_apply_report` under the meta lock), `tests/b137_party_no_press/` (new), `tests/b114_party_minigame_hang/b114_scenario.py`
  (the `nopress` / `nopress_head` modes), `tests/b133_party_prepare_go/test_b133.py` (its two row lists for B137's
  order); `evidence/b137_2026-11-17/b137.diff` (applies on `498ff031`).
- **Switch:** `PRIVYHUB_PARTY=1` (with `PRIVYHUB_H7=1`) and a held start (`hold=1`); either flag absent → today; a
  start without `hold` → B110's order; the HTTP `h7-start` never masks; `_party_mute` False → the bridge as today.
- **Rollback:** `git apply -R evidence/b137_2026-11-17/b137.diff` (B133's order back: the title resumed behind the
  board until its start is read, the begin loaded again at the go).
