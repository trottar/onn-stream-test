---
memory_schema: 1
as_of: 2026-10-31
status: TRIP-R2 READ (session A, read-only, 2026-10-31 ~17:00-18:30Z, the user away). Friday 2026-10-30 21:00Z → 2026-10-31 10:00Z, every client session, the four episodes. Copies only; nothing restarted, adopted or committed; the log-keeper untouched
---

# TRIP-R2: Friday's play and the four episodes

Task: `handoffs/TRIP-R2_FRIDAY_GAMEPLAY_READ_TASK.md`. Everything is in `trip_r2_2026-10-31/`:
- `copies/`: the keeper's chunks joined per log. These are byte copies of `trip_2026-10-30/raw/`, already redacted by
  the keeper. The keeper's directory was only read.
- `tables/`: `sessions.md` / `.tsv`, `per_10min.md`, `per_hour.md`, `stepups.md`, `restarts_5s.md`, `counts.json`.
- `seconds/`: the golf stretch at 1 s, plus ±60 s around every restart and every stall.
- `vod/range_requests_utc.txt`: the range server's requests, redacted.
- `scripts/trip_r2_read.py`: runs on `copies/` only.
- `redact_check.txt`, `manifest.sha256`.

Titles are given as class + tag. Times are UTC. The overlay was `direct` in every game session.

The user's words: "overall ran very well, but a few massive issues".

## 0. The evening

**What was played.** 36 client sessions of 9 titles, 21:22Z → 05:30Z, with about 3 h of stream in total. Every
session was `remote-direct`, on the four WAN lines (G-A9). The onn sat at −51…−58 dBm on 5785 MHz. Control-echo RTT
was p50 111-149 ms and p95 ~390-450 ms in every session; the kart racer's first session was the exception, at
214 / 593 ms. Rendered frames were 59.7-60.1 fps in every session's median.

