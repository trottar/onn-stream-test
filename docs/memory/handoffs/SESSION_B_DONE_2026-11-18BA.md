# SESSION B — done, 2026-11-18 BA (QUEUE_2026-11-18BA: B153 the planned switch's length; B154 the sound after the onn's Home; B155 one row for the session's two keys; run ~20:00Z-21:55Z)

**Checked first:** only `privyhub-companion` and `privyhub-diag` active (user units); `git status --short` empty (PP-H4's
record in `d7a99b62`; the prompt files unchanged). No stream, no companion or keeper restart, no adb, no sudo, no nft;
nothing fetched or installed; nothing written to the drive; the users' cheat setups, their slots and in-game saves, the
kept H7 folders and `runtime/` pictures not opened; the rules folder read only by `id_check.py` (as in queue AZ). **No
emulator title started** (B114's made-up title only). **Godot not run** (B111's Godot parts skipped: the board's repo was
not named, so **the board's repo was not touched, not even read**). **The app not changed** (read only for B154).
**Disclosed — ffmpeg run on the hub as a stand-in:** the real ffmpeg reading lavfi silence at the real rate, writing to a
pipe (no audio device, no pulse server, no network) — in the settle's experiment and as the harness's audio capture in
B153's tests. Read only from the hub: the sitting's party rows, `native_video_alpha.log`, the audio timing snapshots'
mtimes and counters, `native_stream_recovery.log`, the companion's journal for 19:34:20-19:35:20Z and 19:41:25-35Z
(addresses dropped), `pactl info`'s server name. No title, serial, game id, `profile_id`, character name, cheat name,
address or path in any record; no picture or sound in git. The `/tmp/b_q38ba` copy holds companion/, tools/, tests/ and
PrivyHub/'s `app/src` only — **disclosed:** a first `/tmp/b_q38ba_scratch` of mine (the experiment scripts and a list of
heartbeat times) was moved to my main-disk scratch within minutes. My scratch on the main disk: the run outputs, the
diffs' git repo, the mutation copies (removed by the script). **Nothing deleted** but my own scratch: the mutation
copies, the `__pycache__` dirs in my own work copy. The older suites' 153 temp dirs (as in queue AZ) stay in my scratch.
Nothing adopted; nothing committed in either repo. The running companion still runs HEAD's code (no restart).

## What was found and built

- **B153 — BUILT** (`evidence/B153_PARTY_SWITCH_LENGTH_2026-11-18.md`, `b153_2026-11-18/`, `patches/B153_…`).
  **Settled:** every one of the 20 switches is the same after the old sound's stop; the long kind's whole extra is that
  stop, **all eight ending 2.005-2.010 s after the switch began** — the capture's 2-s wait running out, then SIGKILL. The
  reader stops draining the capture's pipe at the stop event; ffmpeg 7.1 acts on SIGTERM only at its 0.5-s wake; 64 KiB
  of pipe fills in ~0.34 s, so a late notice blocks on the full pipe. **Reproduced on the hub with the real ffmpeg: 8 of
  30 at 2006-2008 ms** (the sitting 8 of 20); draining to the exit 0 of 20; SIGKILL at once 6-7 ms. A race on every stop,
  not the window, direction or title. **One short / one long** (the sitting's switches 15 and 16): the old sound stopped
  +0.322 / **+2.008 s**, the old encoder's last frame +0.479 / +2.102, the new first frame +0.982 / +2.605, the row
  +1.852 / +3.480. **A switch, in ms:** the old sound's stop 39-423 (long: 2005-2010) → the old encoder 93-234 → the
  window, relay, spawn and the encoder's own start 483-563 → the 0.75-s check, the new sound and `status()` 857-875.
  **Built:** a party's planned switch (armed by `_switch_stream`, B144's pattern) SIGKILLs the old capture and the old
  encoder at once and starts the new sound right after the encoder's spawn, inside its 0.75-s check (one poll after
  it); every other start takes HEAD's calls in HEAD's order. **Expected on the hub: the switch 1.0-1.4 s (bound
  ≤ 1.6 s); no sound 0.4-0.8 s (bound ≤ 1.2 s)**, today 1.655-1.978 / 3.480-3.605 s and 1459-1759 / 3284-3410 ms.
- **B154 — settled, below (no code).**
- **B155 — BUILT** (same record §B155, `patches/B155_…`): the `minigame_launch` row carries `"keys_written"`: the
  session config stamped before each party launch and read back after — written by that launch and each of the two
  keys there once with its value → true.

