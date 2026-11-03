---
memory_schema: 1
as_of: 2026-11-02
status: HOME-1 DONE (session A, 2026-11-03 00:38-02:05Z = 2026-11-02 19:38-21:05 EST; the user at the TV for stages 2-5). The trip closed and read; privyhub-diag running; B33 live; C1 NOT MET, C2 MET, C3 MET, C4 NOT MET, C5 INVALID; 554ccf61… NOT CONFIRMED → fcd924c2… back on the onn. Nothing adopted; nothing committed
---

# HOME-1: the trip closed, the queue L cells

Task: `handoffs/HOME-1_TRIP_CLOSE_AND_QUEUE_L_CELLS_TASK.md`; B's strings: `handoffs/SESSION_B_DONE_2026-10-31L.md`
§HOME-1 1-7. The directory is `home1_2026-11-02/`: `stage1/`, `c1/`, `stage3/` (C3 and C2), `c4/`, `c5/`, `close/`,
`preregistration.md` and its `.sha256`, `home1_driver.py`, `home1_suite_call.py`, the diff, `redact_check.txt` and
`manifest.sha256`. Times are UTC.

## The user's lines (verbatim)

- Stage 1: "Read _cowork_prompt.txt in the repo root and follow it as my prompt."
- Then: "Stage 2", "Stage 3", "Stage 3 go", "Stage 4", "Stage 4b".
- Stage 5: "Stage 5,  movie was in continue watching and started up right away".

## Stage 1: the trip, the keeper, the restart, the install (`stage1/STAGE1.md`)

- **Preconditions met:**
  - thirteen lines; `--check` ok with `fcd924c2…` CONFIRMED; no `e3_flag.conf`; no game;
  - one device paired, Hub host empty, the newest `token_issued` lan; 5 GHz;
  - HEAD `397199dd`; `privyhub-link-n1` gone.
  - adb was connected to the onn over the LAN first; the address was never written.
- **Housekeeping:** `_cowork_prompt_cap.txt` removed with `git rm`, staged (a plain `rm` was refused by the session's
  permission check).
- **The trip keeper:** stopped by its cap ("done (the cap)", 2026-11-01T23:59:00Z, 862 copies, 4306 samples). The
  manifest checks: 1837 lines, 0 failures.
- **"Read the trip"** (`evidence/reads/diag_trip_20261103T004048Z.md`): 36 sessions, 6 restarts, 5 stalls. TRIP-R2
  §1's six restarts are reproduced exactly (the times, rungs, `trigger: surface`, paused / away ms, silences). The
  rest of the weekend had no games, only VOD: the Saturday feature, and on Sunday 04:19-06:35Z one movie for 2 h 16 min
  plus a camera-source start answered 500 (`stage1/trip_read_weekend.md`).
- **`privyhub-diag`:** the session's permission check refused it (a persistent service); **the user ran B's
  command**.
  - Active at 00:53Z; `diag_check` line 6: `unit privyhub-diag active`.
  - First copy 00:57:10Z, within 5 min of its start.
  - Still active at the close, with 8 sessions logged.
- **The companion restart** at 00:42Z: **B33 live for the first time.** The `rewind_needs_loss_config` row reads
  `implied by PRIVYHUB_LINK_RECOVERY=1`, short 1000 ms.
