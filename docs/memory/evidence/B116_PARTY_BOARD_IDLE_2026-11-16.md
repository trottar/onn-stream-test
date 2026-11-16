---
memory_schema: 1
as_of: 2026-11-16
status: BUILT (session B, queue AQ) — the board idles behind the title: in the board's minigames/hub_minigame.gd only, while it waits for the hub's mini game the board draws at most 10 frames a second (Godot's own Engine.max_fps), and its own frame rate is back as soon as the wait ends — before it tells the hub the end — and whenever the wait's gate leaves the tree (every path). Its check: PASS (34 assertions, from 20), three mutations caught. Godot headless shows the setting applied and restored on every path; only the sitting can show the CPU behind the title. The board's repo: my two files edited, nothing else, nothing committed there. No title, game id, path or picture in this record
---

# B116 — the board idling behind the title (2026-11-16)

**The board's repo** at `820673c` (the user's commit of B111's two files), its tree clean before
(`b116_2026-11-16/board_repo_before.txt`). **Design** hashed 21:16:59Z, before the first edit
(`b116_2026-11-16/design.sha256`); no amendment. Godot 4.7.2 **headless only, in a scratch copy** of the board's repo
(its HEAD + the two files; `--import` first; Godot's own folders redirected) — Godot never ran in the board's repo.

## The change (`minigames/hub_minigame.gd`, +25 / −1)

- `IDLE_FPS := 10`. **B111's pad gate** (the node the script adds to the tree while it waits) now also caps the
  board's frame rate: entering the tree it remembers the board's own `Engine.max_fps` and sets 10 (never raising a
  lower cap of the board's own); `restore()` puts the remembered value back, once; **leaving the tree** — however that
  happens (removed after the end call, the scene or the tree going with it, the board quitting) — calls `restore()`.
- **The script restores it as soon as the wait ends** (a result, a give-up, the hub not answering, its own limit) —
  **before** it calls the hub's end, so the board draws at its own rate before B115's way back switches the stream to
  it. No wait (no hub, a refusal, none for the players) → never touched. No line added to the board's log.
- Physics, input and timers are not slowed (the cap is the frame rate only); the pads stay swallowed as before.

## The check (`checks/hub_minigame_check.gd`, +54 / −2): PASS (34 assertions)

`check_run.txt`: **"HUB MINIGAME CHECK: PASS (34 assertions)"**, exit 0 (was 20). New, with its own stand-in hub
recording `Engine.max_fps` at every result call and at the end call: while it waits the board draws at most 10;
its own rate is back **before the hub is told the end**; after a result (its own: none, 0) / a give-up (a board capped
at 144: 144) / **the hub not answering** (a new "silent" scenario: the result answers 500 → a draw after ten missed
polls) / **the gate torn down mid-wait** (removed from the tree 1.5 s in: the board's own rate back at once, and the
wait still comes back) the board's own value is back; a board capped at 5 keeps 5 while it waits; with no wait the rate
is never changed. Against an outside hub (`PRIVYPARTY_CHECK_HUB`) the five frame-rate assertions are that hub's (they
read the stand-in's records), like the "asked" ones: **23**.

**Mutations** (`check_mutations.txt`, by hand in the scratch copy): the cap never set → FAIL 3 of 34; the restore a
no-op → FAIL 6 of 34; no restore before the end call → FAIL 1 of 34 ("its own frame rate is back before the hub is
told the end"). The file restored and compared after.

**From this repo** (`tests/b111_party_board/test_b111.py`, two lines of expectations and the fake hub's two new
scenarios — `b116_this_repo_test.diff`): the check with its own stand-in hub → PASS (34); against this test's fake hub →
PASS (23), eight end calls (every started one), the "stopped answering" draw line; 3 runs in
`b115_2026-11-16/tests_x3.txt`.

## What headless shows, and what only the sitting can

Headless has no display, no compositor and no vsync: it shows **the setting applied while waiting and restored on every
path** — not the CPU. **Only the sitting can show** Godot's CPU behind the title: PP-H3 saw 98 % behind against 21 % in
front; with a cap of 10 the board should draw a sixth of its frames in front, so expect it **at or below its 21 % in
front** — PP-H3b records it from its status watch (`godot_cpu` while `minigame_playing`).

## The board's two files (new hashes) and the commit line for the user

- `minigames/hub_minigame.gd` — sha256 `4706a28b8028db3ef51a35d51c89321e08d3ba369c83c3f8eae8221e01e487cd` (was `644f0541…`)
- `checks/hub_minigame_check.gd` — sha256 `c09036b7fbccb8deae65fc951b21f63694569ce286d2eece354763a7dafa0617` (was `de4c9db0…`)
- Copies in `b116_2026-11-16/board_files/`, the diff `b116_board.diff` (applies on `820673c`); the board's repo after:
  exactly these two ` M` lines, `.godot/` ignored as before (`board_repo_after.txt`).
- **The user, in the board's repo:** `git -C <board repo> add minigames/hub_minigame.gd checks/hub_minigame_check.gd &&
  git -C <board repo> commit -m "Hub mini game: the board draws at 10 fps while the hub's game is on the TV, with its
  check"`.

## Files

The board's `minigames/hub_minigame.gd`, `checks/hub_minigame_check.gd` (uncommitted there); this repo's
`tests/b111_party_board/test_b111.py`; `b116_2026-11-16/`: the design and its hash, `board_repo_before.txt` /
`_after.txt`, `board_files_before.sha256` / `_after.sha256`, `board_files/`, `b116_board.diff`,
`b116_this_repo_test.diff`, `check_run.txt`, `check_mutations.txt`, redact / title checks, `manifest.sha256`;
`patches/B116_PARTY_BOARD_IDLE.md`.
