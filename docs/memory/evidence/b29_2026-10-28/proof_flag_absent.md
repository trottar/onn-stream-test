# B29 — the guard off = today's stall monitor; nothing else changed

- `NativeStreamActivity.kt`: 4 changed lines, **every one** on the guard (`lossGuard?.…`): the stall input `holdingAgeMs = lossGuard?.holdingAgeMs() ?: -1L`, the keyframe tick `g.tick()` inside `lossGuard?.let`, the report key inside `lossGuard?.let`.
- `StallSignal.kt`: 10 changed lines: `StallInputs.holdingAgeMs` (default -1) and the decision age `if (holdingAgeMs >= 0) min(output, holding) else output`, used in the stall / end datagrams. With -1 it is today's.
- `LossGuard.kt`: the hold's clock (`tick`, `holdingAgeMs`, `maxHoldObservedMs`, `lastArrivalMs`, `@Synchronized`); the object exists only with the guard on.
- Every other main source: `git diff HEAD` empty.
- JVM: `withNoGuardTheMonitorIsTodaysByteForByte` green; B7's `StallSignalTest` and `StallByeTest`, B10's `LossGuardTest`, B27's `LossGuardDefaultOnTest` unedited and green (161 / 161).

Result: **PROVEN**.
