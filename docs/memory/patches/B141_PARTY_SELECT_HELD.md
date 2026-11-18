---
memory_schema: 1
as_of: 2026-11-18
baseline_commit: c1a66bc9 (this repo) + B139's and B140's diffs
---

# B141 — Select is not passed to a held title (PRIVYHUB_PARTY=1)

**Result:** `evidence/B141_PARTY_SELECT_HELD_2026-11-17.md`.

- **Files:** `companion/native_session_io.py` (`party_hold_select`, `_party_hold_select`, the Select bit cleared in
  `_apply_report` while it is on), `companion/party_minigame.py` (`_hold_select` on before a held title's launch, off at
  the go, on at a practice's way back, off at every end; the layer's docstring lines for B139-B141),
  `tests/b141_party_select_held/` (new), `tests/b114_party_minigame_hang/b114_scenario.py` (the fake's hotkey log, the
  Select pairs case); `evidence/b141_2026-11-17/b141.diff` (applies after b140.diff).
- **Switch:** as B139; `_party_hold_select` False → the bridge as today.
- **Rollback:** `git apply -R evidence/b141_2026-11-17/b141.diff`.
