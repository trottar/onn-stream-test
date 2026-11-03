---
memory_schema: 1
as_of: 2026-11-02
baseline_commit: e0155d1c (B39 uncommitted; built in /tmp/b_q02m_b39, integrated by the coordinator)
---

# B39 — the hold's report counts what its rows counted; the guide key recorded, the "consume" half dropped

**Classification: SETTLED + FIXED** inside `debug.privyhub.surface_hold` (B32's property; no new flag).
- **Tests:** JVM `HoldReportTest` 6 new, the whole suite **190 / 190** (184 + 6) three runs; B32's
  `SurfaceHoldTest` 8 green with one test edited (§2, disclosed); host suites in the copy the same as the baseline.
- **Mutations:** 3 caught (M1, M2, M4); one equivalent (M3, §3).
- **Proof:** absent = today, PROVEN (`proof_flag_absent.md`).
- NOT installed; NOT ADOPTED; no live run; nothing committed.

Design `b39_2026-11-02/design_written_before_code.md`, sha256 `b9d1c4ba…cb4d`, hashed **02:58:02Z, before any B39
code**. Precondition: G-A10's record present, only the companion and `privyhub-diag` active (`units_at_start.txt`).

## 0. Settled: why C1's report read `held` 0 while its row read `held`

- **The activity caches its report once:** `cacheSessionReport()` returns `cachedSessionReport` if set and clears it
  only in `startSession`.
- **B32's `beginSurfaceHold` snapshots at every loss, before `onSurfaceLost` counts it.** A held loss continues the same
  session, so the first loss's snapshot is never replaced. Every later report path posts it: the expiry hands it to
  `RestartGuard` (posted at the next start), and `stopSession` / the hand-over get it back from the cache.
- **C1 is exactly that** (`home1_2026-11-02/c1/report_005628_surface_hold.json`):
  - the report posted 00:56:28.888, at the restart after the guide press's ~23-s away;
  - every `surface_hold` counter 0 (`decoders_built` 1);
  - **`duration_ms` 16270 = the session's start to the first loss** (the surface destroyed at 00:55:26.93; the host
    session at 00:55:14).
- **So the whole report was stale, not only the counter.** The decoder, audio and controller counts of any session
  with a held loss stopped at its first loss.
- **B32's tests could not see it:** the activity model in `SurfaceHoldTest` had no report cache.

## 1. Fixed (`b39.diff`; `NativeStreamActivity.kt` +11 −2, `SurfaceHold.kt` +17 −1; tests `HoldReportTest.kt` +195 (new), `SurfaceHoldTest.kt` 6 lines changed)

