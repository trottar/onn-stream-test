---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B4.4 code-orphan cleanup runtime validation

Fresh classification: `B4_4_CODE_ORPHAN_CLEANUP_RUNTIME_CONFIRMED`

Validated:
- MainActivity SHA-256 `394d2b839fdb01f2988a0054b42e139e419e02207728f914e1713287992733cc`;
- MainActivity CRLF preserved;
- orphan helper tokens absent;
- required native tokens intact;
- AndroidManifest unchanged;
- B4.1 games.py unchanged;
- `companion/games/stream_manager.py` physically deleted;
- fresh companion status available;
- representative game active;
- native stream ready/active on windows_graphics_capture / h264_nvenc / rtp_udp_xor_fec;
- Sunshine process not running.

Conclusion: code-orphan cleanup is runtime validated after a clean companion
restart. Capture exact physical legacy artifact hashes and external legacy state
before deletion.
