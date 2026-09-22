---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
durable_memory_updated: true
---

# D-BASE-R3 — link-drop self-recovery

## Purpose

Behaviour decided by the user 2026-09-20 (`docs/KNOWN_ISSUES.md`,
"link-drop resilience") and specified with every constant in
`investigations/LINK_DROP_RECOVERY_DESIGN.md`: pause the game the moment the
session looks desynced, keep auto-recovering the stream, unpause only after
the stabilization gate passes a second time, and after a bounded time save
the game and stay paused with the launcher saying so.

The freeze that motivated it: during play on 2026-09-20 the onn held a stale
frame while the host kept running and the game advanced blind. `D-BASE-R2`
made that visible; nothing acted on it.

## Expected predecessor

- `companion/plugins/games.py`:
  `0e64c09fc45a8a18ade25e5e14e25be0dfcf0fbfaae88ce47a4d853aff0e5e55`
- `companion/games/emulator_manager.py`:
  `aedd17e36b828bcbc91ea8eef39f3ae60c5ae8aa5ac408e676a4157be459a0c4`
- `companion/native_session_io.py`:
  `43ffa0b03e64d7b33a64627a1939781d320aae6f90bd5867f4e21a437de15a8a`
- `PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt`:
  `7cbd9fe8604957910f77ae8247a7af42a895c1e8c52a84ab7d1069c67c8003cc`
- `PrivyHub/app/src/main/java/MainActivity.kt`:
  `dbb2fcd58cc2d3eb988897ae748b6e92edea6178e5257b229e1525839b7e9bb2`

## Changed scope

**New: `companion/games/link_drop_recovery.py`**
(`8e274eff47bfad9d8775767e1a9a5571eca6fae1f110b08eb0845d4d5c1853a2`). The
state machine `PLAYING` / `PAUSED_RECOVERING` / `PAUSED_SAVED` / `ENDED`, a
250 ms monitor thread, the constants, and the JSON-lines transition log at
`logs/games/native_stream_recovery.log` (host time, no addresses). Every
effect is a callback supplied by the plugin, so the module imports neither
the emulator nor the stream manager.

**`companion/native_session_io.py`**
-> `61cb60a03d31c5ce22f1fb8daecc5e95a0e468cd463ecb8c1b44608bbb25b795`.
`NativeControllerBridge` gains `_last_any_packet_at`,
`set_client_silence_callback()` and `last_client_packet_age_ms()`. The
silence check rides in the existing receive loop's timeout branch — the loop
that already measures per-player silence to neutralize inputs — and fires
once per episode, re-armed by the next packet.

**`companion/games/emulator_manager.py`**
-> `f5b2d805152167f75c1004d7c4bcff6300c6980cc93b08651cda3aa3978d25a5`.
The slot-0 capture half of `save_state` is extracted to
`_capture_slot0_state()` and `save_state` now calls it, so the recovery save
uses the identical `SAVE_STATE_SLOT 0` command, artifact observation and
stability wait; only the destination differs. Added:
`save_recovery_state()` (destination `<stem>.state.recovery`),
`load_recovery_state()`, `copy_recovery_state_to_slot()` (same copy
verification, same `_record_state_slot_index`, same occupied-slot
confirmation as a manual save), `discard_recovery_state()`,
`recovery_state_detail()`, and a small index at
`data/games/retroarch/privyhub_recovery_save.json`.
`_normalize_save_state_slot` is untouched and still rejects anything but
1-3, so no existing path can reach the recovery file.

**`companion/plugins/games.py`**
-> `2c07495c96a1fe9d27c38155002cb3784ed5aa87f2b190aea1641246c388fbd3`.
Constructs the recovery object and wires the silence callback;
`GET status` and `native-stream-status` gain the `recovery` block
(`state`, `since_ms`, `restarts`, `last_client_seen_ms`, `save_available`,
`saved_at`, plus the constants); `native-stream-heartbeat` now feeds the
monitor; new POSTs `native-stream-desync`, `recovery-resume`,
`recovery-copy`, `recovery-discard`; `native-stream-start` explicitly
accepts a client re-entering during a recovery; `native-stream-ready` routes
through `note_gameplay_released()` so one gate serves startup and recovery;
`native-stream-stop` and `stop` end the recovery session.

**`PrivyHub/.../NativeStreamActivity.kt`**
-> `731b959518ab04fafd4bc3e9b33648018f1fdfc69012e98a9babd031f2e1aa39`.
`DESYNC_MS` 1,000 and `RECOVERY_CLEAN_TICKS` 3; a detector on the existing
500 ms tick for `last_output_age_ms >= DESYNC_MS` or no RTP for
`DESYNC_MS`; on trigger it keeps the last frame, re-enters the same
stabilization gate, shows the overlay as "Reconnecting…", keeps the
controller sender running, and posts `native-stream-desync` **once per
episode**; the gate's clean-tick requirement becomes
`requiredCleanTicks()`; a gate timeout during recovery restarts the gate
instead of failing.

