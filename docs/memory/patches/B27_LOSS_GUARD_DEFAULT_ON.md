---
memory_schema: 1
as_of: 2026-10-27
baseline_commit: 2cd392c
---

# B27 — the client's `loss_guard` on by default (`0` off); APK `8b0fbb74…` pinned, NOT installed; G-A8 PREPARED

**Result: BUILT; JVM 4 new (154 / 154); `0` = today PROVEN; the mutation caught (3); the replay ran first (47 sessions:
the LAN ~32 frames held a minute, G4-S4 ~15, a hold > 0.5 s possible in 10, capped at 600 ms); NOT ADOPTED; no live
run.** Record: `evidence/B27_LOSS_GUARD_DEFAULT_ON_2026-10-27.md`. Nothing committed.

- **Built:** `LossGuardFlag.parse`: `0` off, `count` as before, anything else (absent / empty / junk / `1`) the
  guard; a failed read → the guard. B10's guard, cap, request and counters are unchanged.
- **Host:** no change. Without `PRIVYHUB_LOSS_GUARD=1` each freeze's 24-B request is one `bad_packets`; the picture
  is the same with or without it (no runtime IDR). G-A8 (the thirteenth line) is prepared in
  `patches/G-A8_LOSS_GUARD_ADOPTION_PREPARED.md`.
- **APK** (B5 + B7 + B10 + B11 + B13 + B14 + B15 + B16 + B17 + B18 + B19 + B22 + B25 + B27)
  `8b0fbb74d110ad89b6c1f9e69355abc3b5713b69055d3e8fa02b898108ee3f4e`, 9,638,182 B. Same signer as `fcd924c2…`; only
  `classes3.dex` differs.
- **Files:** `LossGuard.kt` (the flag object + one KDoc line); `LossGuardDefaultOnTest.kt` (new); the flag lines in
  `LossGuardTest.flagTable` moved.
- **Apply:** `git apply evidence/b27_2026-10-27/b27.diff` (the tree already carries it, uncommitted); install only
  in CL-B15.
- **Rollback:** `setprop debug.privyhub.loss_guard 0` (a reboot clears it); or revert the flag object; or put
  `fcd924c2…` back on.
