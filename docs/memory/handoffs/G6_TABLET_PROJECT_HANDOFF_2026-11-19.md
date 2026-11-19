> **Note (the user, 2026-11-19):** the `L:\Projects\onn-stream-test` path named below is not used; the hub's repository is authoritative.

# Project Handoff: PrivyHub Android Tablet Client

## Objective

Adapt the existing PrivyHub Android TV application to run on a **Samsung Galaxy Tab S6 Lite (2020), model SM-P610**, as the foundation for a custom, inexpensive handheld streaming device.

The goal is to reuse the existing Android client and Linux companion server, making only necessary tablet-specific changes.

## Repository

https://github.com/trottar/onn-stream-test

**Important:** The local repository at `L:\Projects\onn-stream-test` is authoritative. GitHub may be behind.

Before implementation, inspect the current source and project memory:

- `docs/memory/CURRENT.md`
- `docs/memory/MEMORY.md`
- `docs/memory/handoffs/CURRENT_HANDOFF.md`

Follow the project's existing diagnostics, patch validation, rollback, and durable-memory procedures.

## Hardware

Samsung Galaxy Tab S6 Lite (2020), SM-P610:

- Exynos 9611
- 4 GB RAM
- 10.4-inch, 2000×1200 display
- Hardware H.264 decoding capability to be verified
- Dual-band Wi-Fi
- Original 7,040 mAh battery

The tablet currently consumes approximately **10% battery per 30 minutes** of Firefox video playback at 50% screen brightness.

Our initial target is approximately four hours of usable PrivyHub streaming from 100% to 20% battery.

No tablet modifications have been made.

## Existing PrivyHub Architecture

The current system includes:

- Kotlin Android TV client, originally developed for an onn device.
- Linux companion server.
- RetroArch emulation on the Linux host.
- H.264 streaming over UDP.
- Android `MediaCodec` hardware video decoding.
- Opus/PCM audio playback.
- Android gamepad input transmitted to the Linux server.
- Existing streaming diagnostics, FEC, and recovery infrastructure.

Intended architecture:

`Linux companion → Wi-Fi → Galaxy Tab S6 Lite → PrivyHub APK`

The tablet should function primarily as a lightweight streaming client, not perform game emulation locally.

## Repository Findings

The previous chat reviewed the actual GitHub repository.

Relevant files include:

- `PrivyHub/app/build.gradle.kts`
- `PrivyHub/app/src/main/AndroidManifest.xml`
- `PrivyHub/app/src/main/java/MainActivity.kt`
- `PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt`
- `PrivyHub/app/src/main/java/streaming/AvcLowLatencyDecoder.kt`
- `PrivyHub/app/src/main/java/streaming/NativeControllerSender.kt`

The manifest already provides a normal Android `LAUNCHER` category alongside `LEANBACK_LAUNCHER`.

It also declares:

```xml
<uses-feature
    android:name="android.software.leanback"
    android:required="true" />
```

This may need to become optional for general tablet compatibility, although direct APK sideloading may work unchanged.

The current Gradle configuration has `minSdk = 24`.

No tablet-specific modifications have been implemented or tested.

## Immediate Next Step

**T1 — Install and test the existing confirmed PrivyHub APK on the SM-P610 without changing any code.**

Determine whether:

1. The APK installs successfully.
2. The application launches normally.
3. The catalog displays correctly on the tablet.
4. Touchscreen navigation works.
5. The application connects to the existing Linux companion.
6. A game stream launches using the existing client.

If a failure occurs, diagnose that specific failure using existing code and instrumentation before modifying anything.

## Development Plan

**T1 — Initial compatibility:** Test the existing APK unchanged.

**T2 — Tablet interface:** Fix necessary launcher, touchscreen, display scaling, orientation, and navigation issues.

**T3 — Streaming validation:** Verify hardware-accelerated 1280×720 at 60 fps, frame continuity, audio, UDP packet reception, and latency using existing diagnostics.

**T4 — Controller integration:** Connect a Bluetooth or USB controller and validate button/axis mappings, player slots, and input latency.

**T5 — Battery optimization:** Measure actual PrivyHub battery drain at 50% brightness. Investigate reversible Android optimizations only after establishing baseline measurements.

**T6 — Physical handheld:** Investigate inexpensive telescopic controllers or custom 3D-printed grips. No hardware purchases are justified until software performance is validated.

## Critical Requirements

- Preserve the validated onn Android TV client.
- Do not change the Linux server unnecessarily.
- Reuse existing streaming and controller implementations.
- Make tablet-specific changes modular and reversible.
- Do not root, debloat, or replace the tablet OS prematurely.
- Preserve user files unless explicitly authorized.
- Do not request or expose IP addresses.
- Measure performance before optimizing.
- Update `docs/memory/` for meaningful changes.
- Follow existing project patch ZIP, validation, backup, and rollback conventions.

## Desired First Milestone

**PrivyHub runs on the Galaxy Tab S6 Lite, displays the existing catalog, connects to the Linux companion, and plays a game stream.**

Once that works, prioritize 720p60 decoder performance and battery life before investing in a physical handheld enclosure.