# PrivyHub A4 — Audio / Companion Lifecycle Recovery v3

## Root cause

The A4 audio design itself was not intended to leave the PC at 1%.

Normal game shutdown already has a complete ownership chain:

```text
Games stop
    ↓
EmulatorManager.stop()
    ↓
RetroArch SAVE_FILES + targeted WM_CLOSE
    ↓
NativeStreamManager.end_game_session()
    ↓
NativeSessionIO.stop()
    ↓
NativeAudioStreamer.stop()
    ↓
CTRL_BREAK to PrivyHubProcessAudio.exe
    ↓
exact Windows mixer restoration
```

The missing ownership edge was above it:

```text
companion top-level shutdown
    X
plugin/game shutdown
```

`privyhub_service.py` previously closed the HTTP/media controller but did not shut down plugins.

A companion exit during a game could therefore orphan:

- RetroArch;
- native streaming state;
- `PrivyHubProcessAudio.exe`.

`EmulatorManager` and `NativeAudioStreamer` store their `Popen` ownership only in memory, so a new companion cannot adopt those old child objects.

## Why v2 orphan recovery failed

The audio helper is launched with:

```text
CREATE_NEW_PROCESS_GROUP
```

and its owning `NativeAudioStreamer.stop()` uses the retained `Popen` object to send:

```text
CTRL_BREAK_EVENT
```

That is correct inside the owning companion process.

After that owner is gone, an unrelated recovery process cannot reliably deliver a Windows console control event to the old process group. The observed `WinError 87` is consistent with that ownership boundary.

The same recovery run also established:

```text
Managed RetroArch target alive: False
```

That changes the safety decision.

Once the target RetroArch process is already dead:

- its live audio session no longer exists;
- the orphan helper has no live target mixer session to preserve;
- the helper's captured pre-suppression state for this bad generation was already `0.01`;
- leaving the helper running provides no restoration benefit.

Therefore v3 allows exact termination only when all of these are true:

1. companion localhost control API is not running;
2. exactly one `PrivyHubProcessAudio.exe` exists;
3. its executable image is exactly the project-local runtime helper;
4. its status file identifies a target PID;
5. that target PID is already dead.

A helper whose RetroArch target is still alive remains **graceful-only** and v3 fails closed rather than force-killing it.

## Companion lifecycle fix

`shutdown_plugins()` is called from `privyhub_service.py`'s `finally` block.

For Games it reuses the existing:

```text
handle_post("stop", "")
```

path rather than implementing another shutdown system.

That preserves:

- save flushing;
- RetroArch graceful close;
- native stream shutdown;
- controller cleanup;
- audio `CTRL_BREAK` restoration.

## Crash-safe audio mixer state

Process-audio v0.25 writes the exact pre-suppression mixer state before applying the 1% local attenuation:

```text
data/games/native_stream/process_audio_suppression_recovery.json
```

It records:

- original volume(s);
- original mute state(s);
- exact expected suppressed volume(s).

On the next managed audio start, the state is recovered only when the current mixer still matches the expected suppressed state.

Normal shutdown deletes the marker only after exact restoration succeeds.

## Legacy 1% repair

Retained history established:

```text
Sep 8 23:52  original volume = 1.0; final/restored clean
Sep 9 13:56  first retained original volume = 0.01
later runs    original volume = 0.01
```

After the dead-target orphan helper is removed, the installer seeds one recovery marker:

```text
original = 1.0
suppressed = 0.01
mute = false
```

On the next RetroArch session:

- if Windows inherits `0.01`, the marker restores `1.0`;
- if Windows already presents `1.0`, the marker is safely ignored because the current state no longer matches the stale suppressed state.

Either path then proceeds with the normal temporary A4 1% attenuation for PC silence and ×100 stream compensation.

## One-command E2E validation

Run only:

```powershell
python .\tools\probe_a4_audio_lifecycle_recovery.py
```

The probe:

1. requires no existing companion;
2. starts the companion itself;
3. asks the user to launch a game on the onn;
4. confirms TV audio is audible and PC duplicate audio is effectively silent;
5. records the managed RetroArch PID and helper state;
6. sends Ctrl+Break to the companion process it owns;
7. verifies companion shutdown runs the Games cleanup;
8. verifies RetroArch exits;
9. verifies `PrivyHubProcessAudio.exe` exits;
10. verifies process-audio v0.25 reports `final=true` and `restored=true`;
11. verifies the recovered original mixer baseline is `1.0`.

Expected:

```text
A4_AUDIO_LIFECYCLE_RECOVERY_E2E_OBSERVED
```

If it fails, return:

```text
logs/games/a4_audio_lifecycle_recovery_probe.txt
```

## Scope intentionally unchanged

- `companion/plugins/games.py` and A8.1
- `companion/games/emulator_manager.py` and A8.1
- Android
- audio packet format/pacing
- Android audio playback
- video
- PHI1/ViGEm/controllers
- Save/Load/Pause/End semantics

A8.2 resumes after this A4 E2E passes.


## v4 installer compatibility correction

The v3 installer reached its backup stage and then failed because it used:

```text
[System.IO.Path]::GetRelativePath(...)
```

That API is unavailable in the PowerShell/.NET Framework environment on the development PC.

No production project file had been written yet. The v3 installer performs dead-target orphan cleanup before the backup stage, so the already-dead-target `PrivyHubProcessAudio.exe` may have been terminated before this installer failure.

v4 makes no production-design change relative to v3. It replaces that installer-only API with a PowerShell-5-compatible helper that:

1. canonicalizes the project root and target path with `GetFullPath`;
2. verifies the target remains under the project root;
3. derives the relative path with `Substring`.

v4 accepts either runtime state when starting:

- dead-target orphan helper still present, in which case the existing v3 recovery logic disposes of it safely; or
- helper already absent because v3 completed that runtime-only cleanup before its installer compatibility failure.


## v5 probe-only correction

The first v4 E2E run confirmed the actual user-facing audio behavior:

- TV game audio was clearly audible;
- PC duplicate game audio was effectively silent.

The probe then failed because of a deterministic diagnostic bug.

It incorrectly searched:

```text
logs/games/audio_timing/*.json
```

while the game/helper was still running.

That directory is the final-session history source. The live process-audio source is:

```text
data/games/native_stream/process_audio_status.json
```

Process-audio updates the live status during capture and writes the historical timing JSON at final shutdown.

v5 changes **only the E2E diagnostic**. It does not modify A4 production source or the runtime helper.

The corrected probe now:

1. reads live `process_audio_status.json` while the game is running;
2. validates v0.25, `ready=true`, `final=false`;
3. validates the pre-suppression baseline is `1.0`;
4. validates the crash-safe recovery marker exists while attenuation is active;
5. validates compensated live audio is non-trivial;
6. then shuts down the owned companion;
7. only after shutdown reads the fresh final `audio_timing/*.json`;
8. requires `final=true` and `restored=true`;
9. requires the crash-safe marker to be cleared;
10. verifies companion, RetroArch, and the process-audio helper all exit.

The failed first E2E run may already have consumed the one-time legacy marker during its exception cleanup. Therefore v5 validates the stable recovered invariant (`original_volumes == 1.0`) rather than requiring the historical one-time marker to still be available.
