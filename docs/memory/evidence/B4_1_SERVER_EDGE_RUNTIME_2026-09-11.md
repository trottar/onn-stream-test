---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B4.1 server legacy-edge runtime validation

Fresh classification:

`B4_1_SERVER_LEGACY_EDGE_RUNTIME_CONFIRMED`

Validated:
- Games legacy StreamManager import count = 0;
- legacy `self._stream` reference count = 0;
- no forbidden legacy server tokens remain;
- all required native tokens remain;
- 13 NativeStreamManager calls remain;
- `stream_manager.py` unchanged and retained;
- `native_stream.py` unchanged;
- companion status available;
- `stream_host` field absent;
- legacy `/stream-status` disabled (HTTP 400);
- representative game active;
- native stream ready and active;
- native kind `native_stream_host`;
- capture backend `windows_graphics_capture`;
- encoder `h264_nvenc`;
- transport `rtp_udp_xor_fec`;
- Sunshine process not running.

Conclusion:

The GamesPlugin -> StreamManager/Sunshine execution edge is removed and the
normal native game path is runtime validated. Proceed to the isolated Android
Moonlight edge. Legacy manager/runtime artifacts remain physically installed.
