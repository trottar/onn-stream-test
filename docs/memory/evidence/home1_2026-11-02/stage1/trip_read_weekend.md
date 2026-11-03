# HOME-1 stage 1: "read the trip", the whole weekend

- `python3 tools/diag_read.py trip` → `evidence/reads/diag_trip_20261103T004048Z.md` (range 2026-10-30T00:13:33Z →
  2026-11-01T23:59:35Z, the keeper dir only). **36 sessions, 6 restarts, 5 stalls.**
- **TRIP-R2 §1 reproduced exactly.** Six client restarts at 01:20:44, 03:26:05, 04:19:21, 04:30:12, 04:34:41 and
  05:19:35Z on 10-31:
  - all `trigger: surface` where a report exists (the last has none);
  - the same rungs before and after, the same paused / away ms, and the same uplink silences;
  - the stalls 419 / 464 ms before 04:19:21 and 04:30:12.
- **Saturday and Sunday** (from the keeper's samples, `session_audit` and the journal copy; class only):
  - **No game was played** after 2026-10-31T05:30Z. The last `session_started` was 05:19:36Z; the brawler session
    ended by link loss (`gave_up_saved` 05:30:40Z, `ended_after_link_loss` 06:00:43Z).
  - **VOD, Sat 06:04-09:54Z:** the feature (movie B), TRIP-R2 §4.
  - **VOD, Sun 2026-11-01** (overlay; `token_issued` 04:03:10Z):
    - 04:12:49Z: a camera source start answered 500;
    - 04:18:24Z start, 04:18:29Z stop;
    - **04:19:11Z start, 06:34:57Z stop: one movie for 2 h 16 min, no break in the start / stop record**;
    - 06:35:01-06:35:16Z: two 7-s starts of other movies and their stops. Nothing after that.
  - The journal changes offset at the DST end (-04:00 → -05:00 on 11-01 01:00 local). The times above are UTC.
- **The keeper:** stopped by its cap ("done (the cap)", 2026-11-01T23:59:00Z, 862 copies, 4306 samples). The unit is
  gone. `manifest.sha256` (1837 lines) checks with 0 failures.
- **The user's line on the weekend:** not given at stage 1.
