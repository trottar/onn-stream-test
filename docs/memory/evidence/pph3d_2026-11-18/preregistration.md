# PP-H3d — pre-registration (hashed before part 1; nothing perceptual; nothing adopted)

Task: `handoffs/PP-H3D_SOLO_SOUND_BANNER_TASK.md` — B146's sketch (`SESSION_B_DONE_2026-11-18AX.md` §"PP-H3d") with
Cowork's changes 1-8, on PP-H3c's task (v3). T88 = H7's 2-player PS1 title under its cheat setup. The user alone with two
pads paired to the onn. Both bench flags for the task only.

**Stage 1 (read before this hash, 06:31-06:32Z):** the window; queue AX committed (`7700bc27`), clean; B146's six greps
and B142's ten → 1 each; the board's repo clean at **`e0ce8c4`**, `f8d92e38` its ancestor, B's two files
`a1e648f3…` / `95eb6f89…`, the five methods 5, `first_here` 1, the `cards %d, chose` lines 3; adb the onn a
`device`, `--check` ok, the APK CONFIRMED; before: 228 files, no `.state8`; N_HB 1652, N_ENC 59862.

**Part 1 — the gate (on the board's tree at `e0ce8c4`):** (a) in a scratch copy, Godot headless —
`checks/hub_minigame_check.gd` **PASS (89)**, `checks/step25_before_minigame.gd` PASS, `checks/step8_modules.gd` PASS,
and every check file changed since `f8d92e38`: hub_minigame_check.gd step10_camera.gd step11_features.gd step12_effects.gd step14_motion.gd step15_scenery.gd step18_people.gd step20_comforts.gd step21_endings.gd step22_fog_and_fixes.gd step23_wrap_and_fog.gd step24_numbers.gd step25_before_minigame.gd step26_sound_and_ready.gd step7_playable_loop.gd step8_modules.gd step9_witch_hill.gd — each PASS; (b) the rules folder as H7-V5b left it; (c) the
before listing; (d) both drop-ins, twenty lines; (e) one held T88 start on the bench (`bench=1`) → `ready` (the two
keys, a frame-advance row `changed` / `paused` true, no `label_mask`, PAUSED every second to the go) → the go, no
`minigame_reloaded` → the kept end P1 by hand → `end_P1` [1, 0]; the board closed. **Any FAIL → no line asks the
user to pick up a pad.**

**The streamed self-proof** (after the user's "ok" to the pads-down line): as PP-H3c's — ready behind the board, no
route / stream before the go, the capture the board's window, the go → `minigame_stream` `switched` / `planned`
true, the end → the board back.

**The cells (MET = part 1 and all of these):**
- **S — the sound after every planned switch:** for each `minigame_stream` row `"switched": true` at T (`"seconds"`
  s), among the onn's heartbeat rows after N_HB: a row with `audio_queue_depth` > 0 within 4 s after T, and from that
  row to the next switch's start (its T − its seconds) `audio_underruns` rising ≤ 20 per row.
- **B — the banner:** among the `encoder argv:` lines after N_ENC, the one written after the practice's
  `minigame_stream` (window minigame, after a `minigame_go` `"practice": true`) contains `PRACTICE — press Start to
  go back`; every other does not (the count = the practices, 1).
- **L — the board's log:** the newest party log's `PrivyParty: hub mini game:` lines in order: `cards 1, chose 0`,
  `practice`, `start`, then `scores [a, b] for seats 1,2` with the hub's `end_P*` scores; no name.
- **P — Select + R1 in the practice:** every file of the states, saves and T88's cheat setup before = after (sha256).
- **LS — the load screen at the practice's end (the rows' order):** `minigame_playing` `"practice": true` ≥ 2 s before
  `minigame_practice_end` `"by": "start_button"`; then the way back's `minigame_stream` (board), `minigame_ready`
  `"after_practice": true`, and no `minigame_go` before it.
- **F** — PAUSED at every proof second from each watch row to its go; no `minigame_reloaded`. **R** — `recognised`
  true for each preparation. **S (one card)** — as L's first line and the two-player token. **PS** — `"by":
  "start_button"`, no `minigame_ended` inside the practice. **M** — the real match: `minigame_ended` with an end
  class and scores, the board's log crediting that seat. **E** — END: everything ended. **U** — the setups' slots and
  pictures and every normal state and save before = after (in-game saves recorded, not a cell). **W** — every party
  launch's config carries the two keys `"false"`. (H dropped: no Home / RESUME.)

**Recorded, no bar:** the user's words (the joining step's fit; the two questions); each `prepare_s`, `held_s`,
`mute_ms`, each switch's `seconds`; `audio_lost_packets`, `audio_rx_packets`; the window's pictures per preparation
in the git-ignored `runtime/pph3d_frames/`.