1. **A held re-attach clears the cache** (`endSurfaceHold`): `cachedSessionReport = null`. The next loss or stop builds
   a fresh report. The closed decoder's frames stay in `rendered_before_reattach`, and the heartbeat's
   `rendered_frames` still drops back once (B32's disclosure, unchanged).
2. **At a loss, count it, then snapshot** (`beginSurfaceHold`).
3. **When the outcome is decided after the snapshot, the snapshot's `surface_hold` is refreshed** by
   `SurfaceHold.refreshReport(report)`:
   - at the expiry (`restarted`), before the report goes to the guard;
   - at `onDestroy` inside a hold (`ended_in_hold`), before `stopSession` posts it.
   - The function is a text replace of the flat `"surface_hold":{…}` object (`JSONObject.toString()`'s compact text) by
     the current `reportFields()`. Pure Kotlin, so JVM-testable. A report without the object, or null, is returned
     unchanged.
- **C1's sequence now reports `losses` 2, `held` 1, `restarted` 1** (`duration_ms` to the second loss). A held loss
  followed by a normal exit reports `held` 1 over the whole session.

## 2. The guide key (C1 (2)), recorded; B32's "consume" half dropped

- **The finding (HOME-1 C1, the onn's log):** the pad's guide / PS press is consumed by the onn's own input policy
  (`input_cancel … inbound event was dropped because the policy consumed it`), which starts `category.HOME`; the launcher
  logs "Wake by home key". The key never reaches `dispatchKeyEvent`, so **B32's consumption is not possible on this
  onn.**
- **Dropped (the smallest change):** `SurfaceHold.onKey` returns `false` for every key (one line). `dispatchKeyEvent`
  then runs today's code for every key; the activity is not edited for this.
  - Every key-down is still noted for the rows, with the marker `:p`.
  - A pad system key that reaches the activity on another device passes to the system and counts in
    `system_keys_passed`.
  - `pad_system_keys_consumed` stays in the report (always 0), so the report's keys are unchanged.
- **The hold covers a guide press as it covers a Home press:** held within the bound, today's restart past it. C1
  (2)-(3) showed exactly this: the guide press ran as Home, away ~23 s, a `restarted` row at the 12-s bound.
- **Disclosed:** B32's `aPadSystemKeyIsConsumedTheRemotesIsNot` is edited to `noKeyIsConsumedEveryKeyIsNoted`. Its
  consume assertions are now "not consumed", it expects `system_keys_passed` 3 and `pad_system_keys_consumed` 0, and the
  pad MODE key's marker is `110:pad:p`. Its row and reason assertions are unchanged.

## 3. Tests (`tests_jvm_x3.txt`, `jvm_xml/`, `tests_mutations.txt`, `tests_regression_after.txt`)

**`HoldReportTest`** (new, 6): the activity's report cache modelled as the activity has it (first one wins, cleared at
a start, `surface_hold` from `reportFields()`), with B39's hooks as written.

| test | checks |
| --- | --- |
| a held loss, then a stop | `held` 1, `losses` 1, `restarted` 0, `duration_ms` over the whole session (C1 (1)) |
| C1's sequence | held 4.4 s, then a second loss past the bound and the next start: `losses` 2, `held` 1, `restarted` 1, the duration to the second loss |
| an activity ending inside a hold | `ended_in_hold` 1 |
| absent | the loss caches once and the next start posts it unchanged (no `surface_hold` key) |
| the refresh | replaces only that object; no object / null unchanged |
| a pad MODE key | not consumed, noted `110:pad:p`, reason `pad_system_key` |

- **Totals:** JVM 190 / 190 ×3. Host suites in the copy are the same as the queue-M baseline line for line (41 OK);
  B39 is client only.
- **Mutations:**
  - **M1:** the clear at a held re-attach removed (activity + model) → 2 fail. The stop reports `held` 0, and the
    duration stays 16270, C1's own number.
  - **M2:** the refresh at the expiry removed → 1 fails (`restarted` 0).
  - **M4:** the refresh a no-op → 3 fail.
  - **M3 (not caught, equivalent):** the snapshot taken before the count, as B32 had it. The refresh at the expiry and
    at the end rewrites the counters on every path that posts a snapshot taken inside a hold, and a held re-attach
    clears it, so the order cannot show. The order is kept for a hand-over inside a hold (a configuration change while
    away), which no test reaches.

## 4. Proof: absent = today (`proof_flag_absent.py` / `_output.txt` / `.md`)

- All 13 changed lines in the activity sit in hold-only contexts: `beginSurfaceHold`, `endSurfaceHold`, `holdExpiry`
  after its null check, and `onDestroy`'s `surfaceHold?.let`.
- Their callers are guarded by `surfaceHold?.let`, and `SurfaceHold` is constructed only when the property parses.
- B32's absent test is unedited and green; `HoldReportTest`'s absent test passes too.

## 5. For HOME-2 (C1')

- **Set:** `adb shell setprop debug.privyhub.surface_hold 1` on the new APK, then (re)start the game.
- **Do:** in a game, the remote's Home and back to PrivyHub within 3 s; play on ~30 s; exit with Back.
- **Pass:**
  - the recovery log has `"event": "surface_lost"`, `"outcome": "held"`, `away_ms` < 12000;
  - one host session (no `restart_fast` / `session_ended` at the return);
  - **the report posted at the exit has `surface_hold.held` 1, `losses` 1, `restarted` 0, and `duration_ms` covering
    the whole session (past the loss).**
- **Optional:** a guide press is a Home press (`reason` `user_leave`, no key in the row); held within 12 s.
- **Off:** `setprop debug.privyhub.surface_hold ""`.

## 6. Files

- **`b39_2026-11-02/`:**
  - `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
  - `predecessors/` + `predecessor_sha256.txt`, `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b39.diff` (`git apply --check` OK on the tree and on queue L's APK base, B27 / B29 out);
  - `proof_flag_absent.py` / `_output.txt` / `.md`;
  - `tests_jvm_x3.txt`, `jvm_xml/`, `tests_mutations.txt`, `tests_regression_after.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:**
  - `patches/B39_HOLD_COUNTER.md`;
  - a dated note appended to `B32_SURFACE_HOLD_AND_STEP_IN_PLACE_2026-10-31.md`;
  - in the copy (to be applied by the coordinator): `SurfaceHold.kt`, `NativeStreamActivity.kt`,
    `SurfaceHoldTest.kt`, `HoldReportTest.kt` (new).
- **Left in /tmp:** `b_q02m_b39` (the copy), `b_q02m_b39_scratch/` (`m1`-`m4`), `b_q02m_b39_gradle1-3.txt`.
- **The rules held:**
  - no stream, no companion restart, no adb, no sudo, no nft;
  - `privyhub-diag` and `~/privyhub_diag/` untouched; the live tree's code untouched;
  - nothing of A's touched; nothing fetched, deleted, adopted or committed.
