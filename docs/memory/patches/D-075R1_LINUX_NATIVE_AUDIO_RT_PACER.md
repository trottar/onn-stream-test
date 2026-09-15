# D-075R1 Linux native-audio RT pacer correction

Status: **RUNTIME VALIDATED**

Purpose: correct the sender-cadence flaw discovered after D-075 functional
runtime validation without changing the validated PulseAudio route or PHA1 wire
contract.

Evidence sequence:
- Baseline 35 reproduced D-075 pacing jitter with the production audio backend
  isolated from video/FEC.
- Baseline 36 rejected Python interpreter switch-interval tuning.
- Baseline 37 rejected `Event.wait()` versus `time.sleep()` as the cause.
- Baseline 38 localized the dominant delay to sender wake lateness before PCM
  buffer access; PCM lock contention was negligible.
- Baseline 39 proved active RetroArch alone destabilizes a normal `SCHED_OTHER`
  5 ms userspace pacer.
- Baseline 40 showed `SCHED_RR` priority 1 restores stable sender timing.
- Baseline 41 proved only the sender thread can be promoted to `SCHED_RR/1`
  while the main process thread remains `SCHED_OTHER`; 1,000/1,000 packets were
  delivered with sender p95 5.0318 ms, max 5.116 ms, zero sub-2 ms intervals,
  and zero >=8 ms intervals.

Production correction:
- preserve D-075 managed-PID PulseAudio routing, dedicated sink/monitor capture,
  PCM buffering, PHA1 v1 framing, and hybrid deadline loop;
- promote only the Linux PHA1 sender thread to `SCHED_RR` priority 1 from inside
  that thread;
- verify the resulting scheduler policy/priority before sending;
- fail the Linux audio subpath if the thread cannot acquire the required policy;
- expose scheduler state in public helper status and timing evidence;
- never invoke `sudo` or grant broad process capabilities from production code.

Permission model:
- development runtime validation grants only the probe process a temporary
  `RLIMIT_RTPRIO=1` using privileged `prlimit`;
- persistent deployment should scope `LimitRTPRIO=1` to the eventual PrivyHub
  service instead of granting `CAP_SYS_NICE` to the Python interpreter.

Unchanged:
- Windows WASAPI process-loopback backend;
- Android NativeAudioReceiver and PHA1 contract;
- PulseAudio routing architecture;
- video/FEC;
- PHI1/controller output;
- EmulatorManager;
- telemetry.
