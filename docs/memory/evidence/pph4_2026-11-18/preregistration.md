# PP-H4 — pre-registration (hashed before part 1; nothing perceptual; nothing adopted)

Task: `handoffs/PP-H4_FOUR_PERSON_SITTING_TASK.md` — B150's sketch (`SESSION_B_DONE_2026-11-18AY.md` §B150) with B152's
changes (`SESSION_B_DONE_2026-11-18AZ.md` §B152) and the task's changes 1-9. T88 = H7's 2-player PS1 title (a duel),
T89 = the users' N64 four-player title (a round's end), each under its cheat setup. Both bench flags for the task only.

**Stage 1 (read before this hash, 18:35-18:38Z):** the window (18:35Z, outside 04:30-05:30Z and not within 45 min
before it); queue AZ committed (`659be84a`), clean; B150's ten greps and B152's five → 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
1, 1, **0** (`start_button`), 1, 1 as written; the board's repo clean at **`674407d`**, `e0ce8c4` and `674407d`
ancestors, 13 files changed since `e0ce8c4` (names in `pre/`), B's two files `3f32d339…` / `01301ec5…`, `load screen
again` 2, `cards %d, chose` 3, `PRACTICE_ENDS` (Select) 1, `Start button` 0; the board's folder the hub launches is that
same repo (same HEAD); the README's joining / ready-up / practice words as B150's 4 with B152's; adb the onn a
`device`, eighteen lines, `--check` ok, the APK CONFIRMED; the rules folder as H7-V5b left it (both setups True);
before: 228 files, no `.state8`; `party.jsonl` 707, `h7_results.jsonl` 293, N_HB 2028, N_ENC 60195; **B148's test →
0**; both drop-ins, the companion restarted (no SIGKILL), **twenty** lines.

## Part 1 — the gate (nobody at the TV)

(a) in a scratch `git archive HEAD` of the board, Godot headless, its folders in scratch: `hub_minigame_check.gd`
**PASS (97)**, `step25_before_minigame` PASS, `step26_sound_and_ready` PASS, `step27_winner_screen` PASS,
`step8_modules` PASS, and every check changed since `e0ce8c4` (hub_minigame_check, step25_before_minigame,
step27_winner_screen) PASS. (b) the board launched on the bench → `active`, `bench-release` `"released": true`; **B148:
the test gave 0 → no `board_import` row**. (c) `party-minigames` → two entries, players 2 and 4. (d) T88 held, seats
1,2, `bench=1`: `starting`, `ready` within 5 s, `minigame_launch` `"cheat": true, "profile_matches": true`, the two keys
`"false"`, `minigame_frame_advance` `changed` / `paused` true, PAUSED every second from the watch row to the go; the go
`taken` → `playing`, no `minigame_reloaded`; the kept end P1 by hand → `ended` `end_P1` `[1, 0]`; the end. (e) T89
held, seats 3,1,4,2: `ready` within 6 s, PAUSED, the two keys, the cheat row; `go?practice=1` → `playing`
`"practice": true`; on the bench no pad presses anything (no Select), so the practice ends by its own bound:
`minigame_practice_end` `"by": "time"`, `practice_s` ≥ 90, no `minigame_ended` inside; `minigame_ready`
`"after_practice": true`; PAUSED again; the go → `playing`, no reload; `results_1` by hand while paused → `ended`
`"places": [1, 2, 3, 4]`, `"scores": [4, 3, 2, 1]`, `"seats": [3, 1, 4, 2]`; the end. (f) the board quit (F10, exit
0); every file of the before listing before = after; no `.state8`. **Part 1 MET = (a)-(f).** Not met → one plain
sentence, the close, "YOU, now: commit"; no line asks anyone to pick up a pad.

## The self-proof (the user alone) — nothing streamed before the user's "ok"

The board launched by the user from the onn. After "ok": T88 held, seats 1,2 (no `bench`) → `ready`; the go → the
switch to T88 (`minigame_stream` `"switched": true`); **the title held 6 s after `playing`**; the end → the switch back
(`"window": "board"`, `"switched": true`); A waits 4 s, then reads **S on both switches** (switch 1's next starts ≥ 4 s
after it, so it is read; the way back is read to 30 s or the next switch). The band absent from both encoder argv lines.
**S not met on either → stop**: one plain sentence, the close, "YOU, now: commit"; the other three are never asked.

## S (B150's wording, the only wording)

The switches: the party log's `minigame_stream` rows `"switched": true`, in order; T = `time_unix`, start = T −
`seconds`. **Read: every switch whose next switch starts 4 s or more after its T**; one followed sooner is listed, not
read. A read switch meets S when among the onn's heartbeat rows after N_HB **a row has `audio_queue_depth` > 0 within 4 s
after T**, and **from that row to the next switch's start (or 30 s, or the END) `audio_underruns` rises ≤ 20 from one
row to the next**. Recorded, no bar: `audio_lost_packets`, `audio_max_arrival_gap_ms` at each switch.

## The sitting's cells (four people, four pads paired to the onn) — MET = part 1, the self-proof's S, and all of these

- **J** — four players on the board (its log); the first mini game's `minigame_start` players and seats from the pads.
- **D** — each duel: `cards 1, chose 0`; `minigame_start` `"players": 2`; ready, PAUSED, no reload; `minigame_ended`
  end_P1 / end_P2 with scores; the board's `scores … for seats …` the same. At least one; none by 40 min → "not reached"
  (not met).
- **X** — each round's end (two): one card; `"players": 4`; ready, PAUSED, no reload; `minigame_ended` with `places` and
  `scores` (places_to_scores [4, 3, 2, 1]); the board's line the same seats.
- **PR** — the practices (at least one in each title): `PRACTICE — press Select (Share) to go back` in each practice's
  encoder argv and in no other (the count = the practices); `minigame_practice_end` `"by": "select_button"` or
  `"time"`; no `minigame_ended` inside; `load screen again` in the board's log once a practice; `minigame_ready`
  `"after_practice": true` before the next go.
- **S** over every read switch of the sitting; the listed ones named.
- **L** — the board's log in order per mini game: `cards 1, chose 0`, a `practice` / `load screen again` pair per
  practice, `start`, `scores …`; each go matching a `minigame_go` row (`"practice": true` for a practice); no name.
- **C** — every `minigame_launch` `"cheat": true, "profile_matches": true`; every `watching` `"begin": "setup"`; the
  two keys `"false"` after every party launch.
- **F** — PAUSED every second from each `minigame_watch` row to its go; no `minigame_reloaded` anywhere.
- **H** — Home / RESUME once, taken, the board back.
- **E** — END: the board quit (F10, exit 0), nothing running, `status` idle.
- **U** — every file of the before listing before = after (every sha256) but the setups' in-game saves (recorded
  before and after, not a cell); no `.state8`.
- **B148** — the `board_import` row (or its absence) at each launch of the board.

**Recorded, no bar:** each `prepare_s`, `held_s`, `mute_ms`, `frames`; each switch's `seconds`;
`audio_max_arrival_gap_ms` at each switch; which practices were left by Select and which by time; the users' words on
the band and the sound (asked once at the END).
