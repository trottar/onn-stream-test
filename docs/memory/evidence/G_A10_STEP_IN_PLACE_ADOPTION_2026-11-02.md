---
memory_schema: 1
as_of: 2026-11-02
status: G-A10 ADOPTED (the user's "Adopt", 2026-11-02): PRIVYHUB_STEP_IN_PLACE=1 is the FOURTEENTH adopted line (step-in-place.conf). The window VALID with no ladder step in it (the LAN starts at the top); host gates met; --check ok on fourteen. Session A 2026-11-03 02:26-02:50Z. Nothing else adopted; nothing committed
---

# G-A10: `PRIVYHUB_STEP_IN_PLACE=1`, the fourteenth line

Task: `handoffs/G-A10_STEP_IN_PLACE_ADOPTION_TASK.md`. The decision rests on HOME-1 C2
(`HOME_1_TRIP_CLOSE_AND_QUEUE_L_CELLS_2026-11-02.md`): two steps were spliced onto the same stream in 0.9 / 6.1 ms,
with no SSRC change and no stall. Today's restart of the same steps gave 235 / 428-ms gaps (C3). B32's host half:
`companion/step_in_place.py`. Directory: `g_a10_2026-11-02/`.

## 1. Precondition (02:26Z)

All met:
- thirteen lines; `--check` ok; `fcd924c2…` CONFIRMED; `privyhub-diag` active; no `e3_flag.conf`; no game;
- one device paired; Hub host empty; the newest `token_issued` lan; 5 GHz (5180 MHz);
- the seven client properties empty; units: the companion and `privyhub-diag` only;
- HEAD `e0155d1c`; the tree clean.

**One change appeared during the task:** at 02:27:01Z session B appended a line to `handoffs/SESSION_B_STATUS.txt`.
Its queue M precondition stopped, because this record did not exist yet. That line is B's, not this task's.

## 2. The adoption diff (`patches/G-A10_STEP_IN_PLACE_ADOPTION.md`, `g_a10_applied.diff`)

- **The form** is G-A7's applied form:
  - `tools/e1_suite.py` defines `STEP_IN_PLACE` (the comment `G-A10 (adopted 2026-11-02, the user)`) and puts it in
    `ADOPTED`, making **fourteen**;
  - the preflight reads `drop_in_step_in_place` and requires it in `ok`;
  - `e3_state.py`, `e1_remote.py`, `test_e1_remote.py`: wording only;
  - `ADOPTED_E3` is left as it is.
- **Checks:** predecessor and after sha256 recorded. `git apply --check` OK, then applied; the tree diff equals the
  applied diff; `git diff --check` clean.
- **Tests, green from the tree** (`tests.txt`):
  - `e1_suite --self-test` OK; `test_e1_remote` 21 OK; `test_c3_l4_nft_night` 33 OK;
  - `tests/step_in_place` 15 OK; `tests/remote_umbrella` 10 OK; `tests/link_recovery` 9 + 7 OK.

## 3. The drop-in and the restart

- **The drop-in:** `~/.config/systemd/user/privyhub-companion.service.d/step-in-place.conf`, written with the file
  tool (`step-in-place.conf.copy`):

  ```
  [Service]
  Environment=PRIVYHUB_STEP_IN_PLACE=1
  ```

- **The restart:** `daemon-reload` and the restart ran as a separate command at 02:28:03Z.
- **The environ read back fourteen lines** (`environ_after_restart.txt`).
- **`--check` ok on fourteen:** `drop_in_step_in_place` true; `link_recovery.stack` all six `implied 1`; APK
  CONFIRMED.
- **No config row exists for this line.** B32's code writes no `step_in_place_config` row (none anywhere in
  `companion/`; the module is imported at `native_stream.py:76` when the line is set). "By the drop-in alone" is shown
  by the environ, by `--check`, and by a step's `in_place` keys.

## 4. The confirmation window (pre-registered, `g_a10_preregistration.txt`, sha256 `a4fa9edb…6253`, hashed before the run)

- **The run:** one E1-PS1-STREAM `--e2 --window 600` on the LAN, with no `e3_flag.conf` and no property.
  - Runner: `g_a10_window.py`, G-A7's runner for fourteen lines and the PS1 workload (`g_a10_window_vs_g_a7.diff`).
  - Unit `privyhub-g-a10-window` (`--collect`).
  - Session PLAYING at 02:32:04Z, class `lan`; the 600-s window ran 02:33:34-02:43:34Z; the bye at 02:43:35.6Z.

