# PP-H3c part 1 — the bench gate (2026-11-18 02:54-02:58Z, unattended): MET

- **(a)** In a scratch copy of the board's tree (Godot headless, its folders in scratch, the copy removed after):
  `checks/hub_minigame_check.gd` **PASS (81 assertions)**; `checks/step25_before_minigame.gd` **PASS (107
  assertions)**. The board's repo status unchanged (0 lines).
- **(b)** The rules folder as H7-V5b left it: both setups' slot 1, specs, begins and sidecars as read (`pre/rules_check.md`).
- **(c)** Before: 228 files, no `.state8`; `party.jsonl` 478 rows, `h7_results.jsonl` 240 (`pre/before.txt`).
- **(d)** Both drop-ins; twenty lines (added only the two bench flags); MainPID serving.
- **(e)** The board launched (200, `active`, `paused`, `godot`) and released; the list `[(2, True), (4, True)]`. One
  held T88 start, seats 1,2, `bench=1`: `minigame_launch` `cheat` / `profile_matches` true; **the two keys `"false"`**
  read 0.16 s after it; `minigame_frame_advance` `frames` 2, `batches` 2, `moved` 0.5752, **`changed` true**, `mute_ms`
  338.5, **`paused` true**; `watching` `begin` setup, **no `label_mask`**; `recognised` true at the first read (1.0 s,
  start 0.0118); `minigame_ready` **`prepare_s` 1.277**; **the paused proof PAUSED 4 / 4** from the watch row to the go;
  no route / stream before the go; the go `taken`, `held_s` 2.908, **no `minigame_reloaded`**; `playing`; the kept end
  P1 by hand (the scratch removed, `.state8` 0) → **`end_P1` [1, 0]**; the end (`by` board); the board quit by F10,
  exit code 0; nothing left. Pictures `p1e_001`-`p1e_004` in the git-ignored `runtime/pph3c_frames/` (`DISPLAY` set;
  the first file there).
