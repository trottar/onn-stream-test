---
memory_schema: 1
as_of: 2026-11-18
status: BUILT (session B, queue AW) — Select is not passed to a held title, behind PRIVYHUB_PARTY=1 (and PRIVYHUB_H7=1). The pairs (the hub's retroarch.cfg and every session config; the virtual pads' autoconfig adds none): Select (button 6, the hotkey button) + L1 load state, + R1 save state, + Start quit, + R3 pause toggle — a paused core still takes them. From a held title's launch to the go, and on every way back from a practice, the bridge clears Select from every pad's report (a pad holding it is written once without it); from the go on as today; every end releases it. Tests 4 (x3); mutation 1 / 1. Nothing adopted; nothing committed
---

# B141 — Select is not passed to a held title

Queue: `handoffs/QUEUE_2026-11-17AW.md` §B141 (my AV item 3). The directory is `b141_2026-11-17/`: the design +
`.sha256` (hashed 00:25:47Z, before any code), `b141.diff` (on B140's), the checks, `manifest.sha256`; the runs in
`b139_2026-11-17/`. Patch: `patches/B141_PARTY_SELECT_HELD.md`. Nothing started.

## The pairs (read from the configs)

`data/games/retroarch/retroarch.cfg` and every session config: `input_enable_hotkey_btn = "6"` (Select — the bridge
writes the onn pad's Select as `BTN_SELECT`, RetroArch's button 6) with `input_load_state_btn = "4"` (L1),
`input_save_state_btn = "5"` (R1), `input_exit_emulator_btn = "7"` (Start), `input_pause_toggle_btn = "9"` (R3); the
virtual pads' autoconfig binds no hotkey. A paused core still takes them, so behind the board's screens a player could
load or save over the cheat setup's own slot (Select + L1 / R1), quit the title (Select + Start) or resume it (Select +
R3). The board never uses Select (A, B, Y, the d-pad, Start).

## Built (`b141.diff`: `companion/native_session_io.py`, `companion/party_minigame.py` — with the layer's docstring lines for B139-B141)

- The bridge: **`party_hold_select(on)`** — on: the flag set under the meta lock, every pad whose last report holds
  Select written once without it; while on, `_apply_report` clears `XUSB_BACK` from every report before the route and
  the write. The companion's own meta presses (forced buttons) are not reports: untouched. `_party_hold_select = False`
  = today.
- The layer: **on** just before a held title's launch; **off** at the go (before the route and the resume — a practice's
  go too: in a practice Select passes, as in a match); **on** again when a practice ends (its way back); **off** in every
  end's steps. A start without `hold`: unchanged.

## Tests (`tests/b141_party_select_held/`, 4; B137's `nopress` scenario — the fake RetroArch logs a hotkey whenever a virtual pad shows Select with L1, R1, Start or R3, paused or running)

| test | shown |
| --- | --- |
| the preparation and the hold | Select + L1 / R1 / Start / R3 from all four pads every 0.2 s from the moment the hold is on (before the launch): **no virtual pad's Select written, the hotkey log empty**; `ready` |
| a practice's way back | the same pairs from the moment the way back holds Select: none written, the log empty; `ready`; the fake's state folder byte-equal |
| after the go | `taken`; **Select alone from pad 1 written** (passes); the hold off; off after the end |
| the bridge's default | `_party_hold_select` False: Select + L1 written as sent; on: the pad holding Select rewritten without it, Select + Start written as Start; off: Select passes |

**Mutation:** the hold a no-op → 2 fail. **Runs:** `b139_2026-11-17/tests_x3.txt`, `tests_others.txt`.
