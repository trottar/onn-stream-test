# B130 — the recognition window under a cheat setup: the design (written and hashed before any code)

Only with `PRIVYHUB_H7=1` (absent: the module is not imported — today). No title, id or path; no picture in git.

## The numbers it rests on

- **T88 under its setup, the board's order** (H7-D1, early: the begin loaded 0.08 s after the launch answers): the
  first `start` read **9.00 s** after the load — RetroArch's notices (the cheat applied, the pads configured, the state
  loaded) over the lower-left corner keep every read `other` until then; **late** (loaded 15.5 s after the launch):
  **4.00 s**. H7-C2's T88 cheat slot 1: **6.97 s**. H7-V5: T88 not recognised in 8 s (the same cause).
- **T89 under its setup** (H7-D1's pictures cut by B129's rectangle): **2.00 s** early, **1.20 s** late.
- Without a setup (today's 8 s, untouched): H7-V4 4.0 s at three starts; PP-H3b's mini games recognised in time.

## The rule

**`recognised` settles `false` after `RECOGNISE_SETUP_S` = 15.0 s when the watch began with the load under a cheat
setup** (the session's `cheat_session.profile_id` set — B127's `session_profile_id`); **8.0 s otherwise** (today). The
settle rule itself unchanged: `true` at the first read naming the start class (at any second), `false` at the first read
(or picture failure) at or after the window with no start read yet. The watch's `watching` row's `recognise_s` and the
party layer see the watch's own window.

- **Margin:** the slowest start seen under a setup is 9.00 s (T88, the board's order) — **6.0 s inside 15.0 s (1.67 ×)**;
  H7-C2's 6.97 s 8.0 s inside; T89 2.0 s.
- **Cost:** a wrong screen under a setup (not the title's start: nobody may play) now says `false` **15.0 s after the
  load instead of 8.0 s — 7.0 s later**; the party mini game is then given up ("the title's start screen was not
  recognised") and the board comes back; the users wait at most ~15 s + the end's hand-over (B115: ~1-3.5 s) before
  the board is back — inside the 30 s the hub already allows a start (`START_LIMIT_S`) and well before anyone has played
  a match (a match of either title takes minutes).
- **Not chosen:** counting from the first read without notices (needs a notice detector — a new reader); a longer
  window for every load (no need without a setup; earlier answers would move).

## Proof

- **Replay** (`scripts/b130_replay.py`, the watcher's settle rule over the reads with their seconds): H7-D1's four
  folders — T88 early / late (the watcher's own reads from `index.csv`), T89 early / late (B129's cut, read with the T89
  spec) → **all four `true`**, each with its second, under 15.0 s; with 8.0 s: T88 early `false` (today's answer);
  **never-the-start runs → `false` at the first read ≥ 15.0 s, never `true`**: synthetic (every read `other` /
  `unknown`), H7-V2's live fights (the `other` stretches read by the T88 spec), H7-D1's T89 desktop reads as they were
  (the stale rectangle); **earlier answers unchanged:** runs without a setup keep 8.0 s (H7-D1's T88 late, H7-C2's
  slot 1 stretch with its 6.97 s → `true` under both).
- **Tests** (`tests/b130_h7_recognise_setup/`, B103's harness, the windows scaled: `recognise_s` 0.8, the setup's
  1.5, one read every 0.1 s): under a setup, a covered picture for 1.0 s then the start → `true` (with the old window
  it would be `false`); never the start → `false` at ≥ 1.5 s and not before; without a setup → `false` at ≥ 0.8 s
  (today); the constants 8.0 / 15.0; the `watching` row's `recognise_s`; the flag absent → today's answers through the
  real routes (HEAD's companion against mine).
