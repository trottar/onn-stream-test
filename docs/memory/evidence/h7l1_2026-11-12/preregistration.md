# H7-L1 — pre-registration (written and hashed at stage 1, before the launch)

Sources: the task `handoffs/H7-L1_LIVE_READ_TASK.md` (with its four additions); B's rows
`handoffs/SESSION_B_DONE_2026-11-11AK.md` §"A — H7-L1" (stage 1, the watcher, the fight's replies, the rule, the close
and the record's shape — used exactly); `evidence/B99_H7_LIVE_READ_2026-11-11.md`; `evidence/H7_P3_2026-11-11.md`.
One sitting; the user at the TV with the onn and the pads paired to the onn as always; nothing asked of the user on the hub.

## What is read

T88 (HOME-12V's 2-player PS1 title). B99's route `GET /plugins/games/h7-read` behind the bench flag `PRIVYHUB_H7=1` (the
drop-in for this sitting only), reading T88's kept rule (H7-P3: P1's and P2's 2-byte level, the larger leads, equal →
"no winner yet"). The watcher calls it once a second (GET only). The user's lines — who is ahead, roughly how full each
bar is, who won — are the facts, recorded verbatim (a character named is replaced by its label).

## The cells

- **L0** (runs: T88's Continue copy = the kept `end_p2_b` copy by hash, `pre/continue_check.txt`): the first read after
  the stream starts = **110 / 140, leader P2**. Not independent (a save the search used); the first read through the live
  path on the real title.
- **L1-L3** (each pause): **the read's leader is the user's leader** (equal values only if the user says "even"); **the
  values move the way the bars moved** — a bar the user saw drop since the previous pause reads lower, and a fuller bar
  reads higher than an emptier one; **by L2 both values are below 140** if the user says both took damage. "Roughly how
  full" is the user's eye, not a scale: it is set beside the numbers, and judged only through the order (fuller → higher)
  and the direction (dropped → lower).
- **L4** (the knockout): the read's leader is the player the user says won. The loser's value at that second is recorded,
  not judged (H7-P3: a finished fight's loser was not at 0).
- **L5** (only on "new round"): both bars full → equal → "no winner yet". "menu" → not run.
- **The stream not disturbed by the reads:** over the sitting the adaptive bitrate's rows and the recovery log read as on
  a normal session — no stall, no `launch_orphaned`, no recovery row at a read's time (`h7_reads.jsonl`'s times against
  them); every read's `read_ms` and any "busy" / "not in time" answers counted.

**MET** = every cell that ran is met and the stream rows are clean. Any pause wrong → **NOT MET**, the lines recorded,
nothing changed. Nothing here adopts anything; the bench flag is removed at the close (eighteen lines).

## Which read is "the read at that second"

For a pause: the watcher's rows while `paused` is true in that pause, up to the user's line; the leader and values must
agree across those rows (a paused game does not change), and that read is set beside the line. For L0: the first row
with `paused` false after the launch (the hub launches paused; the stream's start resumes it). For L4: the rows from the
last pause to the knockout line — the leader once the fight has stopped (the last rows before the line).
