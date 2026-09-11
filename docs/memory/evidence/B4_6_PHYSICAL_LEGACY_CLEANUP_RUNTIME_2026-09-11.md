---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B4.6 physical legacy cleanup runtime validation

Classification:
`B4_6_PHYSICAL_LEGACY_CLEANUP_RUNTIME_CONFIRMED`

Validated project state:
- all nine B4.5-authorized legacy target paths are absent;
- all nine RetroArch Moonlight-name non-target paths remain;
- B4.4 production source hashes are unchanged;
- representative game session active;
- native stream ready/active;
- capture backend `windows_graphics_capture`;
- encoder `h264_nvenc`;
- transport `rtp_udp_xor_fec`;
- Sunshine process not running.

Android package state:
- not verified by B4.6 because its probe searched only PATH and returned
  `ADB_UNAVAILABLE`;
- zero installed count in that result is not evidence of absence.

The existing `tools/build_install_onn.ps1` has broader validated ADB discovery and
private recovery. B4.7 reuses that pattern without logging device identifiers
or network addresses.
