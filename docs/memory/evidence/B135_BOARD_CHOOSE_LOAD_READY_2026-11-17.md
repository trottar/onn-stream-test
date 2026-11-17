---
memory_schema: 1
as_of: 2026-11-17
status: BUILT (session B, queue AU) — the board's script: choose → load, ready or practise → play, in my two files of the board's repo (uncommitted there; the user commits). With a stage that has the PC side's screens: one or two seeded cards from the hub's list (Random with two), the load screen with the chosen name while the hub prepares (hold=1), the hub's readiness on it, the go — plain or practice — only once the players' choice is made and the hub is ready, with no time limit; hidden at each playing and on every way out; practices any number of times; the pads and the board's frame rate only taken while the hub's game is on; LIMIT_SECONDS only while playing. A stage without the screens: as before. The check PASS 81 (was 40) three runs; the PC side's step8 PASS 210 (read only); mutations 2 / 2. Nothing adopted; nothing committed in either repo
---

# B135 — the board's script: choose → load, ready or practise → play

Queue: `handoffs/QUEUE_2026-11-17AU.md` §B135; the seam: `handoffs/PRIVYPARTY_PC_NOTE_SELECT_LOAD_JOIN_2026-11-17.md`.
The directory is `b135_2026-11-17/`: the design + `.sha256` (hashed 19:35:30Z, before any code), `b135_board.diff` (the
two files against the board's `d321b2d`), `board_files_before.txt` / `board_files_after.sha256`, `check_runs.txt`,
`tests_mutations.txt`, the checks, `manifest.sha256`. **The board's repo:** only `minigames/hub_minigame.gd` and
`checks/hub_minigame_check.gd` changed (uncommitted); the presenter, the picker and the rules not touched;
`FIRST_WHERE` / `FIRST_FOR` unchanged. The checks ran in a scratch copy of the tree under Godot headless (Godot's
folders redirected to scratch). No real game's name anywhere: the names come from the hub at run time; the check uses
made-up ones.

## Built (`minigames/hub_minigame.gd`, sha256 `e580c3e1…`; was `d9e2e6ec…`)

- **The cards** — when the stage has `choose_minigame`: the first card today's seeded pick among the games that fit,
  the second (when two or more fit) a seeded pick from the rest; each `{"title": <the hub's name>}`; `await
  stage.choose_minigame(cards, players)` → `{"card": 0 | 1 | -1}`; **-1 (Random) the seeded pick between the two**;
  anything else today's pick. Who holds the cursor is the presenter's.
- **The screens** — when the stage has all four of `show_minigame_loading`, `set_minigame_loading_ready`,
  `minigame_loading_choice`, `hide_minigame_loading`: the load screen shown with the chosen name and the players; **the
  start with `hold=1`**; the result read every second and the players' choice every 0.25 s; **`set_minigame_loading_ready`
  following the hub's phase**; **the go** (`party-minigame-go`, `?practice=1` for `"practice"`) **once the choice is
  `"start"` or `"practice"` and the hub's phase is `"ready"` — never before, no time limit**; `hide_minigame_loading`
  at the first `"playing"` and on every way out (a draw, a give-up, a refusal, the hub silent, the limit). **A practice:**
  when the hub is back at `"starting"`, the load screen shown again and the wait starts over; the rules get nothing
  until a plain go's `"ended"`.
- **The pads and the frame rate:** the gate (pads swallowed, `IDLE_FPS`) **from the go until the hub is back at
  `"starting"` and at the end** — never while the board's screens are up. **`LIMIT_SECONDS`** counts only the time the
  TV is on the hub's game.
- **`announce_minigame`:** the picker's, unchanged (called once before `play()`); the chosen name is on the load screen.
- **A stage without the screens:** today's pick, today's start (no `hold`), today's loop and gate.

## The check (`checks/hub_minigame_check.gd`, sha256 `76018a20…`; was `b016167d…`)

**PASS (81 assertions), three runs** (was 40; the hub's B111, which runs this check in a scratch copy with its own stand-in hub and against B111's fake hub, updated for it — its fake hub answers the held starts, its counts 81 / 56; two of my new assertions read the stand-in's own records and go through `_expect_asked` like the others of that kind): the old cases unchanged and green; added with a made-up stage and a
stand-in hub that prepares (two `preparing` answers, then `ready`), takes the go only when ready, plays a practice for
two answers then prepares again, plays a plain go to `ended`: two cards with the made-up names (seeded order) and one
card; card 0, card 1, Random (the start's id = the seeded pick computed the script's way); the start held; the load
screen shown with the chosen name; readiness false then true; **no go while the choice was `""` for 16 reads with the
hub ready**; the players ready before the hub → the go waits; **three practice goes then a plain one, the load screen
shown 4 times and hidden at each playing, every go with the hub ready, scored once**; the hub giving up, refusing,
going silent, absent → a draw with the load screen down; **the pads reaching the board while its load screen is up and
swallowed while the hub's game is on**; the frame rate the board's own while its screens are up and `IDLE_FPS` only
while the hub's game is on; no gate left. **The PC side's `checks/step8_modules.gd`: PASS (210 assertions)** on the
same tree, read only.

**Mutations** (`tests_mutations.txt`): the go sent without waiting for the hub's ready → 4 fail; the gate up from the
start with the screens → 3 fail.

**The user, in the board's repo:** `git add minigames/hub_minigame.gd checks/hub_minigame_check.gd && git commit -m
"Hub mini game: choose, load screen, ready or practise, then play - the hub prepares behind the board, with its check"`.
