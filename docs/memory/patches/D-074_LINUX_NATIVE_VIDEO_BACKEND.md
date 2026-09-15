# D-074 Linux native-video backend

Status: **DEVELOPMENT PATCH / RUNTIME E2E PENDING**

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
