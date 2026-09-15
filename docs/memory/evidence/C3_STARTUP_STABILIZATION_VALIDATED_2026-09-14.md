---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: b2f752223d0bd7617a7f7ef75c9618202d2372fa
---

# C3 startup stabilization runtime validation

## Classification

**RUNTIME VALIDATED / STARTUP LAG HIDDEN**

D-067 is accepted for the current Windows + onn runtime.

## Successful focused observation

After restarting the companion process with the installed D-067 Python source:
- `Stabilizing game…` appeared;
- release succeeded;
- gameplay ran correctly;
- the user reported that it “worked great”;
- the user specifically reported **no lag in the beginning**.

No source change was required between the failed and successful attempts.

## First-attempt failure diagnosis

The first attempt displayed the new Android stabilization UI but later showed
`Release failed`, while the game appeared not to stay paused.

Existing RetroArch lifecycle evidence from that attempt showed:
- launch reached real `GET_STATUS PAUSED`;
- lifecycle event `pause` recorded `retroarch_state=PAUSED`;
- later RetroArch reached `GET_STATUS PLAYING`;
- lifecycle event `resume` recorded `retroarch_state=PLAYING`.

That sequence matched the predecessor Games plugin behavior, where
`native-stream-start` automatically resumed a paused emulator.

The Android APK had been rebuilt/installed, but the already-running companion
Python process had not been restarted. The new client therefore interacted with
stale companion code:
- stale `native-stream-start` resumed the emulator;
- stale companion did not implement the new `native-stream-ready` contract;
- Android reported release failure.

A clean companion restart loaded the installed D-067 Games plugin and resolved
the problem without another patch.

## Durable rule

When any companion Python file changes, restart
`python .\companion\privyhub_service.py` before runtime validation.

Do not interpret behavior from a stale companion process as evidence against the
new source.

## C3 disposition

Startup stabilization:
**runtime validated**.

Fixed bitrate ladder remains:
- 5500 kbps low/current Windows floor;
- 6000 kbps medium;
- 7000 kbps high/reference.

5000 kbps remains excluded.

Automatic bitrate controller:
**next / not yet implemented**.

Audio burst/gap:
**still deferred to Linux + Home Opal**.

Linux:
startup/actuator/fixed-envelope behavior still requires representative
revalidation.
