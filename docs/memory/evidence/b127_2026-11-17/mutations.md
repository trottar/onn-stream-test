# B127 — mutations (each in its own copy of /tmp/b_q30as; the suite's UnderSetups class run against each)

- **M1** `h7_minigame._start`: `setup = None` (today's begin always) → tests 1, 2, 4, 5 fail.
- **M2** `party_minigame._start_steps`: the title launched by `emu.launch(game)` even with `cheat` → tests 4, 5 fail.
- **M3** `party_minigame.start`: no setup check → tests 3, 4, 5, 6 fail (a launch went ahead; the setups' tree changed).
- **M4** `h7_minigame._start`: the load into the normal `states/` instead of the session's `_state_root()` → tests 1,
  2, 4, 5 fail (the fake RetroArch, reading the session config's folder, does not find the scratch).

The copies removed after (`/tmp/b_q30as_m1`-`m4`).
