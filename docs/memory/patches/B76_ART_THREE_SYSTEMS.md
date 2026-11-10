---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: a96c816c
---

# B76 — artwork and details for N64 / PS2 / GameCube through the hub's fetcher (NOT adopted; `PRIVYHUB_ART_SYSTEMS=1`)

**Result:** `evidence/B76_ART_THREE_SYSTEMS_2026-11-09.md`.

- **Apply:** `git apply evidence/b76_2026-11-09/b76.diff` (first of queue AC's six, on HEAD). Applied to the tree, uncommitted.
- **Live:** nothing until the knob is set. With `PRIVYHUB_ART_SYSTEMS=1` in a command's environment,
  `tools/update_game_metadata.py --dry-run` reports matched / unmatched per system (RetroArch's whole system lists
  only), and the tool without `--dry-run` fetches the three systems' art and details as PS1's (each matched title's
  database name is sent). The onn needs nothing.
- **Off:** the knob absent (any value but `1`).
- **Writes outside the code:** the provider's per-system list cache, `metadata.json`, `media/games/box_art/<id>.png`
  — only when the tool runs with the knob.
- **Rollback:** `git apply -R` in the order 81 … 76. Fetched art and records stay (they are kept by later runs).
