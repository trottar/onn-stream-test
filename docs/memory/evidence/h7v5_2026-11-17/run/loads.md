# H7-V5 — the loads

- **Made (the hub's own, by the mini-game start):** T88's setup begin into scratch slot 8 of T88's setup's
  `states/<core>/` (RetroArch's load line naming it, 27.1 ms, 16,777,240 bytes); T89's setup begin the same (56.1 ms).
  The scratch removed by the hub: **0 `.state8` after each** (read after step 12's end and after step 16's end) and at
  step 20.
- **Not made:** steps 13-15 (T88's kept end P1, end P2 and mid-fight by hand) and steps 17-18 (T89's kept results_1 by
  hand, paused) — each title was stopped at its `recognised` false (change 4). So **no N64 hand load was sent** (none to
  a core not answering `PAUSED`).
