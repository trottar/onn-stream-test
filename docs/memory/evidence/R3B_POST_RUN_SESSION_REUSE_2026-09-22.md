---
memory_schema: 1
as_of: 2026-09-22
status: EVIDENCE — R3b finding, the two post-N150 defects diagnosed from existing logs only; one hypothesis, one probe; no production code changed and no run performed
---

# R3b post-run finding — the N150 session never ended, and everything after it was routed into it

Companion `pid 4742` (started 11:00:50, `DISPLAY=:0.0`) logged every request
across the whole R3b window, so the diagnosis below is read out of records
that already existed. **No production code was changed and no stream or game
was started for this finding.** Local times are UTC-4; the logs are UTC.

## The two reported defects

1. After the `N150` run, launching **Tekken 3** from the launcher showed the
   recovery prompt and reported **"Loaded"**, but no game opened.
2. A manual launch then streamed **3-4 frames repeating in a loop**.

## Hypothesis

**One root cause, not two.** `native-stream-stop` ends the *stream* and
**pauses** the game, deliberately — it is the "client left the stream screen"
path — but it does not end the *game session*. `N150` finished that way at
11:26:33, so RetroArch `pid 7827` stayed alive, paused, and still registered
as the companion's active session. Every later action was therefore serviced
**inside that stale session** instead of starting a fresh one: the launcher
tile could only offer `recovery-resume` (load a state into the live, paused
process — which opens no window), and the manual launch was a stream start
against that same process's window.

This is the handler, unmodified (`companion/plugins/games.py:3558`):

```python
if action == "native-stream-stop":
    self._recovery.session_ended()
    game_status = self._emulator.status()
    if game_status.get("active", False) and not game_status.get("paused", False):
        ...
            paused = self._emulator.pause()
```

and `load_recovery_state` (`companion/games/emulator_manager.py:6833`) can
only ever run against a live session — it raises `"No active game session is
available to load"` otherwise, and `"Load State requires the game to be
paused"` if it is not paused. **Both preconditions were met only because the
stale session existed.**

## The request log settles defect 1 outright

From the companion's own access log, 11:26 to 11:31 (client address redacted):

```
11:26:33  POST /plugins/games/native-stream-stop     200
11:29:37  POST /plugins/games/recovery-resume        200
11:30:59  POST /plugins/games/native-stream-start?port=48100   200
11:31:03  POST /plugins/games/native-stream-ready    200
11:31:11  POST /plugins/games/decoder-session-log    200
```

**There is no `POST /plugins/games/launch` after 11:20:49** — the last one
belongs to the `N150` run itself. The launcher never launched anything; the
tile's action resolved to `recovery-resume`. Nothing opened because nothing
was asked to open, and "Loaded" is the literal truth of what happened: a
state was loaded into a process that was already running.

The RetroArch-side trace agrees, and is byte-exact
(`logs/games/save_state_probe.txt`, `retroarch_control_probe.txt`):

```
11:26:30  PAUSE_TOGGLE -> GET_STATUS PAUSED     lifecycle action=pause  pid=7827
11:29:36  load_state_link_drop_recovery
            source  .state.recovery  sha256 05BD85…8040  1231354 B
            scratch .state           sha256 05BD85…8040  1231354 B
11:29:36  LOAD_STATE_SLOT 0 -> "LOAD_STATE_SLOT 0"
          GET_STATUS  PAUSED            <- still paused, for 86 s
11:31:03  PAUSE_TOGGLE -> GET_STATUS PLAYING    lifecycle action=resume pid=7827
11:31:11  PAUSE_TOGGLE -> GET_STATUS PAUSED     lifecycle action=pause  pid=7827
11:31:16  SAVE_FILES "OK"; frontend_close_requested sigterm pid=7827
          frontend_close_result returncode=0 forced=false
```

The same `pid 7827` runs through all of it, and the encoder banners confirm
the stream attached to that one process both times
(`logs/games/native_video_alpha.log`):

```
N150  session 11:21  Capture: managed RetroArch window (pid=7827, window_id=60817410, discovered=879x720)
post  session 11:31  Capture: managed RetroArch window (pid=7827, window_id=60817410, discovered=879x720)
```

No new game log was written after `20260922-112048-game_ps1_*.log`, which is
the same thing said a third way: **no second RetroArch was ever started.**

## The probe, for defect 2

The client is not implicated and can be set aside first. The decoder report
for the 12.8 s post-run session
(`decoder_sessions/native_decoder_20260922_153111_688.json`) is clean:
`lost_packets 0`, `sequence_resyncs 0`, `incomplete_au_drops 0`,
`recent_fps 59.85`, `recent_mbps 6.93`, `idr_frames 51`,
`first_clean_idr_ms 477`, `dropped_frames 0`. The onn received and rendered a
healthy 60 fps. **Whatever looped was in the source picture.**

