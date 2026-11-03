# PrivyHub/

The Android TV client is the PrivyHub app on the onn. This directory is its Gradle project.

## The project layout

- `settings.gradle.kts`: the root project `PrivyHub`, with one module, `:app`.
- `build.gradle.kts`, `app/build.gradle.kts`: the build scripts.
- `gradle/libs.versions.toml`: the version catalog (AGP 9.3.2, among others).
- `gradle/wrapper/`: the wrapper (Gradle 9.5.0).
- `gradle/gradle-daemon-jvm.properties`: the daemon JVM toolchain (25).
- `gradle.properties`: the build settings. It turns the configuration cache on, which is why the records pass
  `--no-configuration-cache`.
- `gradlew`, `gradlew.bat`: the wrapper scripts.
- `local.properties`: the local SDK path. It is ignored by git.
- `app/src/main/`: the app.
  - `AndroidManifest.xml`, `res/`, `keepRules/`.
  - `java/`, top level:
    - `MainActivity.kt`: the catalog, the SETTINGS dialog (Hub host, identity v2, "Pair with hub…") and launch;
    - `TvRepository.kt`, `TvEpgRepository.kt`, `TvDatabase.kt`, `TvStateSyncClient.kt`: TV, the guide and the
      TV-state sync;
    - `GameCheatUiState.kt`;
    - `NflRepository.kt`.
  - `java/streaming/`: the native stream client:
    - `NativeStreamActivity.kt`;
    - `RtpH264Receiver.kt` and `AvcLowLatencyDecoder.kt` (hardware AVC);
    - `FecRs82.kt`;
    - `NativeAudioReceiver.kt` and the Opus files (`OpusAudioDecoder.kt`, `OpusDecodePipeline.kt`, `OpusFraming.kt`,
      `OpusDecodeMode.kt`);
    - `NativeControllerSender.kt`;
    - the link report and notice (`LinkReport.kt`, `LinkNotice.kt`);
    - the restart guard and fast restart (`RestartGuard.kt`, `RestartFast.kt`, `FastReady.kt`);
    - `StallSignal.kt`, `SurfaceHold.kt`, `PadSlots.kt`, `LossGuard.kt`;
    - `StreamWifiLock.kt`, `ThermalSampler.kt`, `DecoderReportUpload.kt`, `GameStreamStatusUi.kt`.
  - `java/identity/`: the session identity client: `AndroidIdentity.kt`, `IdentitySession.kt`, `SessionProtocol.kt`,
    `MediaDataSource.kt`.
  - `java/vod/`: the VOD player's retry (`VodRetry.kt`, `VodRetryAndroid.kt`).
  - `java/diagnostics/`: the Diagnostics / Self-Test screen (`DiagnosticsActivity.kt`) and the UDP transport probe
    activities (forward, reverse, loopback).
- `app/src/test/`: the JVM unit tests.
  - `java/streaming/`: 24 tests (the restart guard, link report / notice, Opus, stall, surface hold, pad slots, loss
    guard, client defaults and others).
  - `java/identity/`: the session protocol v1–v3 and the wire tests.
  - `java/vod/VodRetryTest.kt`.
  - `resources/`: the fixtures (`g3_s2`, `g3_s3`, `cl_b4`).
- `app/src/androidTest/`: `ExampleInstrumentedTest.kt` only.

Client-side behaviours that are not on by default sit behind `debug.privyhub.*` system properties on the onn, such as
`surface_hold`, `pad_slots` and `vod_retry`. On the onn today they are all empty (`docs/memory/CURRENT.md`).

## Building

The records build offline in a fresh copy of the tree, with the unit tests in the same run:

```text
cd PrivyHub
./gradlew :app:testDebugUnitTest :app:assembleDebug --rerun-tasks --offline --no-configuration-cache
```

The APK is `app/build/outputs/apk/debug/app-debug.apk`.

**Build output is ignored by git** (`app/build/`, `.gradle/`, `*.apk`). Kept APKs live under `app/build/` and are
never deleted:
- `<step>_installed/`: what was put on the onn;
- `<step>_preserved/`: the previous CONFIRMED APK at that step;
- `queue_l_built/`, `queue_m_built/`: built, not installed.

## The APK pin rule

1. A new build is only a **candidate**.
2. It goes on the onn for a pre-registered, attended run, and it is **CONFIRMED** only by that run's pre-registered
   rule: every cell that ran was valid (CL-B7 §6).
3. A CONFIRMED build is pinned by its sha256 in `tools/e1_suite.py` `EXPECT_APK` (and in
   `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`).
4. If the rule is not met, the CONFIRMED APK goes back on and the pin does not move. That happened in HOME-1:
   `docs/memory/evidence/HOME_1_TRIP_CLOSE_AND_QUEUE_L_CELLS_2026-11-02.md`.

Today **`fcd924c2…` is CONFIRMED** (CL-B14's build, kept in `app/build/cl_b14_installed/`). `tools/diag_check.py`
(the `apk` line) and `tools/e3_state.py` (`"apk"`) read the installed hash against the pin.
