---
memory_schema: 1
as_of: 2026-11-08
status: H3-P2 DONE (session A, 2026-11-08 02:05-03:15Z; the user at the TV through the onn, the pads paired to the onn). PS2 streamed for the first time, behind the bench drop-in b49-ps2.conf (removed at the close). The first launch failed (no audio, no release); A changed B49's launch to wait for PCSX2's audio stream (uncommitted, disclosed); then T1 and T2 played. T1: P7b / P7d / P7e / P7g / P7h met, P7f not met by 1, P7c pad 2 barely exercised. T2: P7b / P7d / P7e / P7h met, P7g not met (one 643-ms drive read), P7f not measured as pre-registered. Nothing adopted; nothing committed
---

# H3-P2: PS2 on the TV, through the stream

Task: `handoffs/H3-P2_PS2_STREAMED_RUN_TASK.md`; B's strings: `handoffs/SESSION_B_DONE_2026-11-08P.md` §A. Directory
`h3_p2_2026-11-08/`: `setup/`, `t1/` (`T1_ATTEMPT.md`, `T1_ROWS.md`, the change's diff and hashes, P2's JSON), `t2/`
(`T2_ROWS.md`), `close/`, `preregistration.md` and its `.sha256`, `redact_check.txt`, `manifest.sha256`. Titles are T1
(light) and T2 (heavy). Times UTC.

## The user's lines (verbatim)

- "Read _cowork_prompt.txt in the repo root and follow it as my prompt."
- "Game didn't start, said game stream isn't ready"
- "I'm at the TV let's just do work. We made zero progress why would you give up"
- "T1 done" / "Save failed but everything else ran surprisingly well. No real issues, maybe the occasional frame tears"
- "T2, game started"
- "T2 done ( I forgot about the back midway so did one at the end)"
- "It felt really good to play"
- "Done"

## Setup (`setup/`)

- **Checks met:** fifteen lines, `--check` ok, `8ba4d996…` CONFIRMED on the onn and paired, the eleven properties
  empty, `privyhub-diag` active, only the two units, HEAD `b665a9c7` (B49 committed), the tree clean, no game, no movie,
  5 GHz; the paths file present (never read into a record); one AppImage; the drive's folders (3 / 118 files) listed
  with mtimes, equal to H3-P1's after.
- **P7e's reference** (`p7e_reference.txt`, the user's rule): the keeper's PS1 sessions since 2026-10-09, LAN, game
  class, ≥ 10 min: **count 1, median 27.7 hitch s / 10 min, no spread** (G-A10's automated window, 2026-11-03, a weak-
  radio evening). Bar: ≤ 29.7. Thin, and lenient; disclosed.
