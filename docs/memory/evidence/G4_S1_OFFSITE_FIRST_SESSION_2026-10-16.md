---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: af3ed73 (the G4-S1 launch uncommitted beside it, not touched)
---

# G4-S1 — the first off-site session

**Classification: MEASURED — 2 of 3 suite runs valid (run 1, run 2: PLAYING over the overlay). Run 3 NOT STARTED.**

- **Gate 1** (setup through G3 over the overlay) and **gate 2** (PLAYING within the wait) are met for both valid runs.
- **Gate 3** (host side) is **NOT EVALUABLE**. The remote row recorded neither RetroArch's FPS nor the encoder's
  progress (§6).
- **Run 2's window is mixed.** The overlay ran to the hotspot toggle. The stream after the toggle was set up over
  the LAN.
- Measurement only; nothing adopted; nothing committed.

- Written from the files (`g4_s1_analysis.py` → `g4_s1_read.json`, `validity.json`), against
  `g4_s1_preregistration.txt` (sha256 `2d6acf5d…7e96`, re-read at the close, unchanged):
  - `runs/E1-PS1-STREAM-REMOTE/run<n>/`: `summary.json`, `telemetry.jsonl`, `status_poll.jsonl`, `path.jsonl`, the
    sampler summary;
  - the companion's heartbeat, recovery and controller-gap logs;
  - `logs/session_audit.jsonl`.

  The audit is reduced to time, event, routing evidence, `sig_v` and "paired". No address, token or device id.
- Tasks: `handoffs/G4-S1_OFFSITE_FIRST_SESSION_TASK.md` (Part 1: `G4_S1_LAUNCH_2026-10-16.md`; Part 2: this).
  **Baseline `af3ed73`.**
- The user's own account is §7, recorded as the user's report and dated, not as readings.

## 1. The setting and the substitution

- The onn was on `<the hotspot>`, a phone hotspot standing in for §G2's travel router, with the Tailscale app on the
  onn standing in for the router's overlay.
- The hub was at home, wired, on the seven adopted lines, plus `PRIVYHUB_WAN_TELEMETRY=1` for the runs (A1).
  `PRIVYHUB_WAN_ADAPTATION` was absent.
- The overlay before the runs: connected, path **relayed**, 2 devices online on `<the tailnet>` (the launch record).

## 2. Per run

### Run 1 — valid

- **Times:** PLAYING at 22:50:56Z, 4.7 min into the 15-min wait. Window 22:52:26-23:02:26Z.
- **Endpoint:** class **overlay** (hash `e53b0955f641`); the client's control peers were classed local and overlay.
- **Profile:** `native_game_720p60_reference`, 1280×720, 7000 kbit/s; the rung polled 7000 ×69.

