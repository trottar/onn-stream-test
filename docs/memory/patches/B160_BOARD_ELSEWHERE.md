---
memory_schema: 1
as_of: 2026-11-18
baseline_commit: bb9dcd5 (the board's repo)
---

# B160 — the hub mini game says it is played elsewhere (the board's repo, my two files)

**Result:** `evidence/b160_2026-11-18/RECORD.md`.

- **Files (the board's repo):** `minigames/hub_minigame.gd` (`const ELSEWHERE := true`; the header's Start → Select),
  `checks/hub_minigame_check.gd` (the assertion); `evidence/b160_2026-11-18/b160.diff`.
- **Switch:** none needed — the picker already believed a script's own `ELSEWHERE` (step28); the board guessed true
  from `FIRST_WHERE` before, so its behaviour is the same, now said rather than guessed.
- **Rollback:** `git -C <board repo> apply -R <this repo>/docs/memory/evidence/b160_2026-11-18/b160.diff`.
