# B72 — the small readings: the design (written before any B72 code)

Baseline HEAD `94c05e4a`; built in `/tmp/b_q18z_work` after B70 and B71 (their files not changed here except where
named). Seven items from HOME-9+GC's "To B" (`evidence/HOME_9_GC_2026-11-09.md`, items 3-7); one record, one patch.

## (a) The N64 layout card above, not over, the details line (client; with the APK)

- **Read:** B67's card is a `Gravity.CENTER` line over the full-screen "Stabilizing game…" overlay, whose own text is
  centred too (phase, "Preparing smooth playback", the title, the resolution / FPS details, "Stream: …"). Both centred
  → the card sits on the details line (C29's photo).
- **Change:** the card at **`TOP | CENTER_HORIZONTAL`** (margins 48 px), and while it is visible the overlay's **top
  padding = the card's bottom + 24 px** (set from a layout listener on the card; the overlay's centred text is then
  centred in the space under the card, never under it). At the card's dismissal (the first key-down, today's rule)
  the overlay's padding goes back to its own (32 px). The arithmetic is a pure function
  `N64LayoutCard.overlayTopPadding(cardBottomPx, basePx)`.
- **The property:** `debug.privyhub.n64_card_top=0` → B67's centred card and the overlay untouched (= the
  `5f72af4b` behaviour); default on. With the prompt off (`player_prompt=0`) there is no card at all (B67's).
- **Tests (JVM, in `B72ClientTest`):** the padding = max(base, bottom + 24); the gravity constants (top +
  horizontal centre on, centre off); the property parse.
- This item goes into the queue's APK with B70 / B71 (the queue's list names B70 + B71; C39 reads this card on the
  new APK, so it must be in it — disclosed).

## (b) `diag_read`'s `fps (min)`: clamped at 0, the hold second excluded

- **Read:** the per-second fps is the heartbeat delta of `rendered_frames` / elapsed. After a Home hold the client's
  counters restart, so the first heartbeat after it has a negative delta (C36: -87.7, -1659.0; C32: -1730.0) — the
  hold's gap, not a rate.
- **Change (in `summarize`):** a sample whose delta is negative is flagged `fps_reset`; **the min is taken over the
  seconds that are neither `fps_reset` nor a hold-resume second, then clamped at ≥ 0**; if no second is left, the
  min of the clamped samples. The median, the per-second table and every other column: today's.
- **Tests (`tests/b72_small_readings`):** a hold's reset second (−1659) excluded → the min is the real lowest; a
  hold-resume second excluded; all-negative → 0.0, never negative; a session without a hold → today's number.

## (c) B66's split on the dolphin kind's sessions

- **Read:** B66 marks the `resumed` second and the two after it. A Dolphin hold's release runs its F9 load before the
  `resumed` row, so the stream (and its reset heartbeat) comes back **before** that row: C35's R second at 06:39:24 is
  2 s before `resumed` 06:39:26 → not split (bar 4.5, hold-resume 0). C36's second hold happened to fall inside.
- **Change:** for a `resumed` row inside a session whose core is `dolphin`, the hold-resume window starts at **the
  hold's own onset** — the latest `desync_pause` before that `resumed` within 60 s (else today's window) — and ends at
  today's end (`resumed` + 2 s). Every other core: today's window, byte for byte.
- **Tests:** a Dolphin session shaped as C35 (desync_pause 18, an R second at 24, resumed 26) → hold-resume 1, bar 0;
  the same rows labelled `beetle-psx-hw` → today's numbers (hold-resume 0); a Dolphin `resumed` without a
  `desync_pause` → today's window.

## (d) `gc_frames.py`: a 20-fps class, a segment classed by its own median, VIs beside

