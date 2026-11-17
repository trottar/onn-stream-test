# B134 — the listing's names, and practice from the load screen: the design (hashed before code)

Only with `PRIVYHUB_PARTY=1` (absent → today). Builds on B133's hold. **A game's name is run-time data only:** never
in a row, a log, a record, a test (the tests use made-up names) or git.

## Settled from the code

- **The pads while routed to the title** (`native_session_io.NativeControllerBridge`): every onn controller report
  reaches `_apply_report(player, buttons, …)` with the XInput button mask (`XUSB_START` = 0x0010), **before** the party
  route sends it to the title's virtual pad. So **the hub sees every pad's Start press there**, routed or not. Nothing
  is swallowed: **the Start press that leaves a practice also reaches the title** (the practice is over; the title is
  paused and its begin loaded again at once). A real mini game: no hook — Start goes to the title as today, untouched.

## The design

- **`party-minigames`:** each entry gains **`"title"`** — the hub library's name for the game (`_find_game_by_id`'s
  record: its display name), read when the list is asked for; nothing else in the answer changes; no row.
- **`POST party-minigame-go?practice=1`** (any other value → 400 "practice is 1"): the same as the plain go (B133:
  remembered before `ready`; the begin loaded again; route; the planned switch; release) → **`"playing"` with
  `"practice": true` and `"practice_s"`** (seconds since the practice began); **no end is read** (the watch's `ended`
  is not taken; the result never says `ended`) and **nothing is scored**.
- **A practice ends** by **the Start button on any pad** (the bridge's hook: a Start press — the bit going from up to
  down on any player's report — while a practice is `playing`; set only then, `None` otherwise = today) or by
  **`PRACTICE_S` = 90 s** of `playing`. Then **the way back** (the actor, in order): the route cleared → the planned
  switch to the board → the title paused → **the begin loaded again and read again** (a new watch with the load; the
  title runs behind the board until the start is read, then paused — B133's preparation) → `"starting"`, `"phase":
  "preparing"` then `"ready"`, **`"practices": n`**; the next go (plain or practice) as B133. As many practices as the
  players like. The board's end, the onn's END / Home during a practice or its way back → as B133 (the mini game
  given up, nothing scored, the title stopped, the board back).
- **What a practice leaves:** the title's in-game save under a setup as a real match does (each stop flushes it,
  B127 item 5) — a practice does not stop the title, so nothing until the mini game's own end.
- **Rows:** `minigame_practice` `{"n"}` at its start; **`minigame_practice_end` `{"by": "start_button" | "time",
  "practice_s"}`**; `minigame_ready` `{"prepare_s", "after_practice": true}` (the practice's end to `ready` again).
  No name in any row.

## Tests (`tests/b134_party_practice/`; B133's harness)

The list with made-up names (`"title"` present and equal to the made-up library name) and no name in any row read back;
`go?practice=1` → `playing`, `"practice": true`; the fake pad's Start (a controller report through the bridge) → back to
`preparing` → `ready`, the stream's window the board's again, the route cleared, no scores, no end read (the fake showing
an end screen through the practice changes nothing); the practice time alone (scaled) → the same; three practices then
a real go → scored as today; Start during a real mini game → nothing on the hub; END from the board and END / Home from
the onn during a practice and during its way back (B114's concurrent calls), nothing left running; the flags absent →
HEAD's answers.
