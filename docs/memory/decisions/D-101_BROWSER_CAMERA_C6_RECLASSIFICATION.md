---
memory_schema: 1
as_of: 2026-09-16
decision: D-101_BROWSER_CAMERA_C6_RECLASSIFICATION
status: accepted
---

# Browser/camera native streaming moves from D5 restoration to C6

## Decision

Do not create Linux ports of the legacy browser/camera runner paths as a D5
acceptance requirement.

Complete D5 with VOD, Live TV/EPG, and diagnostics/Self-Test. After the D8
Linux baseline checkpoint, return to remaining Phase C and implement
browser/app plus camera/live streaming through C6 generalized native source
abstraction.

## Rationale

- C6 already defines the intended reusable source/capture -> profile/encoder ->
  transport/FEC -> client-decoder architecture.
- Rebuilding old runners now would create a temporary parallel path likely to be
  replaced later.
- Browser streaming is strategically useful for a stationary/headless server and
  benefits from shared native streaming infrastructure.
- Client keyboard/mouse forwarding, including onn-attached Bluetooth HID where
  practical, fits the generalized browser/session input design.
- The current Linux Prototype 1 has no representative camera hardware.
- Broader smart-home camera/device integration remains Phase I.

## Roadmap sequence

`D5 -> D7 -> D8 -> remaining C/C6 -> E`
