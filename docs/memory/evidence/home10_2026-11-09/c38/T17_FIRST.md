# The Stage-3 start (~16:31-16:34Z): a four-disc PS1 set (T17), not a one-disc title

- The user's message (verbatim): "Touchpad didn't do anything" / "There is now a disc change button. But it causes the
  end button to run off the screen". No "Stage 3" word sent: read as a status report (the stage not advanced).
- **Hub:** `launch_ports` 16:31:55Z ps1, `device_args` 1-2, `capable` false, **`discs` 4, `disc` 1**; the game log
  `[Disc] Setting disc in tray: 1/4` at the launch; heartbeats 27 × `discs 4 / disc 1`, then 7 × `disc 2`. Two
  leave / return cycles (`session_end_bye` 16:32:41Z, 16:32:55Z; no new launch). **`disc_swap` 16:33:46Z: `ok` true,
  `from_disc` 1, `disc` 2, `discs` 4, `changed` true, `steps` 1, `ms` 953**; the game log `Ejected virtual disc tray.`
  → `Setting disc in tray: 2/4` → `Closed virtual disc tray.` → `PS1 disc swap: 1 -> 2`. A session 16:33:57-16:34:04Z,
  then the game stopped (RetroArch's own unload, no fault). The `GET_STATUS` after the swap was not read (the game had
  ended before the read).
- The hub's pointer read inside the full-screen RetroArch window (960, 540; window 0,0 1920 × 1080) at 16:34:00Z; the
  encoder carried `-draw_mouse 0`.
- **Readings:** C37 PS1 — "Touchpad didn't do anything" (no pointer). C38 — the entry present on a multi-disc set and a
  change made from the bar, `ok` true. **A defect (the user's): with CHANGE DISC in the bar, END runs off the screen**
  → to B (B71's bar layout). The one-disc check (CHANGE DISC absent) not yet made: this was not a one-disc title.
