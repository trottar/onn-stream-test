# H7-V3 — pre-registration (part 1 only; unattended; hashed at the end of stage 1, before stage 2)

Task: `handoffs/H7-V3_LIVE_PATH_UNATTENDED_TASK.md` — B's part 1 (`SESSION_B_DONE_2026-11-16AN.md` §"A — H7-V3", steps
1-16) used exactly, with the handoff's five changes. T88 = H7-V1's / H7-V2's 2-player PS1 title. No user, no onn, no
pads; nothing asked of the user. Part 1 only: no part 2, whatever the result. Nothing here adopts anything.

## Stage 1 as read (`pre/`)

- The spec learnt B104's way from both sources with both label files (`pre/learn_report.json`, `pre/score.json`,
  `pre/replay_k3.jsonl`): every class separable; screen threshold 0.0902; classes start 0.1007 / end_P1 0.1032 /
  end_P2 0.0990; margin needed 0.0929; masks 13,756 / 97 px; `unlike_label` 3 / 4 / 5; version 2. Score: H7-V1
  1,152 / 1,152 right; live 495 / 507 labelled right, the 12 others `unknown` (3 start, 4 end_P1, 5 end_P2 — the
  range-edge pictures); `other_read_as_screen` 0. Replay K = 3: `ended` end_P1 at 153.03 s (end screen from 151.02 s)
  and end_P2 at 420.03 s (from 418.03 s). Spec json `06058b7b…`, npz `922415bc…`.
- The kept begin state beside it `361e4007…`; the kept end P1 `a0efb49b…`, end P2 `ef011ec5…`, mid-fight P1-ahead
  `45dc8522…`, mid-fight P2-ahead `183f4071…` (= H7-V1's SHA256SUMS).
- B99's drop-in byte for byte (`5497a0ee…`); the companion restarted 15:05:38Z, its MainPID serving; nineteen lines,
  the nineteenth `PRIVYHUB_H7=1`; the keeper not restarted. Routes: `no_game`; 400 "no game is running";
  `{"ok": true, "watch": "none"}`.
- Before: 161 save files (T88's 4; slots 1-3 none); no `.state8`; bitrate rows 5,258; recovery log 2,140;
  `launch_orphaned` 2; `h7_results` 9 rows (H7-V2's); `runtime/h7_frames/` holds `h7v2_20261116_run`, `t88`.

## The cells

- **The spec** — equals B104's arrangement 3 in every number above, with its score and replay. *(Read at stage 1:
  met; recorded here so the cell is fixed before the run.)*
- **R — recognised:** `recognised` **true within 8 s** at every start — the first (end P1), the one before end P2,
  the two before the mid-fight states, the two of the replace (6 starts); each `recognised` row's `after_s` recorded.
- **E1 — end P1:** after the end P1 state is loaded, `ended` with **`end_P1`** within **15 s of the load line**; never
  `end_P2`; never `ended` before the load.
- **E2 — end P2:** after a new start and the end P2 state, `ended` with **`end_P2`** within **15 s of the load line**;
  never `end_P1`; never `ended` before the load.
  (Also recorded, not a bar: the seconds from the first kept-index row whose `screen` distance is under 0.0902 to the
  `ended` row — expected ≤ 4 s.)
- **F — never during a fight:** **no `ended` in 45 s** after either mid-fight state's load (class `other`; `unknown`
  reads recorded, not failures); after each 45 s, `h7-stop`.
- **S — stop and replace:** `h7-stop` → `idle`, the game's status unchanged (running, unpaused); a start over a
  running watch → `"replaced": true`, and **exactly one `replaced` row** in the whole run.
- **G — the game:** never paused or ended by the hub during the run (read every 10 s; one relaunch allowed, noted);
  `launch_orphaned` unchanged (2).
- **U — nothing of the user's touched:** the saves listing before = after by count and hash (161); **no `.state8`
  anywhere** after.

**MET** = the spec, R, E1, E2, F, S, G and U all met. Anything else **NOT MET**, with the rows that show why (`last`'s
distances against its thresholds at the reads that mattered).

## How stage 2 runs (B's steps 8-16 with the handoff's changes 1-3)

The launch on loopback with no client, waiting for the answer (`launch?id=<id>`, `-m 120`); `native-stream-start`
(to nobody); `native-stream-ready` (the pause released). If those do not bring the game to running and unpaused, the
code may be read for the right loopback calls, used and disclosed — no file edited, no flag but the bench one,
nothing adopted touched; if the game cannot be kept running unpaused with no client: NOT MET with the reason, the
close. The game's status every 10 s to the end; `h7-result` once a second (GET only). Each state brought in by B101's
load step by hand: the kept copy to scratch slot 8 in the state folder and stem the hub's own load used, RetroArch's
`LOAD_STATE_SLOT 8` on its command port, its `[State] Loading state …` line in the session log (N > 0) within 1.5 s,
the scratch copy removed. Order: start keep=1 → recognised → end P1 → ended; start keep=1 → recognised → end P2 →
ended; for each mid-fight state start keep=1 → recognised → the state → 45 s → `h7-stop`; start → `h7-stop` → idle;
start, then within 5 s start again → replaced → `h7-stop`; the game stopped; the stream inactive; after = before.