- **Pre-registration** `preregistration.md` (sha256 `a3d8b282…f64f`) was hashed at 00:42:17Z, before the install.
- **The install** (00:43Z):
  - `554ccf61…9902` (= B's hash, the same signer) from `queue_l_built/` → `home1_installed/`;
  - read back; paired; identity v2; Hub host empty; the ten properties empty.

## The cells

| cell | what | result | the rows (each cell's `.md`) |
| --- | --- | --- | --- |
| **C1** screen loss (`surface_hold=1`, LAN) | the remote's Home, out ~5.8 s; the pad's guide button | **NOT MET** (valid) | (1) **met**: one session, `surface_lost` `held`, `away_ms` 4429, `reason: user_leave`, the picture back 522 ms after the reattach, the game paused through it. **But the report's `surface_hold.held` read 0.** (2) **not met, and not reachable on this onn:** its log shows the pad's guide press "dropped because the policy consumed it" and a HOME start. The system turns the guide button into Home before any app sees it, so it ran as a Home press. (3) **met** via that press: away ~23 s > the 12-s bound → today's restart, `surface_lost` `restarted` |
| **C3** no-rewind stall (B33 live, the overlay, 14 lines) | two step-ups with today's encoder restart | **MET** (valid) | the 01:20:24 step's 421-ms stall → `input_release` **`method: resume`, `why: no_loss_under_1s`, `held_ms` 542.5** → `resumed` 223 ms; no load into the core (the one "Loading state" line is RetroArch's undo buffer inside the save task); `rewind_needs_loss_config` |
| **C2** step in place (`PRIVYHUB_STEP_IN_PLACE=1`, 15 lines) | two step-ups | **MET** (valid) | `in_place: true`, `ssrc_unchanged: true`, `splice_gap_ms` **0.9 / 6.1**; the encoder log's `B32 in-place step: … active on the same stream`; the client report has no SSRC change and no output gap ≥ 200 ms; no `client_stall` |
| **C4** two pads (`pad_slots=stable`, LAN) | pad B first, then pad A first after a relaunch | **NOT MET** (valid) | both starts wrote the **same** map (stable across the swap), but `count` 3. **The onn's "virtual-remote" (KEYBOARD / DPAD / GAMEPAD, controller number 1) took slot 0**, so the two pads became slots 1 and 2 (players 2 and 3). `updates_by_player` rose equally on all four ([8002, 7999, 7986, 7982] → +318 each in 3 s) |
| **C5** movie drop (`vod_retry=1`, `PRIVYHUB_VOD_LOG=1`) | the Wi-Fi off ~10 s | **INVALID** | to reach the Wi-Fi setting the user pressed Home (01:57:40.5). The player was released as the app left (01:57:42.0); the range log's `client_reset` at 01:57:42 is that release. The Wi-Fi went down 01:57:48.6-01:58:04.0 with no player running, so there was nothing to retry and no `vod_client.jsonl` row. The user's "continue watching" restart at 01:58:15 resumed at the saved position (`bytes=3413136-`) "right away": today's resume, not B35's retry |

- **C3 and C2 detail:** the unit `privyhub-home1` ran one launch, 01:11:47-01:44:23Z. Both were `remote-direct`. The
  driver was CL-B16's with the cells, names, the ten properties and the pre-registration path changed
  (`home1_driver_vs_cl_b16.diff`); its dry run passed first.
- **Every cell:** the ten properties read back empty before and after its own property.
- **The game end before C5:** C4's game was still running at stage 4b, so the session ended it through the hub's own
  stop call (`POST /plugins/games/stop`, the app's exit path) before the C5 restart.

## The close (`close/`)

- `vod_retry` cleared; **all ten properties read back empty**.
- The drop-in was removed by the suite's own `teardown_flags`: `flags_absent: true`, restarted.
- Thirteen lines; no `e3_flag.conf`.
- `privyhub-diag` is still active through every restart.

## The CONFIRMED rule (CL-B7 §6, as pre-registered)

**"Every cell that ran was valid": NOT met. C5 was invalid** (the drop never reached a running player). So
`554ccf61…9902` is **NOT CONFIRMED**:
- **`fcd924c2…` reinstalled** from `cl_b14_installed/` at ~02:00:50Z: read back, paired, identity v2, Hub host empty,
  the ten properties empty.
- **`--check` ok, APK CONFIRMED** on thirteen lines. The pin was not moved.

Where no flag was set, today's behaviours held: C3 and C2 with every property empty; B33's intended difference aside.
C5's invalidity alone decided the rule. C1 and C4 being not met does not bear on the rule but does bear on the
questions.

## The reading: the user's questions

**G-A10 (C2 met).** "Adopt `PRIVYHUB_STEP_IN_PLACE=1` as the fourteenth line? Each bitrate step then keeps the same
stream (no new SSRC, no ~0.4-s gap)." C2 met every row: both steps spliced in 0.9 and 6.1 ms on the same stream,
where today's restart of the same steps gave 235 and 428-ms gaps, and one of those caused a stall pause in C3. It is
a host line, so it needs no new APK.

**Not asked; back to B with the rows:**
- **G-A11 (C1 not met):** the hold works for Home, but the report under-counts it, and the guide-button half cannot
  work on this onn because its system takes the key first.
- **G-A12 (C4 not met):** stable, but the onn's virtual-remote takes slot 0, and all four players still count.
- **G-A13 (C5 invalid):** the drop has to happen with the player in front: the hub-side shim, or the router, not the
  onn's own settings.

**B33 is not a question:** its first live stall resumed without a rewind (C3). Its off switch is
`PRIVYHUB_REWIND_NEEDS_LOSS=0`. The guard's return stays a later item.

**On the onn now:** `fcd924c28cbf70a85bb9a886caabcb07873eee2d028b6538284fce5a7ae39b96` (CL-B14's), CONFIRMED.