- **Read:** `RATES = (30, 60)`, so a title's own ~20-fps scenes snap to 30 and every second under 25 is a "hitch"
  (C34's segments with medians 21 / 19 at "30" → 224 hitches / 10 min while VIs held 60 / s).
- **Change:** `RATES = (20, 30, 60)`; after the runs are cut, **each segment's rate is `snap(its own median)`** and its
  bar 5/6 of that; with `--vblank` and `--render` (one clock: Dolphin's), **each render segment gains `vi_per_s` and
  `vi_p99_ms`** over its own seconds. The capture path gets the 20 class and the own-median rule too (no VIs: another
  clock). The whole-file `dolphin_vblank` summary: today's.
- **Tests:** a 19 / 21 / 20 run → one segment at 20, no hitches; a 60 → 20 → 60 file → three segments; a segment
  whose seconds snap 30 but whose median is 21 → classed 20; VIs beside a render segment; a 60-only file → today's
  numbers. **A read of C34's own Dolphin files on the hub (read-only)** with the new tool for the record (the 224
  artefact gone or not, as read).

## (e) Only the evdev four bound (the duplicate `SDL/0-3` devices)

- **Read:** Dolphin 2609b (C34's log) adds `SDL/0-3/PrivyHub Virtual Gamepad P1` beside `evdev/0/…P1-P4`; the
  `GCPadNew.ini` binds the evdev names only, so the SDL four are unbound but enumerated (all named P1). No Dolphin ini
  key disables one input backend (none in the binary's key names); **its SDL is linked in and reads SDL's hints from
  the environment** — the binary carries `SDL_JOYSTICK_BLACKLIST_DEVICES` and `SDL_GAMECONTROLLER_IGNORE_DEVICES`.
- **Change:** the Dolphin launch's environment gains **`SDL_JOYSTICK_BLACKLIST_DEVICES` and
  `SDL_GAMECONTROLLER_IGNORE_DEVICES` = `0x1209/0x5048`** (the companion's virtual pad's USB ids, read from
  `native_session_io`), appended to any value already there; `GCPadNew.ini` unchanged (it already names only
  `evdev/0/…`). SDL then never opens the virtual pads; the onn's real pads are never on the hub. Under
  `PRIVYHUB_GAMECUBE=1` (adopted); **`PRIVYHUB_GC_SDL_PADS=1` = today's environment** (SDL sees them).
- **Tests:** the env built for a launch carries both hints with the ids; an existing hint value kept and appended;
  `=1` → the environment unchanged; the Popen of a fake launch gets that env; the ids equal `native_session_io`'s.
- **Read at HOME-10:** Dolphin's per-launch log lists `evdev/0/…P1-P4` and no `SDL/` device.

## (f) A stall within the picture check's window does not re-save slot 9

- **Read:** C36: the hold's release loaded slot 9 and spawned `_verify_gc` (the picture check after the resume); a
  second stall 0.23 s after the resume ran `_save_gc` → Shift+F9 again while the first check was still grabbing
  (verdicts ok, but the save landed in a game whose load was being verified).
- **Change (`rewind_cores`):** a `threading.Event` "a GameCube picture check is running", set before `_verify_gc` is
  spawned and cleared when it ends (its row written). `_save_gc` during it: **waits for the check's result** (bounded
  by the check's own bound + 1 s), then **does not press Shift+F9**: the row `state_save_skipped` with
  `reason: "gamecube: the last load's picture check was running"`, `kind`, `core dolphin`, `gc_states hotkey`; no
  `last_save` for that stall, so its release resumes in place (`rewind_skipped` "no scratch state for this pause", the
  PS1 rule). One save per stall, none during a check; the first stall's row order kept (its `gc_states` verdict before
  the second stall's skip).
- **Tests (fake Dolphin of `tests/gamecube_session`):** a save while a check runs → no key, the skip row after the
  check's row; a save with no check → today's (the key, `state_saved`); the event cleared after a check that raised.

## (g) The SAVE / LOAD reply bodies logged on the hub (`state_reply` rows)

- **Read:** the plugin returns SAVE / LOAD's payload to the onn and logs nothing of it (HOME-9: "`confirmed` not
  read").
- **Change (`plugins/games.py`):** after each `save-state` / `load-state`, one recovery row **`state_reply`**:
  `action`, `slot`, `ok`, and the reply's scalar keys from a fixed list (`accepted`, `confirmed`, `control`,
  `verification`, `replaced_existing`, `overwrite_requires_confirmation`, `paused`, `hotkey`, `gc_states`, `disc`,
  `discs`) — **never** `state_file`, `slot_detail`, `game`, a title or a path; a failure: `ok false` and `error` (the
  message, ≤ 160 chars, a path-like token replaced by `<path>`). `PRIVYHUB_STATE_REPLY_ROWS=0` = today (no row).
- **Tests:** a PS1-shaped SAVE reply → the row with those keys only; a LOAD failure → `ok false`, the error; the knob
  → no row; no `state_file` / title / path in the row.

## Mutations, files

One mutation per item at least: (a) the padding's +24 dropped / the property ignored; (b) the reset not excluded;
(c) the dolphin window not used; (d) 20 removed from `RATES`; (e) the hint not set; (f) the check not awaited; (g) the
whitelist opened (`state_file` leaks). Record `evidence/B72_SMALL_READINGS_2026-11-09.md` + `b72_2026-11-09/`;
`patches/B72_SMALL_READINGS.md`. Host items live at the companion's next restart; (a) with the APK.
