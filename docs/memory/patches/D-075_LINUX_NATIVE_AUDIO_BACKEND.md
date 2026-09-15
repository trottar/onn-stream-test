# D-075 Linux native-audio backend

Status: **DEVELOPMENT PATCH / FUNCTIONAL PATH VALIDATED / ORIGINAL CADENCE REJECTED**

Purpose:
implement the Linux native-audio architecture established by Baselines 32-34.

Production changes:
- preserve `NativeSessionIO` and the existing managed RetroArch PID handoff;
- resolve exactly one PulseAudio sink-input owned by that PID;
- fail closed on zero or ambiguous managed sink-inputs;
- create a temporary 48 kHz stereo PrivyHub null sink;
- move only the managed RetroArch playback stream into that sink;
- capture the sink monitor through FFmpeg as PCM S16LE stereo 48 kHz;
- emit the unchanged PHA1 v1 format in 240-frame / 5 ms packets;
- use the Baseline-34 hybrid monotonic pacer;
- send silence on source underflow so the paused stabilization phase can keep
  the transport cadence alive until gameplay resumes;
- restore the original PulseAudio route and unload the temporary sink on stop.

Unchanged:
- Windows WASAPI process-loopback implementation;
- Android NativeAudioReceiver;
- video and PHF1/FEC;
- PHI1 controller protocol and controller output implementation;
- EmulatorManager;
- host telemetry.

Predecessor:
`38785565573160235ad83a9a4361a1c7966038a6`.

Expected production input SHA-256:
`dd895f313a92af83fdf87b96f7c533db1389c4c015e463720c4e183c1b646e84`.

Runtime acceptance remains pending.
## D-075R1 cadence correction

The original D-075 PulseAudio route, PCM capture, PHA1 framing, and restoration
remain valid. Production runtime exposed sender scheduling jitter under active
RetroArch, so D-075 is not accepted in its original pacing form.

Baselines 39-41 established the correction: the PHA1 sender thread alone must
run `SCHED_RR` priority 1. The companion main thread remains `SCHED_OTHER`.
D-075R1 implements and verifies that thread-local scheduler requirement.

D-075R1 runtime revalidation passed. Sender-thread-only SCHED_RR priority 1 is the validated Linux native-audio pacing correction.
