> **Note (the user, 2026-11-19):** the `L:\Projects\onn-stream-test` path named below is not used; the hub's repository is authoritative.

# PrivyHub Handoff — Portrait Handheld Mode Investigation

## Objective

Conduct a **read-only investigation** into adding a portrait handheld mode to the existing PrivyHub Android application, using the Samsung Galaxy Tab S6 Lite (SM-P610) as the initial test device.

The preferred concept is to divide the tablet's portrait display into two regions:

- **Upper region:** Game video, maintaining the original aspect ratio.
- **Lower region:** Virtual game controller with an on-screen D-pad, analog sticks, face buttons, triggers, and other necessary controls.

**Landscape mode must remain fully available and unchanged.** Portrait handheld mode should be optional, not a replacement.

## Background

The existing PrivyHub Android TV APK was installed directly on the Galaxy Tab S6 Lite.

Initial proof-of-concept tests succeeded:

- Application installs and launches.
- VOD playback works.
- PS1 game streaming works.
- A DualShock 4 pairs over Bluetooth and can navigate PrivyHub.

These were preliminary functional tests, not extended performance validation.

The broader goal is to develop an inexpensive, modular handheld PrivyHub client without unnecessary hardware purchases.

We previously considered custom 3D-printed enclosures, telescopic controllers, integrated batteries, and smaller tablets. However, using the existing tablet in portrait orientation with virtual controls could provide a usable handheld at **zero additional hardware cost**.

## Proposed Display Configuration

The SM-P610 has a 2000 × 1200 display.

When held vertically, a preliminary equal division would provide:

| Region | Available resolution |
|---|---|
| Upper game region | 1200 × 1000 |
| Lower virtual controller region | 1200 × 1000 |

A 16:9 game image could render at approximately 1200 × 675 within the upper region, preserving aspect ratio.

These are conceptual dimensions, not a finalized UI layout.

The investigation should also consider whether a 50/50 split is optimal or whether an adjustable division would be preferable.

## Investigation Scope

### 1. Android orientation architecture

Inspect the existing Android manifest, activity orientation settings, and window handling.

Determine how an optional portrait game-streaming activity or mode could coexist with the existing landscape behavior.

Preserve the onn Android TV experience.

### 2. Video rendering

Inspect:

- `NativeStreamActivity.kt`
- `AvcLowLatencyDecoder.kt`
- Existing `SurfaceView` rendering and scaling behavior
- Fullscreen and immersive-mode handling

Determine whether the current 1280×720 stream can be rendered within the upper portrait region without altering the Linux companion or decoding pipeline.

Evaluate aspect-ratio preservation and unused display space.

### 3. Virtual controller architecture

Inspect:

- `NativeControllerSender.kt`
- Existing Android `KeyEvent` and `MotionEvent` handling
- Controller state representation
- Player slot and input transmission logic

Determine whether touchscreen input can be translated into the **existing gamepad state and transport path**, rather than creating a parallel controller system.

Consider:

- D-pad and face buttons
- Dual analog sticks
- L1/R1 and L2/R2
- Start/Select
- L3/R3
- Simultaneous multitouch input
- Input release on touch cancellation, focus loss, or activity pause
- Optional customization of control placement and size

Evaluate analog-stick behavior, multitouch reliability, and potential input latency.

### 4. Landscape preservation

Determine how users could select between:

- **Landscape mode:** Existing fullscreen game display with external controller support.
- **Portrait handheld mode:** Upper video region and lower virtual controller.

An optional landscape virtual-controller overlay may be considered separately, but must not interfere with existing controller behavior.

Switching modes should ideally not require restarting the Linux companion's game session.

### 5. Performance and battery considerations

Evaluate potential implications of:

- Hardware video decoding while in portrait orientation
- Touchscreen rendering and multitouch processing
- Surface resizing or recreation
- Screen brightness and active display area
- Game input latency
- Thermal behavior

Do not assume that displaying black pixels on the LCD saves significant power. Identify what would actually need measurement.

### 6. Existing solutions

Investigate whether suitable open-source Android virtual gamepad components or input-handling approaches could be reused.

Favor modular, maintainable solutions compatible with PrivyHub's existing architecture.

Avoid unnecessary dependencies or substantial changes to proven streaming components.

## Repository and Project Requirements

Authoritative local repository:

`L:\Projects\onn-stream-test`

GitHub reference:

https://github.com/trottar/onn-stream-test

At the beginning of the investigation, consult:

- `docs/memory/CURRENT.md`
- `docs/memory/MEMORY.md`
- `docs/memory/handoffs/CURRENT_HANDOFF.md`
- Relevant architecture and controller documentation
- Current Android source files

Prefer current local source over older GitHub snapshots or conversation summaries.

## Strict Read-Only Requirement

**This investigation is analysis only.**

Do not:

- Modify source code.
- Modify project memory or documentation.
- Generate or install patches.
- Change Android manifests or Gradle configuration.
- Build or deploy an APK.
- Change the Linux companion.
- Modify the working onn or tablet installations.

No implementation work is authorized during this investigation.

## Requested Deliverable

Produce a technical feasibility report covering:

1. Whether portrait virtual-controller mode is feasible with the current architecture.
2. Which existing components can be reused unchanged.
3. Which files and interfaces would eventually require modifications.
4. Recommended orientation and UI architecture.
5. Recommended approach to multitouch and analog virtual controls.
6. Potential regressions and risks to existing landscape streaming.
7. Estimated implementation complexity.
8. A staged implementation and validation plan for future approval.

Clearly distinguish verified repository findings from proposed designs and assumptions.

**Do not implement anything.**

## Desired Outcome

Determine whether PrivyHub can support a practical, zero-additional-hardware handheld configuration using the existing Galaxy Tab S6 Lite, while retaining the fully functional landscape Android TV/streaming experience.

The immediate priority is **feasibility, architecture, and regression avoidance**, not code development.