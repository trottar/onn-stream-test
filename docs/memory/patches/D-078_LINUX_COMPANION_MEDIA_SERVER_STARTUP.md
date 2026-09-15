# D-078 — Linux companion media-server startup seam

**Date:** 2026-09-15
**Status after successful installer validation:** HOST STARTUP SEAM VALIDATED / ONN E2E PENDING

## Purpose

Remove the unconditional Windows PowerShell dependency from the normal Linux companion startup path without changing the validated Windows path or the games/video/audio/controller subsystems.

## Root cause

`companion/privyhub_service.py` unconditionally selected `scripts/start_server.ps1` and `powershell.exe` from `PrivyHubController.start_server()`. On Linux, `main()` therefore failed before opening the control API with `FileNotFoundError: powershell.exe`.

The PowerShell launcher only starts the existing portable Python `companion/range_server.py` with the media root on TCP port 8000.

## Change

- Windows keeps the existing `start_server.ps1` + `powershell.exe` path unchanged.
- Non-Windows hosts launch `companion/range_server.py` directly with the current Python interpreter (`sys.executable`).
- The same media root, bind host, media port, log ownership, managed-process status and existing non-Windows terminate/wait/kill lifecycle are reused.
- Linux controller construction validates `range_server.py`; Windows controller construction continues validating the PowerShell launcher.

## Validation gate

`tools/probes/d078_linux_companion_startup_probe.py` exercises the real Linux `PrivyHubController.start_server()` branch on an ephemeral loopback port, confirms the child remains running, confirms HTTP 200 readiness, then confirms clean managed shutdown. It writes:

`logs/games/d078_linux_companion_startup_probe.txt`

Success token:

`D078_LINUX_MEDIA_SERVER_STARTUP_READY`

## Intentionally unchanged

- `companion/range_server.py` behavior and HTTP Range implementation.
- Windows media-server launch behavior.
- live-source PowerShell runners; those are a separate source-runner portability seam and are not required for the current Games E2E gate.
- GamesPlugin / EmulatorManager D-077 runtime selection.
- D-074 Linux video path.
- D-075R1 Linux process audio / PHA1.
- D-076 Linux uinput / PHI1.
- Android client, wire formats and FEC.

## Next step

Restart the normal companion on Linux, verify the control service remains up, then execute the integrated onn/Linux Donkey Kong Country E2E sequence through the normal Games product path.
