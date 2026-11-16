# H7-V2 — pre-registered (written and hashed at stage 1, before the launch; B's rule with the handoff's change 1)

T88 = HOME-12V's 2-player PS1 title. The hub (B103 behind `PRIVYHUB_H7=1`, the spec learnt by B102's tool from H7-V1's
frames with Cowork's labels, all frames) puts T88 at its mini game's start (the kept "begin" state) and watches the
game's picture once a second; it is told nothing.

- **M1, M2, M3 — in each match the hub's result is `ended` with the side the user names** (`end_P1` = player 1,
  `end_P2` = player 2), **and its `ended` row is earlier than the user's "back".**
- **Never during a fight:** no `ended` row while the kept pictures show a fight, a round's "wins" line or a round intro;
  `seen_start` true from the start.
- **Soon after the screen returns:** from the first kept picture showing the select screen after the match to the
  `ended` row ≤ 8 s. `unknown` reads are recorded, not failures; a match not `ended` within 30 s of the user's "back" is
  "not met" (no retry of the same match).
- **Characters the spec never saw:** matches 1 and 2 with other characters, match 3 with the same character on both
  sides — as the user played them (recorded from the user's words only; if the user says they used the saved pair, the
  match is recorded as such and still judged).
- **Nothing of the user's touched:** T88's slot files and every other game's saves before = after (count and hash); no
  `.state8` left.
- **The stream not disturbed:** the adaptive bitrate's rows and the recovery log as on a normal session — no stall, no
  new `launch_orphaned`, no recovery row at a load's time or caused by the watcher or the picture keeper; the picture
  keeper's cost recorded.
- **MET** = M1, M2 and M3 met, never during a fight, nothing of the user's touched, the stream rows clean. Nothing here
  adopts anything.

Also read, not a cell: what the watcher read during the fights and the rounds' "wins" lines (`other` throughout? any
`unknown`?) and how long after the select screen returned `ended` was said.

Marks at stage 1: the hub's saves 161 files (T88's 4; slots 1-3 none), no `.state8`; bitrate rows 4,902; recovery log
2,078 rows, `launch_orphaned` 2 (both before this sitting — a new one counts); `h7_results` absent; the spec's json
`98e22dc3…`, npz `08ad0ac1…`; the kept "begin" `361e4007…`.
