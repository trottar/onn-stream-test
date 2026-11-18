# B141 — design, written before any code (hashed: `design.sha256`, the time in `design_hashed_at.txt`)

Queue: `handoffs/QUEUE_2026-11-17AW.md` §B141. Behind `PRIVYHUB_PARTY=1` (with `PRIVYHUB_H7=1`); either flag absent →
today.

## The pairs (the hub's configs: the persistent `retroarch.cfg` and every session config; the virtual pads' autoconfig adds none)

`input_enable_hotkey_btn = "6"` (Select) with `input_load_state_btn = "4"` (L1: load state), `input_save_state_btn =
"5"` (R1: save state), `input_exit_emulator_btn = "7"` (Start: quit), `input_pause_toggle_btn = "9"` (R3: pause
toggle). A paused core still takes them. Behind the board's screens, under a cheat setup, Select + L1 / R1 would load
or save over the setup's own slot, Select + R3 resume the title, Select + Start quit it.

## The rule

The bridge: **`party_hold_select(on)`** — while on, `_apply_report` clears `XUSB_BACK` (the pad's Select, which the
bridge writes as `BTN_SELECT`, RetroArch's button 6) in every report before it is routed and written; every pad written
once with Select up when it goes on. The companion's own meta presses (the forced buttons) are not reports: untouched.
`_party_hold_select = False` = today.

**On** from just before a party title's launch (a held start: `party-minigame-start?…&hold=1`) to the go (off before
the route and the resume), and again from the moment a practice ends (its way back) to the next go; **off** at every
end (the end's steps). The board never uses Select (A, B, Y, the d-pad, Start). A start without `hold`: unchanged.

## Tests (the real HTTP server; B137's `nopress` scenario)

The fake RetroArch logs a hotkey whenever a virtual pad shows Select with L1, R1, Start or R3 together (running or
paused, as RetroArch polls them). During the preparation and the hold, Select + each paired button from every pad
through the bridge → no virtual pad's Select written down, the fake's hotkey log empty, the fake's state files
byte-equal; on a practice's way back the same; **after the go** Select passes (the route's pad shows it); END / the
board's end → the hold off; the flags absent → today.
