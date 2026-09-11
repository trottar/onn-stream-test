---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B4.2 Android Moonlight-edge runtime validation

Fresh classification:

`B4_2_ANDROID_LEGACY_EDGE_RUNTIME_CONFIRMED`

Validated:
- MainActivity SHA-256 `d9f7928062a86cdab643ef34b6fa8235a03a2bc900a3d8d7f578cd720d5bc2ea`;
- AndroidManifest SHA-256 `ab1140c3230582f9dbbbf3c179d8fa08363971d9289e08442487f3849c7ac8a2`;
- MainActivity CRLF preserved;
- no Sunshine/Moonlight/com.limelight tokens remain in MainActivity;
- `openGameStreamClient` absent;
- manifest contains no com.limelight;
- all required native tokens remain;
- B4.1 games.py unchanged at
  `f1271c865cdf88b971da4116d7eb887bf9855864ce1ae848baafc7a3452e0f9c`;
- representative game active;
- native stream ready/active;
- capture backend `windows_graphics_capture`;
- encoder `h264_nvenc`;
- transport `rtp_udp_xor_fec`.

Conclusion:
the Android client compatibility edge is removed. Before deleting physical
legacy files or uncaptured helper definitions, run a focused orphan-reference
audit.