**Tests:** B153 6, B155 4, B143 5, B115 6 — **three runs each, all OK**; the recent suites (13) and the earlier ones
once, all OK — **`art_systems` 1 error in the work copy** (its docs test reads `docs/CHEATS.md`, not in the copy),
**120 / 120 against the repo**; **mutations 6 / 6** (one mutation's first copy did not compile — disclosed, fixed, run
again, caught). B153 in the harness (22 planned switches, the real ffmpeg as the capture): **1.364-1.367 s each (0.6 s
of it the harness's stub), the sound's gap 19.5-29.8 ms, the sequence continued, the old killed at once (7.3-7.9 ms)**;
the users' restart SIGTERM as today. **HEAD's code, the same 22: five at 3.561-3.563 s, the capture's stops 64-416 ms
and five at 2000.2-2000.6 ms** — the hub's shape. A users' start on G8-S2's recorders: every call, argv and payload the
same as HEAD's.

**What is left in the users' own start path (not touched):** their stream stop and the end of a game session, and any
start that is not the fast restart, still SIGTERM the capture with the 2-s wait and start the sound after the check.
RESUME and the onn's restarts take the fast restart, which B24 already bounds at 0.3 s (19:35:13Z: SIGKILLed at the
bound, 402 ms).

## B154 — the sound for ~15 s after the onn's Home (settled; no code)

**What plays it: the app, in the background, playing the board's sound that the hub keeps sending.** At a remote's Home
the activity is not destroyed: `surfaceDestroyed` → `beginSurfaceHold` (`NativeStreamActivity.kt` 4503-4529) closes only
the video decoder; **the receiver, the audio and the controller sender keep running for the hold's bound,
`SurfaceHoldFlag.DEFAULT_BOUND_MS = 12_000L`** (`SurfaceHold.kt`; on by default since B42), so that a picture back
within it continues the same session. Nothing is sent to the hub at Home: `onPause` (639-646) only notes it; the only
`native-stream-stop` is in `onDestroy` → `stopSession()`. At the bound, `holdExpiry` (4478-4499) →
`stopLocalPipeline()` → `audioReceiver.stop()`: the sound ends there, still with no stop to the hub. **The hub's sender
never stops by itself:** only a stop or a new start ends it; the hub has no heartbeat timeout.

**The hub's rows, 19:34:28-19:35:13Z:** the onn's last heartbeat 19:34:26.8Z (seq 267); **`client_stall` →
`desync_pause` 19:34:28.964Z** (age 642 ms: Home ~19:34:28.3Z) — the board paused by its key (the session's
`"pause": "board_key"`, `pause` / Escape in the party rows); `stall_handover_v2` 19:34:34.0Z; **at 19:34:41.5Z
`stall_end` → `resumed`** (the app's hold ran out ~19:34:40Z, its stall datagrams with it) — the board ran unpaused for
1.0 s — then `input_hold` → `desync_pause` 19:34:42.5Z (controller silence); RESUME's start 19:35:12.7Z, `surface_lost`
`reason user_leave`, `bound_ms 12000`, `away_ms 13194`; the board resumed 19:35:13.7Z. **The hub's audio run of that
stretch (19:34:12.7Z-19:35:13.1Z) sent 6,022 packets (60.2 s), 11 underflows: the board's sound went out the whole time;
the board's Escape pause did not silence it** (the users heard it; the hub's bytes cannot tell sound from silence).
**How long and why that long: ~12-13 s — the app's 12-s hold**, plus the time from the press to the surface's loss; the
users' "15 seconds" is within that.

**The users' own game sessions today:** the same app hold (12 s, every session) and the same hub pause on the stall
(~0.6 s after Home). The difference is what the paused program plays: the hub pauses a users' title through RetroArch's
own pause, which stops RetroArch's sound, so the onn plays the hub's silence from then — **not measured in this
queue** (the rows do not record loudness). In a party board session the pause is the board's key, and the board's sound
went on.

