# D-074 Linux native-video backend

Status: **HOST-SIDE RUNTIME VALIDATED / ANDROID E2E PENDING**

Purpose:
implement the Linux native-video architecture established by Baselines 29-31.

Production changes:
- pass the active `EmulatorManager` PID into `NativeStreamManager.start()`;
- discover only visible X11 windows owned by that managed PID;
- fail closed when no owned window is available;
- use one FFmpeg process for x11grab + VAAPI H.264;
- feed the existing loopback RTP/XOR-FEC relay unchanged;
- make native-stream liveness/status backend-aware.

Unchanged:
- Windows WGC/NVENC path;
- Android;
- FEC format/relay implementation;
- PHI1;
- audio backend;
- controller output backend;
- host telemetry implementation;
- emulator lifecycle.

Predecessor:
`f6875f3b562fc0440f514067f05cac9605884686`.

Runtime acceptance remains pending.


## Runtime result

Host-side runtime validation passed with real SNES content:
- `x11grab_window` + `h264_vaapi` active;
- 4,500 RTP and 680 PHF1 packets;
- zero skipped relay packets;
- zero relay send errors;
- clean stream teardown;
- graceful RetroArch shutdown.

Full onn/Android E2E remains pending.
D-075R1 does not alter the validated D-074 video backend. The audio scheduler
correction is isolated to `NativeAudioStreamer` and does not modify x11grab,
VAAPI, RTP, or PHF1/FEC behavior.
