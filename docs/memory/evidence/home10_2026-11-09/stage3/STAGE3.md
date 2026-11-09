# Stage 3 — PS1 one-disc (T15): C37's PS1 line, C38's one-disc check (~16:44-16:45Z)

- **The user (verbatim):** "Touchpad does nothing" / "No change disc shows" / "Stage 3". (Before it, at the four-disc
  start: "Touchpad didn't do anything" / "There is now a disc change button. But it causes the end button to run off
  the screen" — `../c38/T17_FIRST.md`; then "Stage 3" with no game played, read as no step done.)
- **Hub** (`../c38/rows_raw_t15_one_disc.jsonl`, pad id redacted): `launch_ports` 16:44:24Z ps1, `device_args` 1-2,
  `capable` false — **no `discs` / `disc` keys**; `state_reply` load-state slot 1 ok (B72 (g)); `session_started`
  16:44:30Z; `session_end_bye` 16:44:49Z. Heartbeats in the session: 12, **none with `discs`**. The game log: a `.cue`
  launch, no `[Disc]` line, no `PS1 disc swap`.
- **Not read live (disclosed):** the session ended (16:44:49Z) before the hub was read (16:45:20Z), so the status poll
  during the game and the encoder argv / pointer-in-window for T15 were not read. The status poll after has no `discs`
  key (idle). The pointer stayed parked at 960 × 540 throughout (nothing moved it; read 16:35Z and 16:45Z), and both
  PS1 starts run RetroArch full screen (T17's window read at 16:34:00Z: 0,0 1920 × 1080, the pointer inside); the
  encoder's `-draw_mouse 0` read on T14 and T17 (the one builder for every capture).
- **Read:** C37 PS1 **MET** (the user's lines on T17 and T15). C38 one-disc: **MET** — no CHANGE DISC (the user), no
  `discs` in `launch_ports` or the heartbeats.
