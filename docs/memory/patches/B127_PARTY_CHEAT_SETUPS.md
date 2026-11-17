---
memory_schema: 1
as_of: 2026-11-17
baseline_commit: d9e95e66 (this repo); the board's repo not touched
---

# B127 — the mini games under each title's cheat setup (PRIVYHUB_PARTY=1 + PRIVYHUB_H7=1)

**Result:** `evidence/B127_PARTY_CHEAT_SETUPS_2026-11-17.md`.

- **Files:** `companion/party_minigame.py` (the sidecar's `cheat`; the setup's begin `<game id>.<profile_id's first 12
  characters>.state` required to list it; the setup checked through the manager before anything is set aside — else
  400 "the cheat setup this mini game names is not on the hub (or its cheats changed): nothing was launched"; the
  title launched through the plugin's own launch path with the onn's Extras query; the session's `profile_id` checked
  after), `companion/h7_minigame.py` (`h7-start` under a cheat setup: the setup's own begin when the rules folder holds
  it, else the normal one; `"begin"` in the answer and the row only then), `tests/b127_party_cheat_setups/test_b127.py`
  (new), `tests/b114_party_minigame_hang/b114_scenario.py` (the harness's `cheat` and `cheat_today` modes);
  `evidence/b127_2026-11-17/b127.diff` (applies on `d9e95e66`).
- **The sidecar (A writes it):** `{"players": 2, "scores": {…}, "cheat": {"source_index": n, "enabled_cheat_indexes":
  [...], "profile_id": "<the setup's id>"}}` — the three values exactly as `POST /plugins/games/cheat-profiles?id=<game
  id>` answers them for the setup; no cheat name.
- **Switch:** `PRIVYHUB_PARTY=1` and `PRIVYHUB_H7=1` (the party routes) / `PRIVYHUB_H7=1` (`h7-start`); either absent →
  today; a sidecar without `cheat` and a session without a setup → today's answers and rows.
- **Rollback:** `git apply -R` the diff (no data written by the code beyond today's: the launch makes no new setup — a
  setup not on the hub is refused before the launch).