- **Pre-registration** sha256 `f46dc3d3…a0f`, hashed 02:08:00Z, before the drop-in.
- **The drop-in** `b49-ps2.conf` (B's printf exactly), restart 02:08:10Z: **sixteen** `PRIVYHUB_` lines, one
  `PRIVYHUB_PS2=1`; the journal clean; the host's list **"PlayStation 2 (115)"** = the folder's 115 distinct titles.
- **Samplers** (`mpstat -P ALL 1`, `iostat -x 1` on `sda`, GPU and Tctl at 1 Hz, `pidstat -t` on PCSX2, the minute-6
  capture with B's command), unattended.

## The first launch failed; the change (`t1/T1_ATTEMPT.md`)

- 02:12:07Z launch; 02:12:09Z `PS2 pause: sigstop` (1.6 s after the launch; PINE did not answer); the stream ran
  (video at ~60 fps, the picture frozen) but **0 audio packets**, no release, the onn's "Game stream isn't ready"; a
  second start the same; Stop → `PS2 exit: sigterm 0.5s`.
- **Reading:** the paused handoff froze PCSX2 before its PulseAudio stream existed; the session's audio is found by the
  PID's sink-input, so there was none; the release never came. **A B49 defect.**
- **At the user's word ("let's just do work"), A changed B49's launch** (`t1/h3p2_audio_wait.diff`, uncommitted,
  `companion/ps2_session.py` + `companion/games/emulator_manager.py`): after the window, wait ≤ 45 s for the PID's
  sink-input, and log `PS2 audio: sink-input <s>s`. `tests/ps2_session` 35 / 35 OK (91 s: two launch tests wait out the
  bound; B to fake it). Companion restart 02:20:51Z. **Not separated:** in the next launches PINE also answered (the
  hotkey, not SIGSTOP), so which of the two cured it is not known; B49b to test both.

## The rows per title (`t1/T1_ROWS.md`, `t2/T2_ROWS.md`)

| row | T1 (light) | T2 (heavy) |
| --- | --- | --- |
| P7a list | met: "PlayStation 2 (115)" = 115; folders before = after | met |
| P7b launch ≤ 90 s | **met**: first picture 2.7 s, the game running 9.4 s | **met**: 2.5 s / 6.2 s |
| P7c pads | pad 1 met; four `PrivyHub Virtual Gamepad` opened, SDL-0..3 = players 1-4 in creation order; **pad 2 barely used** (30 changes) | pad 1 met; pad 2 16 changes — **player 2 not shown** |
| P7d pause / resume ≤ 3 s | **met**: pause 0.04-0.14 s after `session_ended` (×3), resume ~0.005 s before `session_started` (×2); hotkey | **met**: 0.16 s ×2, 0.005 s; hotkey; the Back at the end |
| P7e hitches ≤ 29.7 / 10 min | **met: 0.0** (0 s in 509 s) | **met: 6.2** (4 s in 387 s; 3 control gaps of 250-302 ms, 1 loss) |
| P7f P2 median ≥ 59, corrected min ≥ 55 | median 60; **min 54, not met** (the capture's first second, one 117-ms gap; all others 59-60) | **not measured as pre-registered** (the Back 23 s into the capture); the 23 played seconds: 57-60 per second |
| P7g M2-M6 | **met**: no core ≥ 90 % beyond 1 s; GPU median 24 %; Tctl max 65.4 °C; p95 16.7 ms; no read stall | **not met**: one drive read second at **643 ms** (2.2 min in); else met (GPU 30 %, Tctl 63.6 °C, p95 16.7 ms) |
| P7h exit | **met**: sigterm 0.5 s, nothing left | **met**: sigterm 0.5 s |
| P7i feel | "Save failed but everything else ran surprisingly well. No real issues, maybe the occasional frame tears" | "It felt really good to play" |

- **Play time:** T1 9 min (8.5 min of play), T2 6.4 min; both short of 10 minutes; both **valid** (the pads on the
  onn, no stream restart: every session ended by the user).
- **"The next PS1 launch works"** (P7h's second half): not read (no PS1 tonight, the user's decision).
- **The pause method:** hotkey (PINE answered) in every pause / resume after the change; SIGSTOP only in the failed
  first launch.

## The close (`close/`)

`b49-ps2.conf` removed, `daemon-reload`, restart 03:14:16Z (no game, no movie); **fifteen lines**, no `PRIVYHUB_PS2`;
`--check` ok, `8ba4d996…` CONFIRMED; `flags_absent: true`; the eleven properties empty; the onn paired; the drive's
folders before = after, 0 writes; nothing of PCSX2 running; `privyhub-diag` active. **Left in the tree, uncommitted:**
A's change to `companion/ps2_session.py` and `companion/games/emulator_manager.py` (inert without `PRIVYHUB_PS2=1`).

## To B (B49b)

- the audio-wait change (review, keep or replace; fake the wait in the tests); separate PINE vs. the wait;
- player 2 on a PS2 title still to show (two pads in a two-player mode);
- "Save failed": the hub memory cards read UNFORMATTED at boot (format at first use, or tell the user why);
- "occasional frame tears": PCSX2's present mode / vsync under the capture;
- PCSX2's `Invalid binding: SDL-0/A … SDL-1/Y` lines (the source not in the ini);
- the keeper labels PS2 sessions as PS1;
- the drive: one read second over 500 ms in T2 (643 ms), as in H3-P1's T1 (552 ms); the keep-awake does not cover a
  slow read; read-ahead (option 2) is the candidate if it recurs in play;
- P7f's capture should not overlap the user's Back (start it after a resume, or take it at minute 3).

## The user's questions

- **PS2 always on (`PRIVYHUB_PS2=1` as the sixteenth line), yes / no.**
- **PS2 save states later (the hold / stall / recovery through PINE), yes / no.**