- **Sessions:** `tables/sessions.md`. Each row gives:
  - start and end, length, title class, core;
  - path, transitions, how the session ended;
  - `session_ended_reset` count, post-FEC loss, fps median and minimum, resyncs;
  - stalls, pauses, holds, hitch seconds (R / C / G / L, UX-R3's definition, unchanged);
  - silences and user exits, underruns, starvation, RSSI, RTT.
- **Players sending state:** not in any row. The client sends players 0-3 on every tick whatever pads are present
  (CTRL-L1), and per-player counts exist only in the live `/status` (`native_session_io.py:2719`), which no log
  keeps.
- **The 10-min table:** `tables/per_10min.md`, with the episodes marked.

| hour (UTC) | stream min | client restarts | stalls ≥ 400 ms | ladder steps | top rung | uplink silences (not the user's) | hitch s | loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10-30 21 | 20 | 0 | 0 | 4 | 7000 | 0 | 6 | 174 |
| 10-30 22 | 6 | 0 | 0 | 1 | 5000 | 0 | 2 | 50 |
| 10-30 23 | 20 | 0 | 0 | 4 | 7000 | 0 | 6 | 109 |
| 10-31 01 | 25 | 1 | 0 | 5 | 5500 | 1 | 8 | 101 |
| 10-31 03 | 33 | 1 | 0 | 5 | 7000 | 9 | 20 | 168 |
| 10-31 04 | 51 | **3** | 3 | 8 | 7000 | **17** | 28 | 75 |
| 10-31 05 | 26 | 1 | 2 | 7 | 7000 | 1 | 8 | 32 |

**Where the episodes sit:**
- **E4, the movie:** the long feature, 06:04-09:54Z (§4). The kids title at 21:18Z ran only 72 s.
- **E3, two-player football:** 01:07-01:25Z and 03:32-04:09Z.
- **E1 and E2, the restarts and golf:** 04:13-04:46Z, one stretch. Golf is where most of the restarts happened.
- **The end:** at 05:28:39Z the link went, during the PS1 brawler (`client_stall` 414 → `input_hold` → `gave_up_saved`
  05:30:40; the overlay `relayed` 05:29, `no-peer` 05:30). That is the onn leaving, not an episode.

## 1. The restart loop: corrected

**The correction.**
- **`session_ended_reset` is not a restart count.** The ladder writes it at every session start and every session end,
  including the user's own exits: 91 in the evening, 17 in 04:00-04:38Z.
- **The client restarted itself 6 times all evening**, by `restart_fast` rows: 01:20:44, 03:26:05, 04:19:21,
  04:30:12, 04:34:41 and 05:19:35. Three of them fell in 04:00-04:38Z, all in golf.
- **The other ends in that window were the user's** `session_end_bye` (the Back / pause menu): 04:09:24, 04:16:08,
  04:30:39, 04:31:15, 04:34:33.

**Every client self-restart, with the seconds before it** (`tables/restarts_5s.md`, `seconds/restart_*_pm60.tsv`):

| restart | session (title) | the seconds before | rung before → after | last step-up Δt | `restart_cause` (the client's report) |
| --- | --- | --- | --- | --- | --- |
| 01:20:44 | 14 (football) | 60 fps to 01:20:40; uplink silence 01:20:42.5 (1,736 ms) → save → `input_hold` 952 ms | 4000 → 4000 | 397 s | surface; paused 1,720 ms before the loss, away 1,787 ms |
| 03:26:05 | 20 (kart) | uplink silence 03:25:58.4 (7,467 ms) → `input_hold` → handover 5.26 s → `hold_return_armed` | 4000 → 4000 | (none in the session) | surface; paused 4,511, away 8,582 |
| 04:19:21 | 25 (golf) | `client_stall` 419 ms at 04:19:18.5, resumed via stall_end in 30 ms (rewound); silence 04:19:19.4 (1,918 ms) → `input_hold` | 4000 → 4000 | (none in the session) | surface; paused 1,877, away 2,027 |
| 04:30:12 | 26 (golf) | `client_stall` 464 ms at 04:30:10.8, resumed in 25 ms; uplink gaps 292 / 303 / 495 ms | 6000 → 4000 | 95 s | surface; paused 2,070, away 1,039 |
| 04:34:41 | (31, never PLAYING) | the user's exit 04:34:33; a new start 04:34:37; silence 04:34:39.9 (1,190 ms) | 4000 → 4000 | 363 s | surface; paused 767, away 1,188; activity created 4.3 s before |
| 05:19:35 | 35 (brawler) | uplink silence 05:19:19.5 (16,079 ms) → `input_hold` → handover → `hold_return_armed` | 4000 → 4000 | (none in the session) | (no report: the next session ended in the link loss) |

**From the code: what restarts the client** (the code reader's citations; files under
`PrivyHub/app/src/main/java/streaming/`):
- **The client sends a new `native-stream-start` only from `surfaceCreated`** (`NativeStreamActivity.kt:499-517`,
  `:794-805`). It adds `&guard_end=1` when the restart guard holds a pending restart.
  - The surface goes in `surfaceDestroyed` (`:528-571`). There `stopLocalPipeline()` (`:1098-1113`) stops the
    controller sender, audio, the receiver and the decoder.
  - The controller sender keeps sending through `onPause` (`:574-579`) and stops only there. That is the host's
    `silence` 401 ms → `input_hold` 952 ms before each restart.
- **No stall, decoder, SSRC or link path restarts the stream:**
  - link recovery gates at 1,000 ms and tears nothing down;
  - the decoder is never reconfigured (`AvcLowLatencyDecoder.kt:906-911`);
  - an SSRC change only waits for an IDR (`RtpH264Receiver.kt:699-743`);
  - the stall signal only sends datagrams;
  - the link notice is a TextView (`link_notice_shown` 0 in every report).
- **`trigger: surface`** (`RestartGuard.kt:262-283`) means the same activity instance lost its surface and got it back.
  - It was not recreated. A Bluetooth pad's configuration change would read `recreate`, because the manifest declares
    no `configChanges`.
  - `create_to_start_ms` was 153 s / 157 s / 808 s / 32 s / 4.3 s.
- **`host_ended_session: true`** only echoes the start's `guard_end`. On the host, that start ends the old session
  (`plugins/games.py:3884-3887` → `session_ended`), then `restart_fast` (`:3918-3924`) about 14 ms later.
- **So the trigger is Android taking the stream activity out of the foreground for 1-9 s.** Something came in front
  of it (pause), the surface went, and the same instance came back.
  - What came in front is not in any record.
  - The streaming code starts no activity or dialog. The window keeps the screen on.
  - Candidates are a system panel or the Home / guide button. Keys the sender does not map (`KEYCODE_BUTTON_MODE`
    among them) go to the system (`:4211`).
  - The onn's `logcat -b events` (`wm_on_paused_called` and the other package's resume) would name it, but it needs
    adb (off-LAN; not run).
- **The ~420 ms stalls before the 04:19 and 04:30 restarts are a symptom, not the cause.**
  - By the report's clocks (inference across two clocks), the activity paused about 0.5 s before the 04:19:18 stall
    began, and at about the 04:30:10 stall's onset.
  - The stall is the decoder losing the foreground. The host resumed it in 25-30 ms, and the restart followed when the
    surface went.

**Does a step-up restart the encoder? Yes, on the LAN and on the remote ladder alike.**
- `adaptive_level_transition` (`native_stream.py:2595-2640`) kills ffmpeg, spawns a new one at the new `-b:v`, polls
  for RTP, then holds a 0.75 s stability window. The resolution, fps and GOP do not change; 4000 is 720p too.
- **Every one of the 32 step-ups with a report shows an SSRC change at the client 0.3-0.8 s after the host's
  `transition`** (`tables/stepups.md`).
  - The output gap was 140-248 ms in 29 of them.
  - It was 426-430 ms in three: 04:25:30 golf; 04:37:42 golf → `client_stall` 424 ms; 05:07:16 hockey B →
    `client_stall` 417 ms.
- The two step-up stalls paused, rewound about 0.5 s and resumed. **They did not restart the client.**
- The user's read had "the 04:37:43 stall 1 s after the 4000 → 5000 transition": confirmed, but no restart followed
  it. "The 04:28:37 transition then the stall at 04:30:10": 93 s apart, not linked.
- The remote ladder differs from the LAN one only in starting at 4000 and climbing every ~187 s to 7000. That gives a
  remote session four encoder restarts in its first ~12.5 min. A LAN session starts at 7000.

**Good hours against bad.**
- **21-23Z (0 restarts):** the SNES action-adventure plus short PS1 sessions. 0 uplink silences, the rung up to 7000,
  the same RSSI, RTT and loss.
- **01-05Z (6 restarts):** the uplink silences not the user's own went 0 → 1 / 9 / 17 / 1 an hour, beginning with
  two-player football at 01:07Z.
- **Not different:** the rung (restarts came at 4000 in 5 of 6), the step-up timing (Δt 95-6,511 s), loss, RSSI,
  path, RTT and host load.
- The rows show no cause for the 300-600 ms uplink silences at 03-04Z. The client's report carries only
  `packets_sent`, `send_errors` 0 and `motion_events`, with no input-device events.
- **Inference:** a second pad on the onn from 01:07Z and the onn's own foreground events fit both the silences and the
  restarts. The hub cannot see either.

## 2. "Inputs took minutes" (golf, 04:13-04:46Z)

The per-second view is `seconds/golf_041300_044700.tsv`: 1-s rows with fps, loss, output age, uplink gaps, the rung,
the ladder state and output gap, the client's gaps and SSRC changes, frames sent, and the ladder and recovery events.

**The stretch: 7 client sessions, 33 min.**
- **Sessions 24 and 25** (04:13:15-04:16:08, then 04:16:48-04:19:21): ran at 60 fps.
- **The 04:19:21 restart.**
- **Session 26** (04:19:22-04:30:12): 10:50 at 60 fps (min 44.7). Three step-ups. Uplink gaps 296-600 ms at
  04:24:40-59, then the 04:30:12 restart.
- **04:30:14-04:34:42, 4.5 min in pieces:**
  - 25 s of play, then the user's exit;
  - 12 s in the menu, 24 s of play, exit;
  - 22 s in the menu, then 2:56 of play;
  - exit, then a fresh start restarted by the client at once (04:34:41).
- **Session 30** (04:34:42-04:46:01): 11:19, 60 fps, the step-up stall at 04:37:43.

**Were inputs delayed in flight? No.**
- Controller packets reached the host throughout every PLAYING stretch. The longest uplink silence during play that
  was not a teardown was 600 ms (04:24:42).
- The control echo was p50 125 ms and p95 ~410 ms. That makes each press land about 1/8 s later than at home, and
  sometimes 0.4 s later, which matters to a timing meter, but it is not minutes.

**Were inputs swallowed by a hold or pause? Yes, in short pieces.**
- Three stall pauses in golf (04:19:18, 04:30:10, 04:37:43) each ended with `input_release` via `stall_end`, method
  `state`: `LOAD_STATE_SLOT 9` acknowledged, 25-28 net unattended frames. That rewinds the game ~0.45 s to the stall's
  onset, and what was pressed in that ~0.45 s is gone (B9 / B12, `rewind_cores.py:243-300`).
- The uplink gaps at 04:18:45, 04:24:42 and 04:24:59 took a scratch save but had no pause and no release, so no rewind.
- The restarts loaded nothing.
- The game log's "Loading state … state9" lines are not rewinds. Seven of its eight follow "File already exists.
  Saving to backup buffer": RetroArch reading the old slot-9 file into its undo buffer at each save. The eighth is the
  user's own slot-0 load from the menu, about 04:31-04:34.

**Was the stream down or restarting while the user pressed? Yes. This is the largest part.** From the moment the
activity paused until the new session's first frame, presses went to whatever was in front of the stream or to a
stopped sender:
- about 5 s at 04:19:17.5-22.8;
- about 4 s at 04:30:10.4-14.3;
- about 2 s at 04:34:39-42.

**The longest span in which a press could not reach a running game:**
- In golf, not counting the user's own menus: 04:19:17.5 → 04:19:22.8, about 5.3 s. Only ~0.9 s ran in between, and
  it was then rewound.
- All evening: the kart restart, 03:25:54 → 03:26:07, about 13 s (paused 4.5 s, away 8.6 s).
- The user's own menu trips in golf ran to 41 s (04:16:08-04:16:49).

**No span of minutes appears.** The likeliest reading of "minutes" is the 04:30:10-04:34:43 stretch: two restarts and
three exits in 4.5 min, in which play ran in pieces of 25 s, 24 s and 2:56.

**What the record cannot see:** button presses. The sender sends every ~8 ms whatever the input, and the host keeps
no per-press or per-player row.

## 3. Two-player football (Blitz)

Six sessions: 01:07:55-01:15:21, 01:15:42-01:17:25, 01:18:10-01:22:32 (the 01:20:44 restart), 01:23:06-01:25:05,
03:32:09-03:34:00 and 03:34:16-04:09:37 (35 min).

**Which were two-player cannot be read from the rows** (§0). The setup trail in the journal and game logs:
- 01:15:33: multitap on port 1 switched on;
- 01:17:40: multitap off, pads to DualShock (the analog toggle disabled in the core options);
- 01:22:44: back to the digital pad.

That is four relaunches in 17 min, each changing the pad setup: the look of trying to get the second pad working
(inference). The 35-min session at 03:34 is most likely the two-player game.

**Link and host: flat.**
- Blitz sessions had loss 0.002-0.03 %, RSSI −53…−55, load 1.6-2.1, RetroArch 20-34 % and the encoder 36-38 %.
- That is equal to or better than the brawler, kart and golf around them.
- Per-player controller columns do not exist in the record.

**Port 2 (read-only):**
- The client tags each packet with a player number 0-3. The host makes one uinput pad per player,
  "PrivyHub Virtual Gamepad P{n}" (`native_session_io.py:1905-1913`).
- RetroArch autoconfigures P1-P4 into ports 1-4. The P2 autoconfig equals P1's apart from the name.
- The core gets `--device` for ports 1-2 (1-4 with multitap) from the same profile (`emulator_manager.py:5485-5508`),
  so port 2 always matches port 1.
- The 03:34 log shows ports 1 and 2 both "PlayStation Controller". Blitz's override is `ps1_multitap: off`.
- **With multitap off the host side has no mismatch.**

**The client side (code, not a row):**
- `NativeControllerSender.kt:447-474` hands out player slots in the order the devices first send input. It clears
  them at every start and stop (`:111`, `:136`), so P1 and P2 can swap at every relaunch or restart.
- The motion filter (`:278`) accepts any device with stick or hat axes. A pad's touchpad or motion sensor could take a
  slot and push the second pad to P3, which a PS1 without multitap does not read.

**Verdict:** the two-player trouble was the pad setup and the client's player-slot assignment, not the link or the
host. This is inferred: the record cannot show which pad held which slot.

## 4. The movie that stopped at ~1:50

**The kids title (21:18:57-21:20:10Z)** played for 72 s and ended with the client's `/stop` 3.5 min before the first
game. Neither 1 h 50 min nor 1 min 50 s after its start shows anything; it was already stopped at 21:20:48.

**The feature (movie B)** is the one that fits (`vod/range_requests_utc.txt`):

| UTC | event |
| --- | --- |
| 06:04:10 | start; requests to 06:04:41 |
| 06:13:42 | start again, with no `/stop` in between: a manual restart after ~9 min; the open-ended streaming GET at 06:13:59 |
| 06:13:59 → 09:53 | **no request at all for 3 h 40 min** (one open-ended GET carries a whole movie, so that alone says nothing) |
| 07:55:34 | the overlay first leaves `direct` (`relayed`; `direct` once at 07:56:34; `relayed` from 07:57:34). All evening this follows the traffic stopping by 1-2 min (21:43 → 21:44, 23:21 → 23:23, 01:38 → 01:39, 09:54 → 09:55) |
| 09:53:51 | `/stop`, start 09:53:56, requests 09:54:01-16, `/stop` 09:54:36: the manual continue |

**Placing the stop:**
- The traffic stopped at about 07:54Z, about 1 h 40 min after 06:13:59.
- With the ~9 min of the first try resumed (the client offers a resume over 30 s), that is about 1 h 49-50 min into the
  movie. **The "1:50" is 1 h 50 min** (inference).

**Which side stopped:**
- **Not the server.** No 4xx or 5xx response, the companion's PID was unchanged and the range server was not
  relaunched. The load was 0.03-0.13 and no game was running.
- **The connection was closed or reset from the client side:** the BrokenPipe / ConnectionReset tracebacks carry no
  timestamp.
- **The onn stayed on the tailnet** (`peer_ready` true) until 09:55. It did not sleep or leave.
- **No new request reached the server after the stop.** The player did not reconnect.
- **The client's VOD player** on an error (`MainActivity.kt:15564-15612`) saves progress, marks the source
  "recently failed", shows "Playback error" and stops, with no retry of its own. That matches "needed a manual
  continue".
- **The read:** the player stopped and did not retry. A brief link fault on the long-lived connection cannot be told
  apart from a player-side fault in this record.

**What the hub cannot see:**
- when the connection actually broke;
- byte offsets, Range headers and bitrate, so the position cannot be computed;
- the player's state and error (the onn's logcat);
- overlay changes under 1 min.

## 5. The reading

**E1, the self-restarts.**
- **Cause:** something on the onn takes the stream activity out of the foreground for 1-9 s (Android pause, then
  surface loss). The same activity comes back and starts the stream again. That happened 6 times in the evening, 3 of
  them in golf.
- **It is not the ladder.** Every step-up does restart the encoder, and 3 of 32 gave a ~430 ms gap and a host stall
  pause, but those resumed.
- **What the system did:** B22 / B24's fast restart brought the picture back in ~1.3 s of host time, but only after
  the onn returned. The stall pause and rewind are built for link stalls.
- **Why it was not enough:** a lost surface is not a link event. Each one costs the session, a rewind, and the rung
  back to 4000.
- **Fixes, B32:**
  - (a) log the foreground loss on the client (the pause reason where readable, input-device add/remove, key codes
    that reached `super.dispatchKeyEvent`) and keep `restart_cause` in a row the host writes at the restart, not only in
    the next report;
  - (b) consume the guide / Home-class pad keys in the stream activity, or show why it left;
  - (c) make a step-up change the bitrate in place (VAAPI rate control at runtime, or a new IDR without a new process
    or SSRC), so it never makes a 430 ms gap.
- **The 4000 pin would not stop E1.** As written in `_cowork_prompt_cap.txt` it does not take effect anyway: an
  explicit `PRIVYHUB_REMOTE_RUNG_CAP` beside the umbrella is built with no ladder and inactive
  (`remote_ladder_flag_absent`), and the umbrella then drops its own cap. Session A found this 2026-10-31 ~16:55Z and
  did not apply it.

**E2, golf inputs.**
- **Cause:** the presses went into the restarts (≤ 5.3 s each) and into 3 stall rewinds (~0.45 s each, the presses
  discarded), on top of a 125 / 410 ms control echo that a swing meter feels.
- **No minutes-long delay is in the rows.** The uplink kept arriving.
- **What the system did:** the stall pause and rewind protected the game state as designed.
- **Why it was not enough:** for a timing game, a rewind that drops a press is itself a lost input.
- **Fix, B33:** no rewind on a sub-second stall or silence with no packet loss behind it (pause only, or nothing).
  After a restart or resume, show the user that the stream is live again before input counts. Measure input-to-photon
  on the WAN.

**E3, two-player football.**
- **Cause:** the pad setup and the client's slot assignment: slots in first-input order, reset at every start, with
  any stick-axis device eligible. The link and host were flat.
- **What the system did:** nothing; it does not know which pad is which.
- **Fix, B34:**
  - stable player slots by device descriptor across restarts;
  - exclude non-gamepad input devices;
  - put the slot map in the report and the host's rows;
  - test multitap and DualShock per title.

**E4, the movie.**
- **Cause:** the long feature's stream connection ended from the client side at about 1 h 50 min into the movie, and
  the player stopped with no retry. The hub was healthy and no request reached it.
- **What the system did:** the client saved progress, so the manual continue resumed.
- **Fix, B35:** VOD auto-retry on a load or IO error (resume at the saved position after reconnecting), a timestamped
  per-request range log on the hub (Range, bytes, duration, how it closed), and the player's error in a row.

**B36, the permanent diagnostics keeper:** a trimmed B30, always on, so that each of the above is answerable from the
hub alone. It needs the client's foreground and input-device events, the range log and per-player controller counts.

**The one thing to do today if you play again:** nothing on the hub.
- If two people play: after each launch or restart, press a button on pad 1 first, then on pad 2, with the pads'
  Analog lights off.
- Keep off the pads' Home / guide buttons.
- If the movie stops, the resume from saved position works.

## 6. Method and limits

- **Sources:** the keeper's copies to 2026-10-31T16:58Z, plus the live `logs/server.log`, read only and never copied
  (it holds addresses and titles; `vod/` has the redacted extract). No game ran after 05:30Z; the keeper's samples
  show idle to 17:00Z.
- **The code reads** (the client restart paths, the encoder restart, port 2, VOD) were done by three read-only
  readers. Each claim above carries their file:line.
- **What is inferred, not read:**
  - which sessions were two-player;
  - what took the foreground;
  - the movie's position at the stop.
- **The hitch definition** is UX-R3's, unchanged. Output gaps from the client report are placed by the
  median(heartbeat received − elapsed) of each session.
- **The RTT per session** is the WAN row closed between that session's end and the next start (±1 row where sessions
  were seconds apart).
