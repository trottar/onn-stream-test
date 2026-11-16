# PP-H2 — pre-registration (hashed at the end of stage 1, before the user's launch)

Task: `handoffs/PP-H2_STREAMED_PROBE_TASK.md` — B's §"A — PP-H2" (`SESSION_B_DONE_2026-11-16AO.md`) used exactly, with
the handoff's six changes. PrivyParty on the hub, step 2 of four: the streamed probe. The user at the TV with the onn
and two pads paired to the onn; nothing asked of the user on the hub. Bench flag `PRIVYHUB_PARTY=1` for the sitting
only. Nothing perceptual; nothing here adopts anything.

## Stage 1 as read (`pre/`)

This repo at `81e00de6` (queue AO committed), clean but for this record; the two units; no game; eighteen lines; adb
up; `--check` ok; the APK `ca53df0d…` CONFIRMED. **The board's repo at `d774402d`** (one commit since PP-H1: step 19's
check), clean → the import and the 25 checks headless as PP-H1: **25 of 25 PASS** (C, read at stage 1). The config
file off the repo (fields godot, project, pictures, renderer = `gl_compatibility`). The drop-in `privyhub-party.conf`;
the companion restarted 17:36:11Z; nineteen lines (`PRIVYHUB_PARTY=1`); the keeper not restarted. The onn will offer:
Games → **"PrivyParty (1)"** (the last system) → the game "PrivyParty" → Launch on Companion → Start Fresh; Sony pads
(✕ / ○ / △); the board's confirm = ✕ (starts the game in its lobby), back = ○, map = △.

**The hub's own launch** (17:45:33-17:46:03Z, no user): **W** the window found by class PrivyParty, its pid the
board's, **1920 × 1080 at 0, 0**, fullscreen — met; **A** one sound stream (sink-input) with the board's pid — met;
**D** the `pads` row P1-P4 in event order (11-14) — met; **Q** the stop → F10, `quit 0`, `exited` code 0 in 0.31 s, no
`sigterm` row — met. (A's headless joypad listing: devices 0-3 = P1-P4 by their GUIDs; recorded, not a cell.)

Before: 161 save files, no `.state8`; the pictures folder 116 files, 15,039,288 bytes; the board repo's status empty
(`.godot/` ignored); bitrate rows 5,554; recovery log 2,199; `launch_orphaned` 2; `party.jsonl` 8 rows (stage 1's own
launch). The watcher (status, stream counters, ffmpeg and Godot CPU, graphics busy; once a second, read only) from
17:46:16Z.

## The cells

- **C** — the board's checks: 25 of 25 PASS, exit 0 (run at stage 1: met).
- **W, A, D, Q** — the hub's own launch (read at stage 1: met).
- **P — each pad drives its own seat:** the sitting's `pads` row P1-P4 in event order (P1 = device 0, P2 = device 1)
  **and** the user's one line, verbatim (each pad moved its own figure).
- **H — Home pauses and RESUME resumes:** a `pause` row with key Escape after Home and a `resume` row with key Escape
  after RESUME; the status `paused` true, then false.
- **E — END quits the board:** a `quit` row, then `exited` with code 0; no `sigterm` row.
- **S — the stream:** no stall, no recovery row, no new `launch_orphaned`; frames a second median ≥ 55 over the play.
  The bitrate's level, whether it acted, loss and PRESSURE recorded beside a normal game session's (H7-V4's), not a bar.
- **AU — sound:** the stream's audio counters growing through the play.
- **Recorded, no bar:** the encoder's and Godot's CPU and the graphics busy share, medians over the play, under
  Compatibility (and Mobile, if run); how long the join took by the rows; what the onn showed for SAVE / LOAD if pressed.
- **U — nothing of the user's touched:** the saves before = after (count and hashes), no `.state8`; the pictures'
  count and bytes unchanged; the board repo's `git status --short` after = before.
- **MET** = W, A, D, Q, P, H, E, S, AU and U met, and C (C alone not met → "MET but for C"). Anything else NOT MET.
