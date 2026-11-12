# H7-L2 — pre-registration (written and hashed at stage 1, before the launch)

Sources: the task `handoffs/H7-L2_TIMED_CONTEST_TASK.md` (its three changes); B's rows
`handoffs/SESSION_B_DONE_2026-11-12AL.md` §"A — H7-L2" (stage 1, the watchers, the lines with their stage-1 fill-ins,
the close and the record's shape — used exactly); `evidence/B101_H7_TIMED_CONTEST_2026-11-12.md`;
`evidence/H7_L1_2026-11-12.md`. One sitting; the user at the TV with the onn and two pads paired to the onn as always;
nothing asked of the user on the hub.

## The mini game

T88 (HOME-12V's 2-player PS1 title). B101's contest behind the bench flag `PRIVYHUB_H7=1` (the drop-in for this sitting
only): `POST /plugins/games/h7-contest?seconds=30` loads T88's kept **"begin"** state (H7-P3's: 0 / 0, before the fight)
into the running game through scratch slot 8, arms when the values first leave the state's, runs 30 seconds by the hub's
clock with a read a second, and names the leader at the clock — the kept rule (H7-P3: P1's and P2's 2-byte level, the
larger leads, equal → "no winner yet"). It ends running; nothing on the TV shows the end, so the user fights about 20
seconds, puts the pads down, and reads the bars after A's "time" (Home on the first pad). Two contests: the first with
player 1 asked to get ahead, the second with player 2 (whoever is actually ahead is what counts).

## The cells

- **K1, K2 — in each contest the hub's `winner` is the user's leader** (`null` / "no winner yet" only if the user says
  "even" or "equal"). Beside each: the hub's values at the clock, `armed_after_s`, the samples, `resets_seen`, `ended`;
  and the `h7-read` rows from the clock's end to the user's Home — **still** (the pads were down) or not. If they moved,
  the cell is judged on the values at the user's Home and the movement is recorded.
- **K3 — the two contests name different leaders** if the user's two lines do (recorded, not required).
- **The load and the arming as designed:** RetroArch's own load line; the first read after it 0 / 0 (the state's); armed
  when the values fill; 30 seconds by the hub's clock.
- **Nothing of the user's touched:** T88's slot files and every other game's saves before = after (count and sha256;
  `pre/saves_before.txt`: 151 files); no scratch-slot-8 file left for T88.
- **The stream not disturbed:** the adaptive bitrate's rows and the recovery log over the sitting as on a normal session
  — no stall, no `launch_orphaned`, no recovery row at a load's or a read's time; what the recovery and the hold did at
  the two loads recorded as rows.
- **MET** = K1 and K2 met, nothing of the user's touched, the stream rows clean. A contest that answers an error (the
  state did not load; not armed within 20 s; refused) is retried once with a complete step; a second error ends the
  sitting with the lines recorded (→ NOT MET). Nothing here adopts anything; the bench flag is removed at the close.
