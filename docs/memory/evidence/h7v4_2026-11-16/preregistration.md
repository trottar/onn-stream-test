# H7-V4 — pre-registration (hashed at the end of stage 1, before the launch)

Task: `handoffs/H7-V4_SELF_PROOF_THEN_MATCHES_TASK.md` — the kept state brought in by hand is
`SESSION_B_DONE_2026-11-16AN.md` §"A — H7-V3" part 1 step 10; the lines, start checks, close and record shape are its
part 2's, with the handoff's changes. T88 = H7-V1's / H7-V2's 2-player PS1 title. The user at the TV with the onn and
two pads paired to the onn; nothing asked of the user on the hub. **Nobody is asked to play until P is fully met in
this sitting** (the user's standing word from H7-V2). Nothing here adopts anything.

## Stage 1 as read (`pre/`)

HEAD `f19c8987` (H7-V3 committed); the tree clean but for this record. Two units; no game; eighteen lines; adb up;
`--check` ok; the APK `ca53df0d…` CONFIRMED. **The spec is H7-V3's** (json `06058b7b…`, npz `922415bc…`), not learnt
again; `score` with B's four arguments = H7-V3's in every count (H7-V1 1,152 / 1,152; live 495 / 507, 12 `unknown`;
`other_read_as_screen` 0). Thresholds: screen **0.0902**; start 0.1007 / end_P1 0.1032 / end_P2 0.0990; margin 0.0929.
The kept begin `361e4007…`, end P1 `a0efb49b…`, end P2 `ef011ec5…`. B99's drop-in byte for byte; the companion
restarted 15:37:22Z; nineteen lines (`PRIVYHUB_H7=1`); the keeper not restarted. Routes: `no_game`; 400 "no game is
running"; `{"watch": "none"}`. The onn: "PlayStation (72)", Down 20, Right 1, Start Fresh, Sony pads → ✕. Before:
161 save files (T88's 4), no `.state8`; bitrate rows 5,263; recovery log 2,166; `launch_orphaned` 2; `h7_results` 11
rows; `runtime/h7_frames/`: `h7v2_20261116_run`, `t88`. The result watcher (GET `h7-result` once a second, off the
repo) from 15:38:33Z.

## The cells

- **P — the self-proof** (on "ready", in that one turn, the user touching nothing): `recognised` **true within 8 s**
  at its three starts (proof 1, 3, 4); after the kept end P1 state's load line, `ended` with **`end_P1`** within
  **15 s**; after a new start and the end P2 state's load line, `ended` with **`end_P2`** within **15 s**; never the
  other side; no `ended` before a load. **P not met → the sitting ends with no match; the verdict NOT MET.**
- **R — recognised before every match:** `recognised` true at the start before each of the three matches (proof 4
  for match 1; A's start after the user's line for matches 2 and 3), read before that match's line is given.
- **M1, M2, M3:** in each match the hub's result is `ended` with the side the user names (`end_P1` = player 1,
  `end_P2` = player 2), its row **earlier than the user's "back"**, and **within 8 s of the first kept-index row after
  the fight whose `screen` distance is under 0.0902**. A match not `ended` when "back" arrives is not met (the reads
  after it recorded for 30 s, the watcher's class and `last`).
- **Never during a fight:** the kept picture at every `ended` row of a match shows the select screen with one side's
  tally raised (A's look at that one picture per match, in words, no names), and the kept index shows no `ended`
  between a match's start and that screen's first row.
- **The characters** as the user played them, from the user's words only (labels in the record) — not a bar.
- **U — nothing of the user's touched:** the saves listing before = after (count and every hash); no `.state8`
  anywhere after.
- **The stream not disturbed:** the adaptive bitrate's rows and the recovery log as on a normal session — no stall, no
  new `launch_orphaned`, no recovery row at a load's time or caused by the watcher or its kept pictures. The first
  session's rows read on their own against H7-V2's first-session loss burst — recorded, not a cell.

**MET** = P, R, M1, M2, M3, never during a fight, U and the stream rows clean. Anything else NOT MET, with the rows
that show why (`last`'s distances against its thresholds at the reads that mattered).
