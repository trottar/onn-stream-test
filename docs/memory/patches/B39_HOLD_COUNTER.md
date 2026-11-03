---
memory_schema: 1
as_of: 2026-11-02
baseline_commit: e0155d1c
---

# B39 — the hold's report counter; the guide key recorded

**Result: SETTLED + FIXED inside `debug.privyhub.surface_hold`; JVM 190 / 190 ×3 (6 new), 3 mutations caught (one
equivalent, stated), absent = today PROVEN; no live run.** Record: `evidence/B39_HOLD_COUNTER_2026-11-02.md`. Diff:
`evidence/b39_2026-11-02/b39.diff`. Nothing committed.

- **Settled:** the activity caches its report once. B32's hold snapshotted it at the first loss, before counting it,
  and a held loss never cleared it. So every later report carried the first loss's snapshot: C1's `surface_hold` all 0,
  `duration_ms` 16270 to the first loss.
- **Fixed** (`NativeStreamActivity.kt` +11 −2, `SurfaceHold.kt` +17 −1):
  - a held re-attach clears the cache;
  - a loss is counted before the snapshot;
  - the snapshot's `surface_hold` object is refreshed when the outcome is decided (`restarted` at the expiry,
    `ended_in_hold` at the end), by `SurfaceHold.refreshReport`.
- **The guide key:** the onn's input policy turns it into Home before the app. B32's "consume" half is dropped:
  `onKey` returns false, keys are still noted, and `pad_system_keys_consumed` is always 0. The hold covers a guide press
  as a Home press.
- **Tests:** `HoldReportTest` (new, 6); B32's key test edited (disclosed).
- **Apply:** `git apply evidence/b39_2026-11-02/b39.diff` from the repo root, then the APK. It acts only with
  `debug.privyhub.surface_hold` set on the onn.
- **Rollback:** the property empty (today); or `git apply -R` the diff (B32's behaviour, its stale report included).
