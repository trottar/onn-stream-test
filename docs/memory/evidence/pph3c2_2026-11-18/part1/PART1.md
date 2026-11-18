# PP-H3c (second try) part 1 — the bench gate (2026-11-18 03:32-03:36Z, unattended): MET

- **(a)** A scratch copy of the board's tree, Godot headless, its folders in scratch (removed after):
  `checks/hub_minigame_check.gd` **PASS (81 assertions)**; `checks/step25_before_minigame.gd` **PASS (107
  assertions)**; the board's repo status 0 lines.
- **(b)** The rules folder as H7-V5b left it (`pre/rules_check.md`).
- **(c)** Before: 228 files, no `.state8`; `party.jsonl` 500 rows, `h7_results.jsonl` 246.
- **(d)** Both drop-ins; **twenty lines** (only the two bench flags added); MainPID serving.
- **(e)** The board launched (200, `active`, `paused`, `godot`) and released; the list `[(2, True), (4, True)]`; one held
  T88 start, seats 1,2, `bench=1`: `cheat` / `profile_matches` true; **the two keys `"false"`**; frame advance 2
  frames, 2 batches, moved 0.5241, **`changed` true**, mute 338.8 ms, **`paused` true**; no `label_mask`; `recognised`
  at the first read (1.0 s); **`prepare_s` 1.268**; **PAUSED 4 / 4**; the go, no route before it, **no
  `minigame_reloaded`**; the kept end P1 by hand (scratch removed, `.state8` 0) → **end_P1 [1, 0]**; the board quit by
  F10, exit 0.
