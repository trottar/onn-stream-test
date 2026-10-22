---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 144e5c7 (PrivyHub/ clean vs HEAD at start)
---

# B5 — the client's Wi-Fi lock during a stream (the first suspect for the idle LAN's 250-ms silences)

**Classification:**
- **SETTLED from the code: no Wi-Fi lock and no wake lock is held during a stream.**
- **BUILT** behind `debug.privyhub.wifi_lock=<low_latency|high_perf>`; property absent = today (proof: only added
  lines, all null-safe).
- The JVM tests are 85/85 (78 unchanged + 7 new).
- APK **`8a69a480…b767`** built offline and pinned, **NOT installed**.
- No live run, nothing adopted, nothing committed.

Queue `handoffs/QUEUE_2026-10-22C.md` B5, session B. Design `b5_2026-10-22/design_written_before_code.md`, sha256
`24d2d2a3…255b`, hashed **05:24:51Z, before any B5 code**.

## 1. Settled from the code

- **The only `WifiLock` in the client** is the diagnostic `UdpTransportProbeActivity`:
  - `WIFI_MODE_FULL_LOW_LATENCY`, non-reference-counted;
  - only when its intent asks for it.
  **The stream (`NativeStreamActivity`), the controller sender and the receivers hold none.**
- **No `WakeLock` anywhere.** `PowerManager` is used for thermal reads only. The stream activity sets
  `FLAG_KEEP_SCREEN_ON`: the screen stays on, but that is not a CPU wake lock or a Wi-Fi lock.
- So during a stream the onn's Wi-Fi power save is the platform default. BENCH-R1 cell 8's 18 silences of ≥ 250 ms
  on an idle, unimpaired LAN (15.6 / 10 min, the pad sending ~430 packets / s) are consistent with radio power-save
  dozes. They are equally consistent with the room. **B5 builds the A/B that tells them apart. It does not claim the
  cause.**

## 2. What the platform documents (the host's SDK, API 37 stubs, `android_docs_wifilock.txt`; nothing fetched)

- **`WIFI_MODE_FULL_LOW_LATENCY`:** "operate with a priority to achieve low latency". It is active only while
  connected, **screen on**, and **app in the foreground**. The costs are battery, throughput, and fewer scans (it may
  not roam). The documented example is "real time gaming". The onn is a TV streaming in the foreground with the
  screen on, so all three conditions hold during a stream.
- **`WIFI_MODE_FULL_HIGH_PERF`:** "will not go to power save". **Deprecated, and "automatically replaced with
  `WIFI_MODE_FULL_LOW_LATENCY`"** on the documented platform.
  - The stubs give no "since" level. The onn runs an Android 14 build (`D_BASE_R1_…`). Recalled, not on the host:
    the deprecation is API 34.
  - **Whether `high_perf` differs from `low_latency` on the onn is BENCH-R2's to see.**
- **Permission:** "Any application using a WifiLock must request `android.permission.WAKE_LOCK`". It is **already
  declared**, a normal permission. `CHANGE_WIFI_STATE` is not named by the WifiLock docs; it is also already
  declared. **No manifest change.**

## 3. What was built (`b5.diff`: `NativeStreamActivity.kt` +25, `StreamWifiLock.kt` new, `StreamWifiLockTest.kt` new)

- **The property** `debug.privyhub.wifi_lock` (reflection, B3's convention; a reboot clears it):
  - `low_latency` → `WIFI_MODE_FULL_LOW_LATENCY` on API ≥ 29, else `HIGH_PERF`;
  - `high_perf` → `WIFI_MODE_FULL_HIGH_PERF`;
  - anything else / absent → off.
- **One lock per activity, non-reference-counted** (tag `PrivyHubStreamWifi`):
  - `acquire()` is idempotent and `release()` frees it once, so repeated sessions never stack;
  - every platform call is in try / catch: it cannot fail or delay a stream.
- **Acquired** in `startSession` (after `sessionStarted = true`) and in a new `onResume()` while a session is active.
- **Released** in `stopLocalPipeline()`, which runs only at a session's end: `surfaceDestroyed`, `stopSession` (which
  `onDestroy` and back reach). Also released in a new `onPause()`.
