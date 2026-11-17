# B135 — the board's script: choose → load, ready or practise → play: the design (hashed before code)

My two files in the board's repo only (`minigames/hub_minigame.gd`, `checks/hub_minigame_check.gd`), from the tree at
`d321b2d` (the PC side's `aa58ec6c…` + Cowork's note). The presenter, the picker and the rules are the PC side's — not
touched. No real game's name anywhere: names come from the hub at run time; the check uses made-up ones.

## The seam (the PC note's names; each called only if the stage has it — `stage.has_method`)

`play(players)`:
1. The hub's list (as today); `fitting` = the entries for this many players, sorted by id; none → a draw (today).
2. **The cards:** seeded from the game's seed (today's generator, `_played` as today): two distinct entries when two or
   more fit (the first two of a seeded shuffle), else the one; each card `{"title": <the entry's title, or "">}`.
3. **The choice:** if the stage has `choose_minigame`: `await stage.choose_minigame(cards, players)` → `{"card": 0 | 1
   | -1}`; `-1` (Random, only with two cards) → the seeded pick between the two; anything else / no method → **today's
   seeded pick** among all that fit (so a stage without the seam plays exactly as today).
4. **`announce_minigame`** — unchanged (the rules call it; the script does not).
5. **The screens and the hold** — only if the stage has **all four** of `show_minigame_loading`,
   `set_minigame_loading_ready`, `minigame_loading_choice`, `hide_minigame_loading`: `stage.show_minigame_loading(title,
   players)`; the start with **`&hold=1`**; then a poll every `POLL_SECONDS` (1.0 s) — and the choice read every
   `CHOICE_SECONDS` (0.25 s) in between — while the hub answers `"starting"`: `set_minigame_loading_ready(phase ==
   "ready")` whenever it changes; **the go** (`POST party-minigame-go`, with `?practice=1` for `"practice"`) **once the
   choice is `"start"` or `"practice"` and the hub's phase is `"ready"`** — never before, no time limit on the wait;
   at the first `"playing"` → `hide_minigame_loading()`. **A practice** (`"playing"` with `"practice": true`): the
   board's TV goes to the title; when the hub's answer is `"starting"` again → `show_minigame_loading(title, players)`
   again, the wait starts over (the ready marks clear on the PC side's show), any number of times; a practice gives
   the rules nothing. A plain go's `"ended"` gives the scores (today). Without the four methods: today's start (no
   `hold`), today's loop.
6. **The pads and the frame rate:** the `PadGate` (swallows joypad input, caps the frame rate at `IDLE_FPS`) is in the
   tree **only while the TV is on the hub's game** — added at each go (plain or practice), removed when the hub is back
   at `"starting"` (a practice's end) and at the end; never while the board's screens are up. Without the screens:
   today (the gate from the start).
7. **Bounds:** `LIMIT_SECONDS` counts only time spent `"playing"` (not the ready check); `MISSED_POLLS` as today;
   **every way out hides the load screen** (a draw, `given_up`, a refusal, no hub, the limit) — `hide` called once, with
   nothing shown it does nothing (the PC side's contract). `FIRST_WHERE` / `FIRST_FOR` untouched.

## The check (`checks/hub_minigame_check.gd`, headless; a made-up hub on loopback with made-up names; a made-up stage)

The old cases PASS; added: one card and two cards (the cards' titles = the made-up names); card 0, card 1, Random (the
same seed → the same game; the start's `id` the chosen one); the load screen shown with the chosen name and the
players; `set_minigame_loading_ready` false then true following the hub; no go while the choice is `""` however long
(seconds of polls), the plain go at `"start"`, the practice go at `"practice"`, neither before the hub is `ready`; `hide`
at `"playing"` and on `given_up`, a refusal, no hub; three practices in a row (no scores, the load screen shown again
each time) then a real one scored; the pads not swallowed while the board's screens are up, swallowed while the hub's
game is on; the frame cap only then; a stage without the methods → as today (no `hold`, the old cases). The PC side's
`checks/step8_modules.gd` PASS on the tree (read only, in a scratch copy).
