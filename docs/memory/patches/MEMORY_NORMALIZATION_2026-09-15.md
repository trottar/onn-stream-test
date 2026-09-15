# Durable-memory normalization — 2026-09-15

Status after successful installer validation: **MEMORY NORMALIZED / RUNTIME UNCHANGED / CHECKPOINT PENDING**

## Purpose

Normalize the durable-memory continuation surface after the Phase-D Linux
migration and D079-D083 transport investigation accumulated contradictory
embedded "next step" statements.

## Authoritative state captured

- Phase D Linux migration is active.
- D073-D078 Linux host/runtime seams are validated at their documented scope.
- Integrated Linux/onn PS1 reaches a transport blocker after successful runtime,
  save-load, window discovery, controller preflight, and VAAPI encode.
- The deferred UDP pathology is reproduced bidirectionally while idle on the
  representative Linux + home Opal + onn path.
- Opal `wlan0`, `wlan1`, and `br-lan` ordinary packet-capture points are blind
  during confirmed endpoint traffic.
- Exposed OpenWrt flow-offload flags are falsified as a fix.
- D083/D083R1 are invalid as networking evidence; D082 is the last valid router
  boundary result.
- Open-ended Opal/Siflower reverse engineering is paused.
- Android's Linux auto-open `host_window_policy.window_found` dependency is a
  confirmed compatibility bug and the next narrow production patch candidate.

## Scope

Changed only durable-memory/documentation state. Production source, Android
behavior, emulator behavior, streaming behavior, router state, runtime data, and
network configuration are intentionally unchanged.

The installer verifies exact predecessor blobs for every existing touched file,
backs them up, performs deterministic replacements/appends, regenerates
`docs/memory/manifest.json`, validates JSON/markers, and runs `git diff --check`.
