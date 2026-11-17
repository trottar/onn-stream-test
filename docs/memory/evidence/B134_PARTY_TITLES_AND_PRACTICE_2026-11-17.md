---
memory_schema: 1
as_of: 2026-11-17
status: BUILT (session B, queue AU) — the listing's names and practice from the load screen, behind PRIVYHUB_PARTY=1. party-minigames entries carry "title" (the library's name, read when asked; never in a row). Settled: every onn pad report reaches the bridge's _apply_report with its button mask before the party route sends it on, so the hub sees any pad's Start press while the pads are routed to the title — a hook there, set only during a practice; the press also reaches the title (the practice is over). Built: party-minigame-go?practice=1 → the same hand-over, nothing read, nothing scored, "playing" with "practice": true; Start on any pad or 90 s → the way back (the route cleared, the planned switch to the board, the title paused, its begin loaded and read again) → "starting" preparing → ready with "practices": n; as many as the players like; then a plain go scored as today; Start in a real mini game does nothing on the hub. Tests 5 (3 runs). Nothing adopted; nothing committed
---

# B134 — the listing's names, and practice from the load screen

Queue: `handoffs/QUEUE_2026-11-17AU.md` §B134. The directory is `b134_2026-11-17/`: the design + `.sha256` (hashed
19:35:30Z, before any code), `b134.diff` (`companion/native_session_io.py`; the practice's hunks in
`companion/party_minigame.py` are in `b133_2026-11-17/b133.diff` — the same file), `tests_mutations.txt`,
`tests_x3.txt` (queue AU's hub suites and the others), `scripts/run_all.sh`, the checks, `manifest.sha256`. Patch:
`patches/B134_PARTY_TITLES_AND_PRACTICE.md`. **No game's name in any row, log or record** — the tests use B85's made-up
fixture names and check no name reaches a row.

## Settled from the code

- **The pads while routed to the title** (`native_session_io.NativeControllerBridge`): every controller report from the
  onn reaches `_apply_report(player, buttons, …)` with the XInput button mask (`XUSB_START` 0x0010) **before** the party
  route sends it to the title's virtual pad — so **the hub sees every pad's Start press there**, routed or not. The
  hook (`_party_buttons`, `None` = today) is set only while a practice plays and cleared at its end and at every end.
  **Nothing is swallowed: the Start press that leaves a practice also reaches the title** (the title is paused and its
  begin loaded again at once, so it changes nothing that stays). In a real mini game no hook: Start goes to the title as
  today, and the hub does nothing with it.
- **What a practice leaves:** a practice does not stop the title, so nothing is flushed then; the title's in-game save
  under a setup is flushed at the mini game's own end, as for a real match (B127).

## Built

- **`party-minigames`**: each entry gains **`"title"`** — the library record's `title` (the name the onn's games list
  shows), read when the list is asked for.
- **`POST party-minigame-go?practice=1`** (another value → 400 "practice is 1"): B133's hand-over (remembered before
  `ready`; the begin loaded again; the route; the planned switch; the release); the watch stopped (nothing read) →
  **`"playing"` with `"practice": true` and `"practice_s"`**; no end taken, nothing scored.
- **Leaving a practice:** **the Start button on any pad** (a press: the bit from up to down on a player's report) or
  **`PRACTICE_S` = 90 s** of playing → the way back: the hook cleared, the route cleared, **the planned switch to the
  board**, the title paused → `"starting"`, `"phase": "preparing"` → **the begin loaded again and read again** (a new
  watch, the title behind the board until its start is read, then paused) → `"ready"`, **`"practices": n`**. Then the
  next go, plain or practice; any number of practices.
- **Rows:** `minigame_go` `"practice": true`; `minigame_playing` `"practice": true, "n"`; **`minigame_practice_end`
  `{"by": "start_button" | "time", "practice_s"}`**; `minigame_ready` `{"prepare_s", "after_practice": true}` (the
  practice's end to `ready` again). The board's end, the onn's END / Home during a practice or its way back → given up
  as B133, nothing scored.

## Tests (`tests/b134_party_practice/`, 5; B114's scenario, its `practice` mode)

| test | shown |
| --- | --- |
| the list | `{2: <made-up name>, 4: <made-up name>}` — the fixture's library names; **no name in any party row** |
| three practices | each: the go `taken` with `"practice": true` → `playing`, practice; **an end screen shown in it → still playing, no class, no scores**; the route {0: 0, 1: 1}, the stream on the title; then **the second pad's Start** (practices 1 and 2) / **the practice time** (3, scaled) → `starting`, `ready`, `"practices": 1 / 2 / 3`, the route cleared, the stream on the board, no scores; the end rows `start_button`, `start_button`, `time` |
| then a real go | Start on a pad in it → still `playing`, nothing on the hub; **ended end_P2 [0, 1]**, `"practices": 3` |
| ends in a practice | the board's end and the onn's Home / END during a practice, the board's end during its way back → given up, nothing scored, the title gone, **the Start hook cleared** |
| routes | every route < 2 s; nothing left running |

The flags absent → HEAD's answers (B133's test). **Mutation** (`tests_mutations.txt`): the Start hook never set → the
Start-button practices never end (test 1 fails). **Runs:** 3 green (`tests_x3.txt`).