- So the lock never outlives the session or the foreground, which is the only place low-latency mode works anyway.
- **The session report, flag on only:** `wifi_lock_mode` and `wifi_lock_held` (the platform's `isHeld()` at the first
  acquire).

**Property absent** (`proof_flag_absent.py` → `proof_flag_absent.md`): **PROVEN**.
- 0 lines removed or changed.
- All 25 added lines are comments, the lazy holder (null without the property), null-safe calls, or the two
  overrides calling `super` first.
- The only new work when absent is one reflective property read per activity, as B3's.

## 4. Tests and the APK

**The tests** (`tests_apk.txt`): `:app:testDebugUnitTest --rerun` gives **85/85**, which is 78 existing, unchanged,
plus `StreamWifiLockTest` 7:
- the flag table;
- the property absent on the JVM is off;
- the lock type per API level;
- one non-reference-counted lock, idempotent acquire, a single release;
- 5 sessions with no stacking;
- release before acquire is nothing;
- a throwing platform call, and no `WifiManager`, never escape.

**The APK** (`apk_sha256.txt`, `build_console.txt`): **`8a69a48095a36d7fa0fbcdbba370cc4abad5442d5f21077a7c09fc01b0c7b767`**,
9,608,270 B.
- Built offline in `/tmp/b_q22c/PrivyHub`, with only the companion active.
- The signer is the same as the installed APK's (digests compared, not printed).
- **NOT installed.** BENCH-R2 installs B7's APK, which carries B5 + B7. This one is pinned for the record.

**The first build ran on the tree's project, an incident, disclosed and repaired** (`incident_tree_build.md`):
- Gradle reused a configuration cache that carries the tree's absolute paths, so the first `gradlew` in the copy
  rebuilt the tree's gitignored `PrivyHub/app/build/` from HEAD's unchanged source.
- That replaced the tree's APK file `043891e1…` (CL-B5's, also kept in `cl_b7_preserved/`).
- No source changed and nothing was installed.
- **All 289 overwritten files were restored byte-equal from the copy.** 24 newly created intermediates are left
  (nothing deleted) and listed.
- Every later build uses `--no-configuration-cache` and is checked: no tree file newer than a marker, and the copy's
  sources in the output. The second build compiled the copy's file, and 0 tree files changed.

## 5. For A (BENCH-R2): the Wi-Fi lock A/B on the idle LAN

- **Install** `8a69a480…` or B7's (which also carries this).
- **Run** shim `none`, the hold off, the pad untouched, ~10 min each, in the same hour:
  - (a) `debug.privyhub.wifi_lock` empty;
  - (b) `adb shell setprop debug.privyhub.wifi_lock low_latency`;
  - (c) `… high_perf`.
- **Read:**
  - the control-gap log's uplink silences ≥ 250 ms per 10 min (cell 8 read 15.6);
  - the report's `wifi_lock_mode` / `wifi_lock_held`.
- **Interpretation:**
  - (b) near 0 means the gaps were the radio's power save, and B6's H can be revisited;
  - (b) = (a) means the room or the AP;
  - (b) = (c) means the onn maps one to the other.

## 6. Files

**`b5_2026-10-22/`:**
- `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/`, `predecessor_sha256.txt`, `after_sha256.txt`;
- `design_written_before_code.md`, `design.sha256`, `design_hashed_at.txt`;
- `android_docs_wifilock.txt`;
- `b5.diff`, `diffstat.txt`;
- `proof_flag_absent.py`, `proof_flag_absent.md`;
- `build_started_at.txt`, `build_console.txt`, `tests_apk.txt`, `apk_sha256.txt`;
- `incident_tree_build.md`, `incident_first_build_console.txt`, `incident_tree_new_files.txt`;
- `redact_check.py`, `redact_check.txt`, `manifest.sha256`.

**Elsewhere:** `PrivyHub/app/src/main/java/streaming/StreamWifiLock.kt` (new), `NativeStreamActivity.kt`,
`PrivyHub/app/src/test/java/streaming/StreamWifiLockTest.kt` (new); `patches/B5_CLIENT_WIFI_LOCK.md`;
`logs/b5_git_status.txt`.

The rules held, apart from the incident above:
- no stream, no adb, no sudo, no nft;
- the Opal untouched;
- gradle `--offline` with only the companion active;
- nothing fetched, nothing deleted;
- nothing of A's touched.
