# B39 — design, written before any B39 code (2026-11-03, session B, queue M)

## Settled: why C1's report read `surface_hold.held` 0 while its row read `held`

- **The activity's report cache is "first one wins".** `cacheSessionReport()` (`NativeStreamActivity.kt:1209-1226`)
  returns `cachedSessionReport` if it is set and builds a report only if it is not. The cache is cleared only in
  `startSession` (`:634`).
- **B32's `beginSurfaceHold` calls `cacheSessionReport()` at every loss, before `onSurfaceLost` counts it** (`:4252`,
  then `h.onSurfaceLost`). At the first loss the snapshot has `losses` 0, `held` 0, and `duration_ms` up to the loss.
- **A held loss continues the same session, so nothing clears the cache.** Every later report path posts that first
  snapshot:
  - the hold's expiry hands `cachedSessionReport` to `RestartGuard.onSurfaceLost` (posted at the next start);
  - `stopSession` / the hand-over call `cacheSessionReport()`, which returns the old one.
- **C1 fits exactly:**
  - the report posted 00:56:28.888, at the restart after the guide press's 23-s away;
  - every `surface_hold` counter 0 (`decoders_built` 1);
  - `duration_ms` 16270, which is the session's start to the **first** loss (the surface destroyed at
    00:55:26.93; the host session began 00:55:14).
  - So the report was the snapshot from before the first, held, loss. The whole report was stale, not only the counter:
    its decoder, audio and controller counts all stop at the first loss.
- **B32's tests did not see it:** `SurfaceHoldTest`'s activity model never modelled the report cache.

## The fix (inside `debug.privyhub.surface_hold`; absent = today: every new line runs only with a non-null `surfaceHold`)

1. **A held re-attach clears the cache** (`endSurfaceHold`, after `onSurfaceBack()` is true): `cachedSessionReport =
   null`. The session continues, so the loss-time snapshot is obsolete. The next loss or stop builds a fresh report;
   the closed decoder's frames are still in `rendered_before_reattach`, as B32 disclosed.
2. **At a loss, count it first, then snapshot** (`beginSurfaceHold`): `h.onSurfaceLost(…)` before
   `cacheSessionReport()`. The snapshot then has this loss in `losses`; `held` / `restarted` are not yet known.
3. **When the outcome is decided after the snapshot, the snapshot's `surface_hold` object is refreshed:**
   - at the expiry, after `h.onExpired()` and before the report goes to the guard;
   - at `onDestroy` inside a hold, after `h.onEndedInHold()` and before `stopSession` posts it.
   - The refresh is `SurfaceHold.refreshReport(report)`: a pure-Kotlin text replace of the report's `"surface_hold":{…}`
     object (flat, numbers only, no nested braces) by the current `reportFields()`. JVM-testable with no `org.json`.
     A report with no such object (or null) is returned unchanged.

## The guide key (C1 (2)), recorded; the "consume" half dropped

- **The finding:** on the onn, the pad's guide / PS button never reaches the app. The system's input policy consumes it
  (`input_cancel … inbound event was dropped because the policy consumed it`) and starts `category.HOME`; the launcher
  logs "Wake by home key". So B32's consumption in `dispatchKeyEvent` cannot act. **It is recorded as not possible on
  this onn.**
- **Dropped:** `SurfaceHold.onKey` no longer consumes anything. It returns `false` for every key, so
  `dispatchKeyEvent` runs today's code for every key. It still notes every key-down for the rows: a pad system key that
  does reach the activity on another device is passed to the system and counted in `system_keys_passed`.
  - `pad_system_keys_consumed` stays in the report (always 0) so the report's keys do not change.
  - The row's key marker is `:p` for every key.
  - This is the smallest change: one line in `onKey`; the activity is not edited for it.
- **The hold covers a guide press as it covers a Home press:** within the bound the session holds; past it, today's
  restart. C1 (2)-(3) showed exactly that: the guide press ran as Home, was away ~23 s, and restarted at the 12-s bound
  with a `restarted` row.

## Tests (JVM, `SurfaceHoldTest`, and a new `HoldReportTest`)

- **The activity model gains the report cache as the activity has it:** first one wins, cleared at the start, the
  snapshot carrying `surface_hold` from `reportFields()`. B39's three hooks are modelled exactly as written.
- **A held loss, then a stop → the posted report has `held` 1, `losses` 1, and a duration past the loss.**
  This is C1 (1).
- **C1's sequence → the report has `losses` 2, `held` 1, `restarted` 1:** a held loss, then a second loss past the
  bound, with the report posted at the next start.
- **Absent (hold null):** today's cache and report path. The surface's loss caches the report once and posts it at the
  next start, unchanged.
- **The refresh:** replaces only the `surface_hold` object; leaves a report without one, and null, unchanged.
- **The keys:** a pad MODE key is no longer consumed (`onKey` false); the row has `110:pad:p`; `system_keys_passed`
  counts it. This edits B32's `aPadSystemKeyIsConsumedTheRemotesIsNot`, renamed, disclosed.
- **Mutations:**
  - M1: the clear at re-attach removed → the held-then-stop test fails;
  - M2: the refresh at expiry removed → the C1 sequence fails;
  - M3: the order at the loss restored → the `losses` assertion fails.
