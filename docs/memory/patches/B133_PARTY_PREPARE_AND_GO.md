---
memory_schema: 1
as_of: 2026-11-17
baseline_commit: 73284310 (this repo)
---

# B133 — the hub prepares the title behind the board and hands over on the board's go (PRIVYHUB_PARTY=1)

**Result:** `evidence/B133_PARTY_PREPARE_AND_GO_2026-11-17.md`.

- **Files:** `companion/party_minigame.py` (`start(hold=)`, `_held_steps` / `_prepare` / `_handover` / `go`, the phase
  in the result, the bounds for a held start, the onn's Home / RESUME during it), `companion/h7_minigame.py`
  (`MiniGame.reload`: the begin again, the watch kept), `companion/plugins/games.py` (`hold=1` on the start; `POST
  party-minigame-go`), `tests/b133_party_prepare_go/` (new), `tests/b114_party_minigame_hang/b114_scenario.py` (the
  `hold` / `practice` modes, `QUIET`, the `today` mode's go), `tests/b111_party_board/test_b111.py` (its fake hub's held answers, B135's counts); `evidence/b133_2026-11-17/b133.diff` (applies on
  `73284310`; it carries B134's hunks in `party_minigame.py` too).
- **Switch:** `PRIVYHUB_PARTY=1` (with `PRIVYHUB_H7=1`); absent → today; a start without `hold` → today's order, rows
  and answers.
- **Rollback:** `git apply -R` b134.diff, then b133.diff.
