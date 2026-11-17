# H7-V5b — the loads

- **The hub's own** (each mini game's start): the setup's begin into scratch slot 8 of the setup's own folder — five
  starts, each `loaded` (26-57 ms), `"begin": "setup"`.
- **By hand** (into the setup's own `states/<core>/<stem>.state8`, the scratch removed at once — **0 `.state8` after
  each**): T88 end P1 (06:59:10.613Z, 51 ms), end P2 (06:59:27.363Z), mid-fight (06:59:44.113Z) — PS1, no pause needed;
  T89 results_1 twice (07:00:52.330Z, 07:00:59.813Z) — **each sent only after `GET_STATUS` answered PAUSED** (by
  `PAUSE_TOGGLE` from PLAYING), `PLAYING` again after; every `LOAD_STATE_SLOT 8` answered and its load line naming the
  scratch (`t88_steps.txt`, `t89_steps.txt`).
