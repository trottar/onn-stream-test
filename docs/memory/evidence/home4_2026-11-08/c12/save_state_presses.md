# The "Save failed" explained (read 08:01Z)

The user sent a photo of the onn's dialog: "Game State" — `HTTP 503: {"ok": false, "error": "Save states are not
available for a PS2 session"}` (the photo is not copied: it shows titles).

The companion's journal: `POST /plugins/games/save-state` → **503** at 07:37:53Z, 07:41:01Z and 08:00:35Z. So every
"save" so far was **PrivyHub's own save-state button**, which B49 turns off for a PS2 session by design (the
`ps2_session` row: `save_states: off`; PS2 save states through PINE are the user's yes, LATER). No in-game save to the
memory card was attempted; the card unchanged is consistent with that. **`attempt1.md`'s "Save failed" is this, not a
memory-card failure** — B50's card is not implicated. C12 (the game's own save) still to run.

## Stage 6 (the user's "Stage 6", 08:01:23Z)
- At 08:01:23-08:03:46Z `Mcd001.ps2` still `69358f81…` (the post-format value); the session resumed 08:01:37Z
  (`PS2 resume: hotkey`). PCSX2 may hold a card write until the file is closed: the card is read after the Stop.
- The user told: Back, Stop, relaunch, load (B stage 6).

## The user's lines at 08:04Z (verbatim): "There is no save" / "We never do it like this? Why are you changing it from ps1 and others"
- State: the 07:59:07Z launch still running (no Stop, no relaunch since); both cards `69358f81…` (the post-format
  value): no in-game save has reached the card in any launch (07:57:51Z exit flushed nothing new).
- **The user's requirement (to B, recorded as said):** saving a PS2 game should work the way it does for PS1 and the
  other systems — PrivyHub's SAVE button (a save state). Today B49 answers it with 503 "Save states are not available
  for a PS2 session" by design; PS2 save states through PINE were the user's "yes, later". This remark moves that
  question up: it re-plans C12 (the as-built cell is the game's own memory-card save). Asked: run the in-game save now,
  or leave C12 not met tonight.

## The user's answer (08:0xZ, verbatim): "2"
**C12: not run → NOT MET** (the user's choice: skip tonight; PS2 stays bench-only until B makes PrivyHub's SAVE button
work for PS2). So G-A14's condition (C11 and C12 met) fails: fifteen lines at the close.
