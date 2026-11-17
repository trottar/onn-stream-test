# H7-V6 — the frame advances and the loads

- **The hub's own:** each preparation one `minigame_frame_advance` — T88 `"frames": 2, "paused": true, "mute_ms":
  163.9`; T89 `"frames": 2, "paused": true, "mute_ms": 196.7` — each 0.13 s after its watch row; each begin the setup's
  own (`"begin": "setup"`), loaded 27.4 / 56.0 ms.
- **By hand: none** — the kept end states, the mid-fight and T89's results come after a `ready` that never came; A's own
  `FRAMEADVANCE` (step 7) was not sent; no `.state8` at any time (0 at step 10).
- **Practices: none run** (each title's preparation given up before a go).
