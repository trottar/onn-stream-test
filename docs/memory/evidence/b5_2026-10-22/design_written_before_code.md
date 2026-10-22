# B5 — the client's Wi-Fi lock during a stream: design (written and hashed before any B5 code)

Queue `handoffs/QUEUE_2026-10-22C.md` item B5, session B. Baseline HEAD 144e5c7 (`PrivyHub/` clean vs HEAD).

## 1. Settled from the code: no Wi-Fi lock is held during a stream; no wake lock

- **Wi-Fi lock:** the whole client (`PrivyHub/app/src/main`) has one `WifiManager.WifiLock`, in the diagnostic
  `diagnostics/UdpTransportProbeActivity.kt`:
  - `WIFI_MODE_FULL_LOW_LATENCY`, `setReferenceCounted(false)`;
  - only when the probe's intent asks `wifi_lock_mode=low_latency`;
  - released on the probe's end / `onDestroy`.
  **The stream activity (`streaming/NativeStreamActivity.kt`), the controller sender, the receivers and
  `MainActivity` hold none.**
- **Wake lock:** none anywhere (`PowerManager` is used only by `ThermalSampler` for thermal reads).
  - The stream activity sets `WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON` (`onCreate`), and the main layout has
    `android:keepScreenOn="true"` on a view.
  - These keep the screen on. They are not a CPU wake lock and not a Wi-Fi lock.
- **The manifest already declares** `INTERNET`, `ACCESS_WIFI_STATE`, `CHANGE_WIFI_STATE`, `WAKE_LOCK`. All are
  normal permissions, granted at install, no prompt.
- So the Wi-Fi radio's power-save behaviour during a stream is the platform's default. **B5 goes ahead.**

## 2. What the platform documents (the host's SDK: `platforms/android-37.0/android-stubs-src.jar`, `WifiManager.java`; nothing fetched)

- `WIFI_MODE_FULL_LOW_LATENCY`: "Wi-Fi will operate with a priority to achieve low latency". It is active only:
  1. while connected to an access point;
  2. **while the screen is on**;
  3. **while the acquiring app is in the foreground**.
  The documented costs: battery, throughput, and less frequent scanning (no roaming to a better AP). The documented
  use case: "real time gaming".
- `WIFI_MODE_FULL_HIGH_PERF`: "Wi-Fi will not go to power save … active even when the screen is off or the app is in
  the background". **Deprecated: "automatically replaced with `WIFI_MODE_FULL_LOW_LATENCY` … any request to
  `WIFI_MODE_FULL_HIGH_PERF` will now obtain a `WIFI_MODE_FULL_LOW_LATENCY` lock instead."**
  - The stubs carry no "since" level.
  - The onn runs an **Android 14** build (`D_BASE_R1_…` §: "on this Android 14 build").
  - Recalled, not on the host: the deprecation is API 34. Whether the onn's build already maps `high_perf` to
    low-latency is therefore not settled here. **The BENCH-R2 A/B answers it:** equal counts mean equal locks.
- `WifiLock`: "Any application using a WifiLock must request the `android.permission.WAKE_LOCK` permission"
  (declared). Non-reference-counted: "the first call to acquire will lock the radio, but subsequent calls will be
  ignored. Only one call to release will be required". `isHeld()`.
- `CHANGE_WIFI_STATE` is not named by the WifiLock docs. It is already declared, for the probe and others. **What is
  needed: `WAKE_LOCK`, present.** No manifest change.

## 3. The flag and the lock

- **`debug.privyhub.wifi_lock`** (system property; CL-B7P / B3's convention, read by reflection, any failure =
  absent):
  - `low_latency` → `WIFI_MODE_FULL_LOW_LATENCY` on API ≥ 29, else `WIFI_MODE_FULL_HIGH_PERF` (the platform has no
    low-latency mode below 29);
  - `high_perf` → `WIFI_MODE_FULL_HIGH_PERF`;
  - absent, or anything else → off. **Off = today:** no `WifiManager` call, no lock object.
- **New file `streaming/StreamWifiLock.kt`:**
  - `StreamWifiLockFlag`: `PROPERTY`, `parse(value) → Mode?`, `fromSystem()`, `lockType(mode, sdkInt)`;
  - `StreamWifiLock(handle)`: `acquire()`, `release()`, `held`. The platform lock sits behind a three-method
    interface, so the JVM tests use a fake.
  - **One lock object per activity, non-reference-counted** (`setReferenceCounted(false)`, as the probe). Repeated
    `acquire()` is idempotent, and one `release()` frees it, so repeated sessions in one activity cannot stack
    references. `acquire()` is a no-op when already held; `release()` is a no-op when not held.
  - Every platform call is in try / catch: **the lock can never fail or delay a stream.**
  - The lock's tag: `PrivyHubStreamWifi`.
- **Hooks in `NativeStreamActivity`** (each one a null-safe call on a lazily built holder that is `null` unless the
  property is set):
  - `startSession`: after `sessionStarted = true` → `acquire()`;
  - `stopLocalPipeline()` → `release()`. It runs only at a session's end: `surfaceDestroyed` and `stopSession`
    (which `onDestroy` and the back path call);
  - **`onPause()`** (new override, `super` first) → `release()`. **`onResume()`** (new override) → `acquire()` only if
    `sessionStarted`. A lock never outlives the foreground, which is where low-latency mode works anyway.
  - `onDestroy` reaches `stopSession` → `stopLocalPipeline` → `release()`.
- **Logged, flag on only:** the session report gains `wifi_lock_mode` / `wifi_lock_held` (the mode asked, and whether
  the platform reports the lock held at the first acquire), so BENCH-R2 can tell the run had it. Absent = no new key
  (B3's pattern).

## 4. Tests (JVM, `StreamWifiLockTest`)

1. the flag table (`low_latency`, `high_perf`, padded / upper case, garbage, empty, null);
2. the property absent on the JVM gives off;
3. `lockType` per SDK: 28 → `HIGH_PERF`, 29 → `LOW_LATENCY`, `high_perf` → `HIGH_PERF`;
4. with a fake handle: non-reference-counted set once; acquire twice = one platform acquire; release once frees;
   release when not held = nothing; acquire after release re-acquires (sessions 2..n); a throwing platform call is
   swallowed and `held` is false;
5. the report keys present only when on.

The existing tests must stay unchanged and green: 78 at B3.

## 5. The APK

`sh ./gradlew --offline :app:testDebugUnitTest --rerun :app:assembleDebug`, in the copy `/tmp/b_q22c/PrivyHub`, only
when no `privyhub-*` unit but the companion is active.
- Pinned: sha256, bytes, the signer compared with the tree's build output. **NOT installed.**
- B7's APK will carry B5 + B7. That APK is the one BENCH-R2 installs. B5's own is pinned for the record.

## 6. For A (BENCH-R2)

The count of uplink silences ≥ 250 ms per 10 min on the idle LAN (shim `none`, the hold off, the pad untouched; the
control-gap log), same hour:
- the property absent;
- `low_latency`;
- `high_perf`.

BENCH-R1 cell 8 read 15.6 / 10 min (cell 1: 11 in 11.5 min).
- **If `low_latency` brings it near 0, the gaps were the radio's power save, and the hold's false triggers mostly go
  with them.**
- If not, they are the room or the AP.
- If `high_perf` = `low_latency` within noise, the onn maps one to the other.
