---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: 94c05e4a (B72 built in /tmp/b_q18z_work after B70 and B71; its diff against the after-B71 snapshot; applied to the tree third, uncommitted)
---

# B72 — the small readings: (a) the N64 card above the details line, (b) `fps (min)`, (c) B66's split on the dolphin kind, (d) `gc_frames`' 20 class, (e) only the evdev four, (f) one slot-9 save per stall, (g) `state_reply` rows

**Classification: BUILT** (one record, one patch). Each item has an off switch, or a scope that keeps today:
`proof_flag_absent.md`.

**Tests:**
- host `tests/b72_small_readings` 25 green ×3 (no temp dir);
- client `B72ClientTest` 5, inside JVM 259 / 259 (working tree) and 248 / 248 (APK tree);
- every host suite as the baseline.

**Mutations: 7 / 7 host and 3 / 3 client caught.** Item (a) is in the APK `64d02f31…85dd` (not installed).

Design `b72_2026-11-09/design_written_before_code.md`, sha256 `0a825f22…ceff857b`, hashed **07:37:06Z, before any
B72 code**.

| item | built | read on the hub's own data (read-only) |
| --- | --- | --- |
| **(a)** the N64 card | The card at **top centre** (margins 48). While it shows, the "Stabilizing game…" overlay's top padding = the card's bottom + 24 px, so the overlay's centred text, its details line included, sits under the card, never under it. The padding is put back at the dismissal. **The top card has its own "shown" key (`shown_top`)**: an onn that saw B67's centred card sees the new one once, at the first N64 start on the new APK, which is what C39 reads. `debug.privyhub.n64_card_top=0` = B67's centred card and B67's key | C39 at the TV |
| **(b)** `fps (min)` | A negative per-second delta (the client's counters restarted after a hold) is flagged. The min is taken over the seconds that are neither such a reset nor a hold-resume second, clamped at ≥ 0. The median and the tables are unchanged | **the HOME-9 evening re-read** (`home9_diag_reread.txt`): the three negative minimums −1730.0 / −87.7 / −1659.0 now read **57.6 / 58.1 / 58.4**; every other session is unchanged |
| **(c)** B66 on dolphin | A Dolphin hold's stream returns **before** its `resumed` row (the F9 load runs first). In a `dolphin` session the hold-resume window therefore starts at the hold's own `desync_pause` (≤ 60 s before) and ends at B66's end | **C35's session: bar 4.5 / hold-resume 0 → bar 0.0 / hold-resume 1** (as C36's); the PS1 / N64 sessions identical |
| **(d)** `gc_frames` | **A segment's rate is its own median snapped to 20 / 30 / 60.** With `--render` + `--vblank` each render segment carries its own `vi_per_s` and `vi_p99_ms` | **C34's first launch: 224.39 → 39.02 hitches / 10 min.** Its two segments with medians 21 / 19 are now classed 20, with VIs 60.0 / 59.25 per second. 8 seconds remain under their segment's bar, VIs 59-60 / s throughout. C35's and C36's launches are unchanged (0.0; `c34_c36_gc_frames_reread.txt`) |
| **(e)** only the evdev four | Dolphin's linked-in SDL also opened the companion's uinput pads (C34: `SDL/0-3`, all named "P1"). The Dolphin launch's environment now gains `SDL_JOYSTICK_BLACKLIST_DEVICES` and `SDL_GAMECONTROLLER_IGNORE_DEVICES` = `0x1209/0x5048` (the virtual pad's USB ids, checked against `native_session_io`), appended to any value already set. Both hint names are in Dolphin 2609b's binary (read as an archive; nothing run), and no Dolphin ini key turns one input backend off. `GCPadNew.ini` is unchanged (it names only `evdev/0/…`). `PRIVYHUB_GC_SDL_PADS=1` = today's environment | HOME-10: Dolphin's log lists `evdev/0/… P1-P4` and no `SDL/` device |
| **(f)** one save per stall | `rewind_cores` keeps an event that is clear while a GameCube picture check runs. A stall's `_save_gc` during it **waits for the check's verdict** (≤ 8 s), then **sends no Shift+F9**: the row `state_save_skipped` with reason "gamecube: the last load's picture check was running". That stall's release resumes in place ("no scratch state for this pause", the PS1 rule) | C36's back-to-back stall would now read: check verdict, then the skip, then a plain resume |
| **(g)** `state_reply` | After each SAVE / LOAD, one recovery row `state_reply`: `action`, `slot`, `ok` and the reply's scalar keys from a fixed list (`accepted`, `confirmed`, `control`, `verification`, `replaced_existing`, `overwrite_requires_confirmation`, `paused`, `hotkey`, `gc_states`, `disc`, `discs`). It **never** carries the state file, the slot detail, the game, a title or a path. A failure gives `ok false` and `error` (≤ 160 chars, path-like tokens replaced by `<path>`). The reply to the onn is unchanged. `PRIVYHUB_STATE_REPLY_ROWS=0` = no row | HOME-10: C38's SAVE / LOAD rows |

## Disclosed

1. **(d) was refined after a test finding.** The design put 20 into the per-second classes. B69's own metric tests then
   showed that a real hitch second in a 30-fps run (≈ 23 presents) would snap to 20, cut the run and vanish as a hitch.
   So the runs are still cut on today's 30 / 60, and the 20 class applies only when a segment is classed by its own
   median. C34's case ("30" runs with medians 21 / 19) is covered either way. New guard
   `test_a_hitch_second_stays_in_its_run`; the design's first form is mutation M3b, caught.
2. **(a)'s `shown_top` key** was added after the design was hashed. Without it, C39 could not be read on an onn that had
   already seen B67's card, short of clearing app data. The APK was rebuilt (twice, the same bytes) and re-pinned.
   Mutation M3 (B67's key kept) is caught.
3. **(g) changed one existing test's view:** B65's plugin test pinned the exact row list of a refused N64 load. It now
   filters out the new `state_reply` row and keeps its assertion.
4. **Not addressed here (HOME-9's readings, listed):** the audio underruns per session (121 N64 / 4:21; 76-82 GameCube
   / ~2 min). They are a reading for a later item, not one of the seven.

## Tests and mutations

- **Host** (`tests_x3.txt`, `tests_mutations_host.txt`; B36's diag fixture, B69's fake Dolphin):
  - **(b)** a reset second excluded; a hold-resume second excluded; never negative; today's number without a reset;
  - **(c)** C35-shaped rows on dolphin → split; the same rows on PS1 → B66's; dolphin without a `desync_pause` → B66's;
  - **(d)** the 20 class; a hitch second stays in its run; the own-median rule; the VIs beside; 60-only → today's;
  - **(e)** the hints; an existing value kept; the knob; the ids; the launch builds the env; the ini unchanged;
  - **(f)** a stall during the check → no key, the skip after the verdict, then a plain resume; after the check → the
    save as today; a check that raises still ends;
  - **(g)** a SAVE reply's row with no leak; a LOAD failure's row with `<path>`; the knob; a GameCube LOAD reply.
  - Mutations M1-M6 and M3b are all caught.
- **Client** (`tests_jvm.txt`, `tests_mutations_jvm.txt`): the padding under the card; the top / B67 gravity; the
  property; the top card's own key; B67's rule unchanged. Mutations caught: the gap dropped; the property ignored;
  B67's key kept.

## Files

`b72_2026-11-09/`:
- the start files; the design + its hash;
- `b72.diff` (12 files), `applied_to_tree_at.txt`, `diff_check.txt`, `proof_flag_absent.md`;
- the tests and mutations; `tests_host_after_b70_b71_b72.txt`; `tests_host_full_export_head.txt` /
  `tests_host_full_export_b70_b72.txt`;
- `home9_diag_reread.txt`, `c34_c36_gc_frames_reread.txt`;
- `redact_check` / `title_check` (+ `.txt`), `manifest.sha256`.

Patch note: `patches/B72_SMALL_READINGS.md`.

**One line for the user:**
- the N64 button card now sits above the "Stabilizing" text, and shows once more so you can see it;
- GameCube no longer sees duplicate pads;
- a quick second freeze no longer re-saves;
- the hub's readings no longer show negative frame rates or count a GameCube pause as a hitch.
