# B151 — a practice is left by Select, not Start (design, written and hashed before any code)

Queue: `handoffs/QUEUE_2026-11-18AZ.md` §B151. Baseline `58bc6c42`. Behind `PRIVYHUB_PARTY=1` (and `PRIVYHUB_H7=1`);
absent = today byte for byte.

## Settled from the code (HEAD `58bc6c42`, read before this design)

- **Where a practice's Start is seen.** Every onn controller report reaches
  `NativeControllerBridge._apply_report(player, buttons, …)`. Its first step calls the practice's report hook
  (`_party_buttons`, set by `PartyMinigame._start_hook` at a practice's hand-over, after the route and the switch, before
  the resume; `None` again at the way back and at every end) with **the onn's player and the raw button mask** — before
  B141's Select hold, before the route, before the mute. The hook takes Start (`0x0010`) going from up to down on any
  player's report (its own `last` per player, empty at the hand-over) as "leave": `practice_end_by = "start_button"`.
- **What happens to that Start on its way to the title.** Nothing is swallowed: after the hook, the hold clears only
  Select (`0x0020`), the route maps the onn's player to the title's virtual pad, and the report (Start in it) is
  written to that pad; the running title gets Start. The held-steps loop then sees `practice_end_by` and runs the way
  back: the hook cleared, Select held again (already held), the row `minigame_practice_end {"by": "start_button"}`,
  the title paused, the route cleared, the planned switch to the board, the begin loaded and read again → ready.
- **Select from a party title's launch to a real go (B141, B145).** `party_hold_select(True)` just before a held title's
  launch; from then every report's Select bit is cleared before the route and the write (a pad already holding it is
  written once without it). It stays on through the preparation, the hold, **every practice** (B145: only a real go
  turns it off) and every way back; a real go turns it off before the route and the resume; every end turns it off.
  **Today Select in a practice does nothing at all**: it never reaches the title and the hub does not look at it.
- **Select + Start in a practice today:** the hook sees Start → the practice ends (`"by": "start_button"`); the hold
  clears Select, so the title gets Start alone — RetroArch's quit pair (Select + Start) never forms; the title is
  paused and its begin loaded again at once.

## The design

1. **The hook watches Select instead of Start.** `_start_hook` becomes `_select_hook`: Select (`0x0020`, the report's
   Back / Share bit) going from up to down on **any** player's report (seated or not, as B134's Start) sets
   `practice_end_by = "select_button"` while the practice plays. **Start is no longer looked at**; it reaches the title
   as it does in a real mini game (the route and the write, unchanged).
2. **A Select already down at the hand-over does not count until it is let go and pressed again.** The hook's starting
   state per player is that player's Select **as the bridge last saw it**, not "up". The bridge keeps it while Select is
   held (B141's hold is on from the launch through every practice): `_party_select_down` — `{player: bool}` of the raw
   reports' Select bit, written in `_apply_report`'s hold branch after the hook (so the hook, reading it, sees the
   previous report's state); seeded at the hold's off → on step from the pads' last reports (route not yet set then, so
   the index is the onn's player); emptied when the hold goes off. Read by `party_select_down(player) -> bool`. The hook
   reads it for a player the first time that player reports in the practice; after that its own `last`. A bridge
   without the method (or a player never seen) → up. **The hold's on-call while already on (the way back) does not
   re-seed** (the route may still be set then).
3. **Select still never reaches the title before a real go**: B141 / B145's hold unchanged (the hook reads the raw bit;
   the hold clears it after).
4. **The time bound as it is** (`PRACTICE_S = 90.0`; `"by": "time"`).
5. **The row:** `minigame_practice_end {"by": "select_button" | "time", "practice_s"}`.
6. **The band's words: `PRACTICE — press Select (Share) to go back`** (`PARTY_BANNER_TEXT`), placed by B147's rule
   unchanged (font, size `h*30/720`, centred, the box's top at `h*5/100`, 10 px above and below, 16 px to each side,
   black @ 0.72): every pixel inside the inner 90 %. The parentheses need no escape inside the filter's quotes. The
   columns are measured from the output frame after the change (the words are longer: the box widens, still centred);
   the build fails the item if any changed pixel leaves the inner 90 % at 720p or 1080p.
7. **A real mini game, and everything outside a practice, as today:** the hook is set only at a practice's hand-over,
   as before; `_party_select_down` is written only while the hold is on (set only by the party layer). Docstrings and
   the `PRACTICE_S` comment updated to say Select.

## Tests (through the real HTTP server on loopback; B114's scenario)

- **B134's cases with Select in Start's place** (`practice` mode): practices 1 and 2 left by **the second pad's
  Select**, the third by the time → rows `select_button`, `select_button`, `time`; in each practice **a Start press
  first → still playing** (the practice goes on); a real go with Start and Select pressed → nothing on the hub; the
  ends during a practice and its way back (the way back now started by Select); the hook cleared at every end.
- **B145's cases with Select in Start's place** (`nopress` mode): the practice left by Select alone (`select_button`),
  the title not quit, no hotkey, the state folder byte-equal.
- **New `tests/b151_party_select_leaves/`** (a new scenario mode `select151` on `nopress`'s fake title and virtual
  pads): (a) **a practice left by a Select press on each pad** (four practices, pads 1-4, each `select_button`);
  (b) **Start in a practice** from each seated pad → still `playing`, **the title's virtual pad written with Start**;
  (c) **Select in no report the title gets** (no virtual pad written with `0x0020` from the launch to the real go, the
  hotkey log empty), Select + Start leaves (`select_button`) with Start written and the title alive; (d) **a Select held
  across the hand-over** (down before the practice's go, still down after it, reports repeated) → the practice goes on;
  let go and pressed again → it ends (`select_button`); (e) **the time bound** (scaled) → `"by": "time"`; (f) a real go:
  Select and Start pass, nothing on the hub.
- **The band:** B144's and B147's tests with the new words (the practices' encoder commands carry the new filter; every
  other command equals HEAD's; B147's frame test: every changed pixel inside the inner 90 % at 720p and 1080p; the
  columns reported); B144's frame test with the new words.
- **The bridge's default:** `_party_select_down` untouched with the hold off; seeded at off → on, not re-seeded on → on.
- **Mutations:** (1) the hook back on Start (`XUSB_START`, `"start_button"`) → B151's and B134's tests fail; (2) the
  seed ignored (the hook's starting state "up") → the held-across case fails; (3) the band's old words → B147 / B144 fail.
- **The flags absent → today:** B114's and B108's flag tests, B133's (HEAD's answers through the real routes).
- **The earlier party suites green** (B137's `run_others.sh` list; B111 with Godot on its own scratch copy); temp dirs
  removed.