| §G4 item | reading | source |
| --- | --- | --- |
| authenticated control / setup | `token_issued` 22:44:20Z, `routing_evidence: overlay`, `sig_v` 2, `overlay_declared` true, games/tv/vod/diagnostics. It came 1 s after a `session_refused token-unknown` on `/plugins/games/systems`: the token predated 22:41's flag restart, and the client retried once. That token served both runs; no fresh `token_issued` at either run's own start (the token lasts 8 h). **No `legacy_setup`** all evening | audit |
| games discovery / launch | a `media_session` for box art at 22:44:23Z over the overlay (the list's artwork loaded); the launch reached PLAYING | audit; the console |
| video | PLAYING; rendered **57.16 fps** | heartbeat (the suite's `key`) |
| process audio | heartbeat audio underruns **2,344**; audio heard: not reported by the user | heartbeat; §7 |
| controller input | **one controller-silence recovery pause** (below) | recovery log, gap log |
| Pause / Resume | the user reported it worked (§7); no other record of the hand action | §7 |
| Save / Load | the user reported it worked (§7) | §7 |
| end / teardown | the suite stopped the game; `game_active` false | `summary.teardown` |

**The recovery event in run 1:**

- 22:55:43.5Z: a controller-input gap of **25.3 s** (gap log).
- 22:55:48.9Z: `desync_pause` (trigger `controller_silence`).
- 22:56:13.4Z: `resumed`, a **24.5-s pause**.
- The overlay path read `relayed` from 22:55:52Z to 22:56:23Z, then direct again (`path.jsonl`).
- The heartbeat's largest last-output age was 25.5 s.

### Run 2 — valid; its window mixed

- **Times:** PLAYING at 23:07:36Z, 9 s into the wait. Window 23:09:06-23:19:06Z.
- **Endpoint:** class **overlay** (hash `e53b0955f641`); 7000 ×69.
- **Its window has two streams** (the files, §4):
  - the overlay stream to 23:12:47.6Z;
  - a 157-s outage;
  - from 23:15:24.97Z, a stream whose setup was a **LAN** `token_issued` (23:15:01Z, `routing_evidence: lan`,
    `overlay_declared` false).
- The §G4 items are as run 1:
  - the overlay token reused;
  - rendered 59.29 fps over the window;
  - audio underruns 43;
  - **no recovery pause**; 54 controller gaps of 252-1,894 ms, all after 23:15:22Z;
  - the teardown clean;
  - Pause/Resume and Save/Load per the user.

### Run 3 — not started

- `[e1 23:19:11Z] run3: idle gap 300s`
- `[e1 23:24:11Z] run3: waiting up to 900s -- start a PS1 game on the onn`
- `[e1 23:39:11Z] run3: FAILED -- RuntimeError: no stream reached PLAYING within 900s`

No game was started in its wait. By the user's account, the third hotspot session and the LAN check came before it
(§5). It is treated as **not started**, not failed. No run is replaced (the pre-registration replaces only a void).

### The gates

| gate | run 1 | run 2 |
| --- | --- | --- |
| 1. setup through G3 over the overlay (`token_issued` overlay; endpoint class overlay) | **met as read**: the overlay token of 22:44:20Z, before the run (not at its start); class overlay | **met as read**: the same token; class overlay at PLAYING |
| 2. PLAYING within `--wait` (900 s) | **met** (4.7 min) | **met** (9 s) |
| 3. host side: RetroArch ≥ 59.9, capture 60 ± 0.1, dup+drop ≤ 0.2/min | **NOT EVALUABLE** | **NOT EVALUABLE** |

**Why gate 3 is not evaluable** (from the files and `tools/e1_remote.py`):

- The RetroArch title log (`title.txt`) holds the window title without the "FPS / Frames" counter: 0 titles with FPS.
  The local suite writes a per-run counter override for that counter, and the remote row does not.
- The remote row starts the sampler without `--e2` and keeps no `encoder.jsonl`, so the capture rate and dup+drop
  are not recorded.
- Host CPU is reported beside: 12.78 / 10.03 %. In % of a core: companion 24.5 / 18.5, RetroArch 34.9 / 37.1,
  encoder 44.7 / 42.8.

## 3. Reported (not gated)

| | run 1 | run 2 (whole window) | run 2, overlay part (to 23:12:47Z) | run 2, after the toggle (from 23:15:25Z; LAN setup) |
| --- | --- | --- | --- | --- |
| client reports / span | 282 / 9.4 min | 214 / 7.1 min | 108 / 3.6 min | 103 / 3.4 min |
| delivered goodput (kbit/s, `receiver.recent_mbps` mean) | 7,065 | 7,118 | 7,054 | 7,262 |
| post-FEC loss /min (telemetry / heartbeat) | 2,283 / 2,259 | 284 / 289 | 14.2 / 13.9 | 575 / 586 |
| pre-FEC loss /min (heartbeat: lost + FEC recovered) | 2,298 | 308 | 29.2 | 608 |
| FEC recovered /min; unrecoverable groups | 38.8; 24 | 18.3; 46 | 15.3; 4 | 21.9; 42 |
| resyncs (heartbeat) | 3 | 3 | 0 | 3 |
| rendered fps | 57.16 | 59.29 | — | — |
| RTT, control echo (ms, median / p95) | 120 / 383 | 121 / 452 | 125 / 217 | 86 / 626 |
| overlay path (10-s polls in the window) | direct 56, relayed 3 | direct 27, relayed 6, no-peer 26 | | |
| `wan` last-window class (per poll) | clean 35, lossy 18, path-changed 2, starved 2 | clean 26, lossy 14, starved 3, none 1 | | |
| `wan` session class at the end | path-changed | lossy | | |
| hub's tailnet-interface tx (Mbit/s, window mean) | **11.42** | 4.26 (the overlay carried ~3.7 of the 10 min) | | |

- **Path changes** (`path.jsonl`):
  - run 1: direct → relayed 22:55:52.999Z → direct 22:56:23.8Z;
  - run 2: direct → relayed 23:13:22Z → no-peer 23:14:03Z → relayed 23:14:13Z → direct 23:14:23Z → relayed
    23:14:44Z → **no-peer 23:14:54Z**, to the end.
  - `connected` was true in every poll; that is the hub's own state.
- **The wire rate against the planning figure** (reported, not judged): run 1's overlay-interface tx averaged
  **11.42 Mbit/s** at the 7000 rung.
  - §G4's planning figure is 10-11 Mbit/s outbound.
  - At home, 720p/7000 measured 11.6 Mbit/s on the wire (E2-S1 §6). C5-M3 measured 8.60 Mbit/s at 7000 and 5.02 at
    720p/4000.
- **Host-side readings, reported:** host CPU 12.78 % (run 1) and 10.03 % (run 2); the ladder held 7000 throughout.

## 4. The reconnect in run 2 (the hotspot toggle)

- **The recovery log:** `session_ended` at **23:12:47.6Z**, then `session_started` at **23:15:24.97Z**, a
  **157.4-s** gap, and another `session_started` at 23:15:45.4Z.
  - **No `desync_pause` and no `resumed`.** So the files show the session ending and a new one starting, not the
    pre-registered "recovery pause, then a resume".
  - The client's reports stop at 23:12:51Z and resume at 23:15:23Z (152 s).
- **The path:** relayed at 23:13:22Z (about 35 s after the session ended), no-peer and back twice by 23:14:44Z, then
  **no-peer from 23:14:54Z to the window's end**.
- **The setup after the outage was LAN-routed:** `token_issued` 23:15:01Z, `routing_evidence: lan`,
  `overlay_declared` false, then a box-art `media_session` on the LAN at 23:15:08Z.
  - So in these files the stream after the toggle did not come back over the overlay: it came back after a LAN setup.
  - The user's account of this run is in §7. The two are set side by side, not reconciled.
- **On the stream after 23:15:25Z:** loss 586/min, 3 resyncs, RTT p95 626 ms, and the 54 controller gaps.

## 5. Outside the suite's captures: the third hotspot session and the LAN check (audit, heartbeat and recovery logs)

- **Before run 1's wait** (in run 1's idle gap, 22:41:16-22:46:16Z), the heartbeat log has three short client
  sessions: 22:44:42-22:45:11Z, 22:45:14-22:45:31Z and 22:45:36-22:45:46Z.
  - The recovery log shows `session_started` / `session_ended` at 22:44:52 / 22:45:14Z and 22:45:41 / 22:45:49Z.
  - They ran over the overlay token of 22:44:20Z. None is a suite run.
- **In run 2's idle gap** (23:02:31-23:07:31Z): the client's heartbeats continued from run 1's session to
  **23:07:21Z**, with no reset of the session's elapsed time.
  - The recovery log has **no `session_started`** between run 1's `session_ended` (23:02:26Z) and run 2's 23:07:40Z.
  - The audit has no `token_issued` then; the token of 22:44:20Z stayed valid.
  - These files cannot separate a third hotspot session there from run 1's client continuing. The user reports one
    (§7).
- **The LAN check:**
  - **`token_issued` 23:15:01Z, `routing_evidence: lan`**, `sig_v` 2, `overlay_declared` false; a LAN `media_session`
    23:15:08Z.
  - Heartbeat sessions 23:15:21-23:21:28Z and 23:21:44-23:22:15Z.
  - The LAN setup and the start of that stream lie **inside run 2's window** (it ended 23:19:06Z). The LAN stream's
    end lies in **run 3's idle gap**, before run 3's wait (23:24:11Z).
  - So the "outside the suite's windows" framing holds only for its end. Its start overlaps run 2 (§4).
- After 23:22:15Z: no heartbeat and no `token_issued` to the session's close.

## 6. What failed, and where

1. **Gate 3 could not be read** (§2): the remote row (G4-P1's `tools/e1_remote.py`) records neither RetroArch's FPS
   counter nor the encoder's progress. A harness gap, not a stream fault.
2. **Run 2's reconnect did not come back over the overlay** (§4): the session ended at the toggle, and the next setup,
   157 s later, was LAN-routed.
   - The overlay path then read no-peer to the end.
   - From these files alone it cannot be told whether the onn joined the home Wi-Fi by itself when the hotspot went
     off, or whether that was the LAN check starting early. **The hub's firewall on the tailnet interface remains
     unread (no `nft`).** No setup timed out, so it is not named as a suspect here.
3. **Run 1 lost heavily:** 2,259 post-FEC loss/min, 2,344 audio underruns, rendered 57.16. It also had one 24.5-s
   controller-silence pause, coinciding with a direct → relayed → direct path change. Reported, not gated.
4. **Run 3 was not started** (§2), by the evening's order of events, not a failure of the row.
5. **The client could not be read by the state tool before or after** (adb not reachable after the onn changed
   networks; `adb connect` is outside this task). `--check` reads not ok on `adb` and therefore on the APK. Every
   host-side field holds (§8).
6. **No session was refused** apart from the one `token-unknown` retry at 22:44:20Z. **No `legacy_setup`.**

## 7. The user's report (2026-10-16, after the session; the user's words summarised, not readings)

- The suite's run 1 and run 2 reached PLAYING over the overlay.
- The user played **a third hotspot session that the suite did not capture as run 3**; it fell inside run 2's window
  or gap.
- Then the user did **the LAN check** (Tailscale disconnected on the onn, home Wi-Fi, Hub host cleared, one PS1
  session by hand) **before run 3's wait began**, so run 3 was expected to time out.
- **Pause/Resume, Save/Load and exit worked in every session.**
- **The hotspot toggle in run 2 paused the stream, and it resumed by itself.**
- **Some picture artifacts at the start of run 1** (a different title); none in the other two.
- **About 1.7 GB of cellular data** for the evening.
- Audio and the game's response to input were not reported separately.

## 8. The state after (23:39Z)

- The telemetry drop-in was removed, the companion restarted (`flag_removed.json`): seven lines, `flags_absent` true.
- `tools/e3_state.py` (`check_after.json`): seven lines, all seven drop-ins, no `e3_flag.conf` or `e4_constraint.conf`,
  no game, no RetroArch or encoder, PS1 files identical, MainPID serves 8765.
  - **Not ok on `adb` false / APK unreadable** (the client was not reconnected; §6.5).
  - The APK was last read CONFIRMED (`59f736d2…`) at 21:26Z; nothing has been installed since.
- One device paired. The unit `privyhub-g4-s1` was collected.

## 9. A consequence for the data volume (stated, not a recommendation)

- At the 7000 rung, run 1's overlay-interface rate was 11.42 Mbit/s: about **5.1 GB per hour** of play.
- The user's ~1.7 GB is about 20 min at that rate. The overlay streams in the heartbeat log total roughly 22 min, run
  1's continuation included.
- C5-M3's 720p/4000 rung passed transport at **5.02 Mbit/s** on the wire: about **2.3 GB per hour**.
- G5-S2's remote floor is that rung (`floor_4000`). It is **recorded, never actuated**: the live actuator's validated
  ladder ends at 5000, and actuating 720p/4000 is G5-S3. Until then, an off-site session runs at 7000, or at the
  ladder's 5000 floor.

## 10. Files

- **`g4_s1_2026-10-16/`** (the launch's, plus):
  - `runs/` (run 1, run 2, run 3, `suite.log`);
  - `suite_console.log`;
  - `g4_s1_analysis.py`, `g4_s1_read.json`, `validity.json`;
  - `flag_removed.json`, `check_after.json`;
  - `redact_check.txt` (replaced, the whole directory), `manifest.sha256`, `manifest_check.txt`.
- `logs/g4_s1_git_status.txt`. ROADMAP §G4 status line. `docs/KNOWN_ISSUES.md`: the entries for §6.1-6.3.
- No sudo, no nft, no Opal access, no adb, no Tailscale change.
- No address or identifier: the endpoint as class + hash, the hotspot and tailnet as placeholders, the interface
  named generically.
- Nothing fetched, deleted, adopted or committed.