| row | read | result |
| --- | --- | --- |
| W1 the flag by the drop-in alone | 58 / 58 environ reads at fourteen lines with the flag; no `e3_flag.conf`; `e3_state` mid-window ok-shaped | **MET** |
| W2 the steps | **no step in the window**: the rung was 7000 throughout (a LAN session starts at the top and saw no pressure step-down), so there were 0 `transition` / `transition_done` rows; there was no `in_place: false` / `in_place_fallback` anywhere in the ladder log. The proof of the behaviour is `tests/step_in_place` (15 OK from the tree) and HOME-1 C2 (two steps over the overlay, 0.9 / 6.1 ms) | **none (no step)**, as pre-registered |
| W3 host gates | RetroArch 59.997, capture 59.996, dup+drop 0.1 / min; the suite's status OK | **MET** |
| W4 stall pauses | 2, both **real stalls**: 02:43:06 (431 ms; `input_release` `why: loss`, method `state`) and 02:43:28 (488 ms; `why: uplink_loss`). B33 rewound only with loss behind them, as built. Silences 0 (no uplink gap ≥ 250 ms); hitch 32 s in 692 s = **27.7 s / 10 min** (L 25, G 9, R 6, C 0); 5 GHz in 29 / 29 band reads | MET (0 outside a real stall); hitch reported |
| W5 the teardown | the bye; `flags_absent` true; fourteen lines; `--check` ok on fourteen; APK CONFIRMED | **MET** |
| W6 `privyhub-diag` | active throughout; a copy at 02:32:10Z and later, after the 02:28:03Z restart; the `sessions.jsonl` row for the window's session written at 02:46:12Z (the file's time), **155 s** after its end at 02:43:36.6Z | active and the chunk **MET**; the row **5 s past the 150-s bound** (the keeper writes on its 60-s tick) |

**The link this evening:**
- The onn sat at **−67…−69 dBm** on 5180 MHz, tx 175-260 Mbit/s. That was already so at 01:50Z, during HOME-1 C4,
  and on the trip it was −51…−56.
- Post-FEC loss was 3,647 packets in the session (361 / min in the window). It came mostly in its last ~2 min: bursts
  of 100-434 per heartbeat from 02:41:49Z.
- None of it is a step's: the rung never moved.
- **The window is valid**: it ran to its end, 5 GHz throughout, fourteen lines throughout, no property set. The loss
  is the room's radio tonight, and is worth a look before the next bench evening.

## 5. The state now

- **The fourteen adopted lines:**
  1. `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live` (`adaptive.conf`);
  2. `PRIVYHUB_EPG_GUIDE_INDEX=cached` (`epg-index.conf`);
  3. `PRIVYHUB_SNES_CORE=snes9x` (`snes-core.conf`);
  4. `PRIVYHUB_RECOVERY_TRIGGER=v2` (`recovery.conf`);
  5. `PRIVYHUB_SNES_CAPTURE_FIX=output_rate` (`snes-capture.conf`);
  6. `PRIVYHUB_OVERLAY_PROVIDER=tailscale` (`overlay.conf`);
  7. `PRIVYHUB_SESSION_IDENTITY=v2` (`session-identity.conf`);
  8. `PRIVYHUB_AUDIO_CODEC=opus` (`audio-codec.conf`, G-A2);
  9. `PRIVYHUB_LINK_REPORT=1` (`link-report.conf`, G-A3);
  10. `PRIVYHUB_LINK_RECOVERY=1` (`link-recovery.conf`, G-A4; B33 inside it since 2026-11-03);
  11. `PRIVYHUB_RESTART_FAST=1` (`restart-fast.conf`, G-A5);
  12. `PRIVYHUB_RESTART_FAST_UNLOCK=1` (`restart-fast-unlock.conf`, G-A7);
  13. `PRIVYHUB_REMOTE=1` (`remote.conf`, G-A9);
  14. **`PRIVYHUB_STEP_IN_PLACE=1` (`step-in-place.conf`, G-A10).**
- **Checks:** `--check` ok on fourteen; APK `fcd924c2…` CONFIRMED; no `e3_flag.conf`; the ten client properties
  empty.
- **Units:** only `privyhub-companion` and `privyhub-diag` are active; the window's unit was collected.
- **Off:**
  1. Delete `step-in-place.conf`.
  2. `systemctl --user daemon-reload`, then `systemctl --user restart privyhub-companion`.
  3. Reverse `g_a10_applied.diff`.

  Each step then restarts the encoder as before (a new SSRC, a ~0.2-0.4-s gap).
- **Files:** the patch, the applied diff, the predecessor and after sha256, `tests.txt`, the drop-in copy, the window
  runner and its diff, the state script, the pre-registration and its hash, `window_result.json`, the console, the
  band reads, the runs' logs, `diag_sessions_row.jsonl`, `check_end.json`, `units_end.txt`, `redact_check.txt` and
  `manifest.sha256`.