**`PrivyHub/.../MainActivity.kt`**
-> `983223ab247b88a23f191649073968a9f8bb56ca07c3e26007dbf411933c0629`.
The status poll reads `recovery`; when `save_available` is true the launcher
shows one dialog — "The stream was lost at HH:MM and <game> was saved
automatically." — with Resume from recovery save / Copy to slot 1-3 /
Discard / Not now, once per `saved_at`. The copy path reuses the existing
occupied-slot confirmation dialog.

APK: `6140c894354034cc9823caf8ab5439bea6e391b1d872e4a30f44a90703709fee`.

**Unchanged**, as instructed: `RtpH264Receiver` resync/IDR logic,
`AvcLowLatencyDecoder`, the 60 ms stale-drop policy, every streaming
constant, FEC, audio, the controller transport, and the emulator lifecycle
outside `pause()`/`resume()`. No raw `PAUSE_TOGGLE` is sent anywhere in this
patch. Nothing pauses on audio starvation.

## Validation performed

- Python compiled (`ast.parse`) on all four companion files;
  `git diff --check` clean;
- the real `sh ./gradlew :app:assembleDebug --no-daemon`, then
  `adb install -r`, with the companion restarted after every companion
  change (D-068) and port 8765 checked free before each start;
- four fault-injection runs from fresh attract-mode sessions of the PS1
  reference title, driven per `TOOLS.md`, plus the launcher prompt exercised
  end to end (resume, copy to slot, discard);
- teardown per `TOOLS.md`: recovery save discarded, game ended from the
  client, banner confirmed gone, only then the companion stopped; nothing
  left running and no listener left.

## Result

**DEVELOPMENT.** Full record:
`evidence/D_BASE_R3_LINK_DROP_RECOVERY_2026-09-20.md`.

**The specified fault injection could not be run.** The note's plan needs
root; `sudo -n nft add table inet privyhub_fault` answers
"sudo: a password is required" and no password is available to an autonomous
run. Tried twice, not retried. No nft table was ever created, so none was
left behind. The runs below use a host-side substitute — `SIGSTOP` on the
managed x11grab encoder, re-applied so a restarted encoder is stopped again
— which stops host->client video while leaving the controller channel and
control HTTP untouched, the same differential. It differs in three ways that
the record states wherever they affect a result.

| run | N | pause | resume after clear | restarts | save | verdict |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| F05 | 0.5 s | none | n/a | 0 | no | **match** |
| F3 | 3 s | 1.302 s | 3.374 s | 1 | no | **miss** |
| F15 | 15 s | 1.727 s | never | 3, all failed | no | **miss** |
| F150 | 150 s | 1.621 s | n/a | 5, all failed | **yes** | **match** |

**What works.** The pause fires on the client's desync notice within
1.3-1.7 s of the fault, every time. The overlay says "Reconnecting…" and the
game stays paused. The gate resumes the game on `RECOVERY_CLEAN_TICKS` = 3.
The give-up fired at **120.243 s** against `GIVE_UP_MS` 120,000, with the
backoff exactly 5 / 10 / 20 / 30 / 30 s. The recovery save is its own file,
1,975,320 bytes at `<stem>.state.recovery`, never a slot, and
`recovery-copy?slot=0` is still refused with "Save-state slot must be 1, 2,
or 3". The launcher prompt appears with the right time and title and all
five options; Resume, Copy to slot and Discard were each confirmed.

**What failed.**

- **The restart decision reads a stale heartbeat.** The note says restart if
  the age is "still rising"; the code checks the newest value, which can be
  2 s old. On the 3 s run that fired a restart 1.47 s *after* the fault had
  cleared and cost ~1.5 s of extra interruption — `restarts` 1 where the
  table expects 0, resume 3.374 s where it expects ~2 s. Reproduced twice.
  The fix is to require two consecutive non-decreasing readings and a
  heartbeat fresher than `RESTART_AFTER_MS`; it is a correction to the note
  and was not made here.
- **A failed encoder restart is terminal.** The C3.L1 primitive's failure
  path leaves `manager._process = None`, so `_running_locked()` is false and
  every later restart raises before doing anything. The 15 s run never
  resumed, 30 s after the fault had gone. Reached by the substitute
  injection but not caused by it: any real outage that fails one restart
  ends the same way. Needs its own decision — leave the old encoder alive on
  failure, or fall back to a full `native-stream-start`.
- **The host-side trigger is unexercised.** Every run was triggered by the
  client's notice, because neither the nft rule nor the substitute
  interrupts the client->host controller channel. Controller-silence pause
  is wired and untested.
- **`END_MS`** (30 min) was not exercised.

**Two defects in this patch, found by its own validation and fixed** before
the final build: the recovery file was looked for at the state root when
RetroArch's `sort_savestates` puts it under a per-core directory (every
resume and copy failed while the file sat on disk), and the launcher dialog
combined `setMessage` with `setItems`, which renders no options at all. A
third, cosmetic: `save_game_title` read the wrong identity key and the
prompt said "null".
