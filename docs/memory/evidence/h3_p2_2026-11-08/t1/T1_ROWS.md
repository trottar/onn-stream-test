# T1, the rows (the second launch, 2026-11-08 02:39:21-02:48:38Z, after A's audio-wait change)

The user (verbatim): "T1 done" / "Save failed but everything else ran surprisingly well. No real issues, maybe the
occasional frame tears".

**Between the attempt and this run (disclosed):** A changed B49's code in the working tree (`h3p2_audio_wait.diff`,
uncommitted): the launch now waits (≤ 45 s) for the PCSX2 PID's PulseAudio sink-input before it returns, and logs
`PS2 audio: sink-input <s>s`. `tests/ps2_session` 35 / 35 OK after it (91 s: two launch tests now wait out the 45-s
bound with no audio; B should fake it). The companion restarted at 02:20:51Z (no game, no movie; sixteen lines; the
journal clean). **Two things differed from the attempt:** the sink-input was there 0.3 s after the window, and PINE
answered, so the pause / resume used PCSX2's hotkey (the attempt fell back to SIGSTOP); which of the two cured it is not
separated.

**The game log:** `PS2 launch: pcsx2 players=2 multitap=false adapter=named` 02:39:21.402Z; `PS2 audio: sink-input
0.3s` 02:39:23.251; `PS2 pause: hotkey` 02:39:23.394 (the paused handoff); `PS2 resume: hotkey` 02:39:30.812; then
pause / resume at 02:42:01.4 / 02:42:16.4 and 02:44:28.5 / 02:44:43.5 (the user did Back / Resume twice); `PS2 pause:
hotkey` 02:48:31.6 (Back); `PS2 exit: sigterm 0.5s` 02:48:38.2 (Stop).

| row | reading | result |
| --- | --- | --- |
| P7a the list | "PlayStation 2 (115)" = the folder's 115 distinct titles; the drive's folders unchanged (read at the close) | met (folders: the close) |
| P7b launch | the host's `PS2 launch` 02:39:21.4 → the stream's first heartbeat with frames 02:39:24.1 (**2.7 s**, the paused first picture) → `session_started` (the game running on the TV) 02:39:30.8 (**9.4 s**); bar 90 s; the `PS2 launch` line and the `ps2_session` row present | **met** (margin ~80 s) |
| P7c pads | PCSX2's log: four `PrivyHub Virtual Gamepad` opened, instance 1-4 = SDL-0..3 = player id 0..3 in creation order (Pad1 = SDL-0, Pad2 = SDL-1); the heartbeat's `updates_by_player`: slot 0 52 → 4,379, slot 1 30 (all in the first minute), slots 2-3 0; the user: "everything else ran surprisingly well" | **pad 1 met; pad 2 reached the hub but player 2 was barely exercised** (30 changes, the user's line does not name it) — not fully shown |
| P7d pause / resume | three Backs: `PS2 pause` 0.14 / 0.04 / 0.14 s after `session_ended`; two Resumes: `PS2 resume` 0.005 / 0.004 s before `session_started` (and the launch's release 0.006 s before); method **hotkey** (PINE answered) every time; the game continued (the user's line) | **met** (margin > 2.8 s) |
| P7e hitches | the keeper's three session rows (150 + 132 + 227 = 509 s of play): **0 hitch seconds** (R / C / G / L all 0) → **0.0 per 10 min**; bar 29.7 (the keeper's PS1 reference 27.7 + 2); the capture minute (02:45:31-02:46:31) is inside the third row and adds none | **met** (margin 29.7) |
| P7f P2 | `ps2_p2_frames.py` on the minute-6 capture (02:45:31-02:46:31Z, B's command): 3,597 frames, median **60**, corrected minimum **54** (bar 55), 0 static seconds, 0 single repeats; the 54 is the capture's first second (with one 117-ms gap); seconds 17 / 34 / 50 read 59, all others 60 | **not met** (by 1, in the capture's first second) |
| P7g M2-M6 | over 02:39:30-02:48:31: no core ≥ 90 % for more than 1 s (per-core max 99 % for one second; busiest core median 18 %); threads EE 37 % mean / 67 % max, VU1 24 %, GS 24 %; GPU median **24 %** (p95 26); Tctl max **65.4 °C**; frame-time p95 **16.7 ms** (the capture's unique-frame intervals; p99 17.0); the drive: 21 reads, 0 writes, no stall (max r_await 361 ms) | **met** |
| P7h exit | `PS2 exit: sigterm 0.5s`; no `AppRun` or FUSE helper left; the next PS1 launch not tried (no PS1 tonight, the user's decision) | **met** (the PS1 half not read) |
| P7i feel | "Save failed but everything else ran surprisingly well. No real issues, maybe the occasional frame tears" | recorded |

**Notes:**
- **Play time:** 9 min 1 s from the release to the last Back (8 min 29 s of play in the keeper's rows), a little under
  the 10 minutes; valid (the pads on the onn; no stream restart: three user-ended sessions, `restarts` 0).
- **"Save failed":** PCSX2's two hub memory cards (`data/games/ps2/memcards/`) read UNFORMATTED at boot and no
  memory-card write is logged; PrivyHub's own save states are off for a PS2 session by B49's design. Which save the
  user meant is not in the logs → to B49b (format the hub cards at first use, or say why a save fails).
- **"Occasional frame tears":** PCSX2's Vulkan present mode / vsync with x11grab is not read here → B.
- **PCSX2's log** also lists `Invalid binding: 'SDL-0/A' … 'SDL-1/Y'` (A / B / X / Y names, both pads) before the pads
  open; the ini's face buttons are `FaceSouth` / `FaceEast` / `FaceWest` / `FaceNorth` (valid). The source of the A / B
  / X / Y bindings is not found in the ini → B.
- **The keeper labels these PS2 sessions as PS1** (its title class and core field) → B (diag keeper).
- A's sampler script crashed at 02:39:31Z on its own bug (a file-position call) and was restarted at 02:39:58Z; the
  first script's `mpstat` / `iostat` / `pidstat` kept running through it (the series is continuous); the 1-Hz GPU /
  Tctl series misses 02:39:31-02:39:58.