Frame *size* cannot answer that, and it is worth saying why so nobody
re-runs it: the encoder is CBR (`-b:v 7000k -maxrate 7000k -bufsize 7000k`),
so it pads. Mean bytes per frame for the looping session is **14483** against
**14613 / 14749 / 14680** for the three R3b gameplay windows — indistinguishable.

**Probe: IDR size dispersion.** An IDR is an intra-coded still of the source,
so its size measures the spatial complexity of the picture, and a source that
cycles through a handful of pictures must produce a handful of byte-exactly
repeating IDR sizes. Taking per-second `max_bytes` from
`logs/games/native_frame_sizes.jsonl` (GOP 15 at 60 fps, so the per-second
maximum is an IDR), over full seconds only:

| window | full s | distinct IDR sizes | byte-exact repeats | IDR size spread |
| --- | --- | --- | --- | --- |
| **post-run, after resume 15:31:04-15:31:12** | 8 | **5 (62%)** | **62%** | **3 686 B** |
| N3 gameplay 15:17:23-15:18:14 | 51 | 37 (73%) | 35% | 56 344 B |
| N15 gameplay 15:18:55-15:20:12 | 76 | 62 (82%) | 25% | 52 923 B |
| N150 gameplay 15:24:10-15:26:20 | 130 | 123 (95%) | 8% | 74 242 B |
| N150 **paused** window 15:21:35-15:23:30 | 110 | **1 (1%)** | 100% | **0 B** |

The paused window is the calibration that makes this readable: a genuinely
frozen picture gives **66150 bytes, 110 seconds running, spread 0**. Live
gameplay gives a spread of 53-74 KB. The post-run session sits at **3 686 B**
— **14 to 20 times narrower than any gameplay window, but not zero** — with
`44248` recurring three times in eight seconds.

**So the source was moving, and cycling through about four distinct pictures.**
That is the reported 3-4 frame loop, measured, and it rules out both
alternatives: not a frozen window, and not a running game.

The transition is visible to the second. Before the resume the window carried
the loaded recovery-state picture at 83-85 KB IDRs; from 15:31:04, one second
after `PAUSE_TOGGLE -> PLAYING`, IDRs drop to 40-44 KB and
`frames_ge_40` falls to 0 and stays there:

```
15:31:02  max_bytes=85520  ge40=4     <- paused, loaded state
15:31:03  max_bytes=83646  ge40=5     <- PAUSE_TOGGLE -> PLAYING at 15:31:03.2
15:31:04  max_bytes=40771  ge40=0     <- loop begins
15:31:05  max_bytes=44248  ge40=0
15:31:06  max_bytes=40624  ge40=0
15:31:07  max_bytes=44248  ge40=0
15:31:08  max_bytes=40562  ge40=0
15:31:09  max_bytes=40624  ge40=0
15:31:10  max_bytes=43914  ge40=0
15:31:11  max_bytes=44248  ge40=0
```

The core did come out of pause — the picture changed, and kept changing — but
it never left a short cycle.

## What this does and does not establish

**Established.** Defect 1 is fully explained: the stale session meant the
launcher tile resolved to `recovery-resume`, no `launch` was ever issued, and
no window could open. Defect 2 is established as a genuine short loop in the
source picture, with the client and the transport exonerated by their own
counters, and with the loop beginning within one second of the core being
unpaused.

**Not established.** *Why* the core cycles. Two candidates remain and the
existing logs cannot separate them: (a) the ordering — `LOAD_STATE_SLOT 0`
was applied to a **paused** core and the core then sat paused for 86 s before
`PAUSE_TOGGLE`, and (b) **Beetle PSX HW restoring a state under GL hardware
rendering** (`[Video] Using HW render, OpenGL driver forced`, `hdcache`
active), a core/state interaction that has nothing to do with this project's
code. Separating them needs a run — load the same `.state.recovery` into a
freshly launched RetroArch and compare — which is outside this task.

## Recovery file disposition

`load_recovery_state` **stages** `.state.recovery` as slot 0 and does not
remove it. Both files are still on disk and byte-identical:

```
Tekken 3 (USA).state           1231354 B  11:29  sha256 05bd85c7…abbd8040
Tekken 3 (USA).state.recovery  1231354 B  11:23  sha256 05bd85c7…abbd8040
```

**Consequence:** the recovery prompt will appear again on the next launch of
this title, because the file that triggers it survived being consumed. The
file is being **kept deliberately** — R3b teardown nominally calls for the
recovery save to be discarded, but it is the evidence for both open defects
and for the probe above, and deleting it would also destroy the only copy of
the give-up state. It should be discarded once the defects are fixed or a
reproduction is no longer wanted.

## Redaction

No addresses, ADB endpoints, device identifiers or key material. The client
address in the access log was replaced with `<client>` before quoting; ports
are bare numbers.
