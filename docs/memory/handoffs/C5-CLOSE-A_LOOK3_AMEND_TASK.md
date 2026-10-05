---
memory_schema: 1
as_of: 2026-10-05
status: TASK HANDOFF — C5-CLOSE-A: read the user's repeated Look 3 of 2026-10-05 from the logs (did the injected entry act, how long at 1920×1080, what the decoder report says), record the user's words — "Looked the same and loading the game still says 720" — and amend the C5-CLOSE record, the decision and CURRENT.md accordingly; also make the client overlay's size cosmetic note explicit. Read-only on the system; no session; nothing adopted; nothing committed
---

# C5-CLOSE-A — the repeated Look 3, read from the logs

**The user's words, 2026-10-05, after repeating Look 3 with the fixed
hand steps (flags set, the game started from the TV, ≥ 2 min, then
`inject?class=INCREASE_1080P`, then the flags unset):** *"Looked the same
and loading the game still says 720"*. Record verbatim.

## 1. What happened, from the logs only

Find the session (today, local evening; the manager carried `TOP=1080p`
and `INJECT=1`; the companion journal, the controller decision log — the
rotated and live files, sliced by time — the recovery log, the decoder
report stored at BACK, `native_video_alpha.log`'s `Output #0` lines):

- the `inject` row's time relative to PLAYING, and its outcome:
  `transition` (7000 → 12600, `increase_1080p`, `injected: true`) or
  `refused` with its reason;
- if it acted: the encoder's `Output #0 ... 1920x1080 ... 12600 kb/s`
  line, the SSRC change, the minutes at 12600 until BACK, the C2
  telemetry at the rung (fps, stale, loss per minute), the decoder
  report's totals (spikes/min, max gap, the SSRC count) and, if the
  report carries the decoded size or the session's largest frame sizes
  that only 1080p produces, say so;
- if it was refused: which guard, and whether a later inject arrived;
- the teardown: flags absent afterwards (the manager and the environ),
  live, 7000 / 1280×720, APK `de072762…835e`.

**The overlay.** The client's on-screen size text prints the decoder's
configured hint (1280×720), not the live SPS size — C5-M1 recorded it
as cosmetic. State that in one line with the file and the line that
prints it (`PrivyHub/.../streaming/...`), so "still says 720" is
explained without a client change (and list the one-line client change
that would make it read the live size, for a later APK, not built).

## 2. Amend

- `evidence/C5_CLOSE_2026-10-05.md`: a dated addendum — the user's
  words; whether this look was at 1080p; the figures; the overlay note.
  If it was at 1080p: "the user looked at the rung's picture and saw no
  difference from the 4x 720p stream", and the decision's grounds now
  include the look. If it was refused: "the 1080p picture remains
  unlooked-at; the decision stands on its other grounds", and name what
  refused it.
- `decisions/C5_1080P60_CAPABILITY_2026-09-28.md`: the same addendum, in
  short. The four decisions unchanged.
- `TOOLS.md`: the 1080p hand steps carry the overlay note ("the on-screen
  720 is the hint; check `native-stream-status` width/height, or the
  decision log's transition row").
- `docs/ROADMAP.md` C5 / C7 row: the "unlooked-at" sentence corrected or
  kept per §1. `investigations/ACTIVE.md`; the daily file; `CURRENT.md`
  (Active Objective's look lines; Next Action 1 the user's commit, 2 the
  user's go for Phase E).
- `check_memory_health.py`; the redactor `--check`; `git status --short`
  and `git diff --stat` to `logs/c5_close_a_git_status.txt`.

No session, no flag set, no `nft`, no real `sudo`; no addresses, MACs,
SSIDs, ADB endpoints, serials or credentials anywhere. Nothing adopted.
Nothing committed.
