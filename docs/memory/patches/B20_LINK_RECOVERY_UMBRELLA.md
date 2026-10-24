---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: 7f3f71d
---

# B20 — `PRIVYHUB_LINK_RECOVERY=1`, one umbrella for the six stack lines

**Result: BUILT; `tests/link_recovery` 7 green; absent proven (AST, three files); NOT ADOPTED; no live run.** Record:
`evidence/B20_LINK_RECOVERY_UMBRELLA_2026-10-24.md`. The adoption: `patches/G-A4_LINK_RECOVERY_ADOPTION_PREPARED.md`
(PREPARED only). Nothing committed.

- **Built:**
  - `companion/link_recovery.py`: the umbrella implies exactly the six (`=1`); an explicit line wins;
  - `apply` sets them into the process environment before the first read, at both import-time readers (`plugins/games.py`,
    `games/emulator_manager.py`);
  - a `link_recovery_config` recovery row;
  - `tools/e3_state.py` prints `link_recovery` when the service carries the umbrella.
- **Tests:** the umbrella alone = the six by hand in every module's reader and in fresh processes; an explicit `0`
  wins; absent → nothing read.
- **Files:** `companion/link_recovery.py` (new), `plugins/games.py`, `games/emulator_manager.py`, `tools/e3_state.py`,
  `tests/link_recovery/` (new).
- **Rollback:** remove the umbrella line; or revert the files above.
