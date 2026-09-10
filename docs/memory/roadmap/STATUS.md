---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: e65e8f89604ce325e6e3e0537d0287070b8996c5
---

# Authoritative Roadmap Status — 2026-09-10

This file is the compact status companion to `docs/ROADMAP.md` v2.

| Phase | Status | Immediate meaning |
|---|---|---|
| **A — Emulator Subsystem** | **COMPLETE / PUSHED** | Checkpoint `e65e8f89` |
| **B — Diagnostics & Clean Native Baseline** | **NEXT** | Unified diagnostics first, then Sunshine/Moonlight removal |
| **C — Adaptive Streaming Architecture** | PLANNED | Explicit profiles, telemetry, adaptive bitrate/FEC, 1080p, source abstraction |
| **D — Media Library / VOD UX** | PLANNED | Recursive poster art, local-first metadata/library polish |
| **E — Resource Scaling / Linux** | PLANNED | Formal workloads, Windows benchmark, cheap Linux tiers, capability scaling |
| **F — Open Platform / Firmware** | OPTIONAL / PARALLEL | OpenBIOS evaluation with compatibility fallback |
| **G — Smart-Home & Client Expansion** | FUTURE | Cameras, devices, storage, remote PC game relay, handheld clients |

## Phase A coverage note

SNES and PS1 have runtime coverage. NES and Genesis had zero local fixtures
during A9 and remain explicitly not runtime validated. This is a coverage gap,
not an active regression.

## Immediate sequence

```text
B1 diagnostic inventory
→ unified schema / health snapshot
→ GUI diagnostics / self-test / sanitized bundle
→ Sunshine/Moonlight inventory/removal
→ native-only regression
→ clean-native checkpoint
→ Phase C
```

## Adaptive-streaming rule

For local streams, adapt to measured PC→isolated-LAN/Wi-Fi→client path health,
not router Internet/WAN throughput. Start with bitrate-only adaptation while
holding resolution/60 fps stable. Consider FEC adaptation only after bitrate
control is independently measurable.

## OpenBIOS rule

OpenBIOS is a portability/customization/debuggability candidate, not a promised
performance optimization. Keep the validated compatibility BIOS path available
until an explicit compatibility matrix justifies otherwise.
