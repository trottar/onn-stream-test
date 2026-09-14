---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 47d3cf54220146c1d727e2a0491111f6d7dea6c9
---

# Stale cached wireless-ADB target native-error regression

## Status

**CLOSED / RUNTIME VALIDATED 2026-09-14**

## Fresh failure

During the Phase-C2 Android build/install attempt, step `[2/4] Finding physical
ONN ADB target` terminated on a stale cached `_adb-tls-connect._tcp` target:

`adb -s <redacted-target> get-state` returned device-not-found and PowerShell
raised a terminating `NativeCommandError`.

No network address, endpoint, hostname, or device serial is recorded here.

## Root cause

D-053's recovery architecture is still present and correct:

1. private cached target;
2. online physical transport;
3. ADB mDNS TLS-connect discovery;
4. reconnect offline;
5. one ADB-server restart plus bounded retry;
6. user Wireless debugging Off/On retry.

However, the exploratory ADB commands run under script-wide
`$ErrorActionPreference = "Stop"`. A stale cached target can therefore terminate
PowerShell inside `Test-AdbTargetOnline` before the later recovery branches run.

The 2026-09-10 D-054 validation classified `ADB_TARGET_ALREADY_ONLINE`; it did
not exercise this stale-cache failure branch. Its validation claim was therefore
too broad for this specific failure mode.

## Fix

Make every exploratory step-2 ADB operation fail-soft through one bounded helper:

- `adb devices`;
- cached/selected `get-state`;
- `adb connect`;
- `adb mdns services`;
- `adb reconnect offline`;
- `adb kill-server`;
- `adb start-server`.

The helper captures/suppresses native stderr and returns an exit code/output
object instead of allowing an expected stale/offline condition to terminate the
script.

Final recovered-device validation, APK install, and app launch remain fail-hard.

## Acceptance

**Runtime validated 2026-09-14.**

The actual stale cached-target failure branch recovered through
`cached-after-server-restart`, identified the physical onn, installed the APK
successfully and launched PrivyHub without the previous terminating
`NativeCommandError`.

The subsequent sanitized ADB audit reported one online transport, mDNS enabled,
one TLS-connect service, and zero offline/unauthorized transports. No address,
endpoint, hostname, device serial or mDNS instance name was copied into durable
memory.

The older audit's literal-source checks for direct `adb mdns` / `adb reconnect`
calls now report false because those commands are intentionally routed through
`Invoke-AdbRecoveryCommand`. That is a stale diagnostic heuristic; raw runtime
behavior is authoritative.

This fix remained independent of the C2 stream-telemetry source bytes.