**What would end it at once, and whose:** **at the press itself only the app** — on a remote's Home (`onUserLeaveHint`,
or `beginSurfaceHold` when the loss is `user_leave`) pause or mute `audioReceiver`, keeping the hold's session; or skip
the hold for a remote Home and send `native-stream-stop`. That waits for an app change. **Within ~0.6 s, the hub,
without the app:** while a client stall holds a party board paused (`PAUSED_RECOVERING` by `client_stall` with the
party's `board_key` pause), the audio sender sends silence in place of the capture, and the captured sound again at the
resume — behind the flag, the users' sessions untouched. Or the board mutes itself when paused (the PC side).

## What I would change (not done — the queue is the task)

1. **The users' own stop path's 2-s wait** (their stream stop, the end of a session, a start that is not the fast
   restart): the same blocked capture. Draining the pipe until the capture exits, or B24's 0.3-s bound, would end it;
   that is the users' path, so its own task, its own byte-for-byte proof.
2. **B154 on the hub** (item 2 above, behind the flag): silence while a client stall holds a party board paused; it
   needs no app change and covers the case the users met. The app's change would end it at the press in every session.
3. **The 1-s run of the board at the hold's end** (19:34:41.5-42.5Z): the app's stall datagrams stop when its hold runs
   out, the hub reads that as the stall's end and resumes the board until controller silence pauses it again. Nobody
   was watching; a party board at a menu came to no harm, but a running title would have run a second.
4. **The 0.75-s check** is now the largest part of a planned switch; a planned switch could end it at the new
   encoder's first output instead of a fixed time. Not needed for the bound.
5. **`settle/blocks.py`** is pinned to this sitting (the log's line offset, the date in the snapshot glob): a record,
   not a tool.

## For A — a short solo check of B153 (sketch; exact strings)

**Preconditions (this repo)** — else "YOU, now: commit queue BA first, then send the read line again":
`grep -c "def party_switch_next" companion/native_stream.py` → 1; `grep -c "def _kill_managed_process_now"
companion/native_stream.py` → 1; `grep -c "self._stop_locked(fast=True)" companion/native_stream.py` → 1; `grep -c "def
_kill_process_now" companion/native_session_io.py` → 1; `grep -c "self._arm_fast(ns, int(pid))"
companion/party_minigame.py` → 1; `grep -c '"keys_written": keys' companion/party_minigame.py` → 2. The board's repo and
its checks as PP-H4's stage 1 (its HEAD at `674407d` or after). The companion with both bench flags for the check only,
back after, as PP-H4.

**The user alone, the pads on the onn**, one line: "YOU, now: open Games, 'PrivyParty (1)', Launch on Companion, Start
Fresh; play the board until a mini game's load screen; there press △ for a practice, leave it with Select (Share), do
that once more, then press ✕ to play the mini game for real and play it to its end; reply ok when you are back on the
board." (T88 or T89, whichever the board gives; in the record only T88 / T89.) That is **six planned switches** (two
practices in and out, the go, the end).

**Reads — MET when all hold:** (1) every `minigame_stream` row with `"planned": true` has `"switched": true` and
**`"seconds"` ≤ 1.6**; (2) **S as PP-H4 read it** (B150's wording: sound within 2.0 s after each switch, underrun rises
≤ 20 a row) and **`audio_max_arrival_gap_ms` ≤ 1200** at every switch; (3) the `minigame_launch` row has
**`"keys_written": true`**; (4) two `minigame_practice_end` rows `"by": "select_button"`; the end as the board says.
Not met → one plain sentence with the numbers, the close, "YOU, now: commit". Expected: the switches ~1.0-1.4 s, the gap
~0.4-0.8 s.

## Files

`companion/native_stream.py`, `companion/native_session_io.py`, `companion/party_minigame.py`;
`tests/b114_party_minigame_hang/b114_scenario.py` (the `b153` and `b155` modes), `tests/b153_party_switch_length/`,
`tests/b155_party_keys_written/` (new); `evidence/B153_PARTY_SWITCH_LENGTH_2026-11-18.md` + `b153_2026-11-18/`
(`b153.diff` applies on `d7a99b62`, `b155.diff` on top of it), `patches/B153_PARTY_SWITCH_LENGTH.md`,
`patches/B155_PARTY_KEYS_WRITTEN.md`; `docs/KNOWN_ISSUES.md` (one line inserted), `docs/ROADMAP.md` (one paragraph after
PP-H4's), `logs/b153_git_status.txt`, `logs/b155_git_status.txt`, `handoffs/SESSION_B_STATUS.txt` (one line), this file.

**The user, now:** this repo — commit the tree (queue BA's B153-B155). The board's repo — nothing.
