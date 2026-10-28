# B27 — `0` = today's absent; the rest of the client unchanged

- `PrivyHub/app/src/main/java/streaming/LossGuard.kt`: 10 changed lines, **all** inside `object LossGuardFlag` (or the one added `B27:` KDoc line).
- HEAD's parse: `else -> null` (absent = null): **True**. The new parse: `"0" -> null`: **True**. With null the activity builds no `LossGuard` (its line is unchanged): no hold, no datagram, no report or heartbeat key.
- Every other main source: `git diff HEAD` empty.
- JVM: `LossGuardDefaultOnTest.zeroIsTodaysAbsent` green (with `0` the receiver queues B10's today list, the same as with no guard); it stays green under the mutation, as it must.

Result: **PROVEN**.
