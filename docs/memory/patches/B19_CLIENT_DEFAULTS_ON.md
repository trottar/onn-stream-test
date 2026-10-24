---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: 7f3f71d
---

# B19 — the client's `stall_signal` and `restart_guard` on by default (`0` off); APK `20e3e339…` pinned, NOT installed

**Result: BUILT; JVM 4 new (136 / 136); `0` = today proven; NOT ADOPTED; no live run.** Record:
`evidence/B19_CLIENT_DEFAULTS_ON_2026-10-24.md`. Nothing committed.

- **Built:** `StallSignalFlag.parse`: absent / empty / junk → 150, `0` → off. `RestartGuardFlag.parse`: on unless `0`.
  A failed read means on for both. `link_notice` stays opt-in.
- **Today's host:** a stall datagram is counted as a bad controller packet and nothing else, so it behaves as today.
  The guard's return flow is its own product change.
- **APK** (B5 + B7 + B10 + B11 + B13 + B14 + B15 + B16 + B17 + B18 + B19)
  `20e3e3392b3853a598ecee651b291f4654fa6aa46d63157e649f9c07d6b5563d`, 9,633,230 B. Same signer as `e2db0aa0…`; only
  `classes3.dex` differs.
- **Files:** `StallSignal.kt`, `RestartGuard.kt`, `ClientDefaultsTest.kt` (new); four tests' flag lines moved.
- **Rollback:** `setprop debug.privyhub.stall_signal 0` / `restart_guard 0`; or revert the two flag objects.
