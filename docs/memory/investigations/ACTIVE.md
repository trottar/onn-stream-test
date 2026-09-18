# Active investigations

## C3 Linux actuator boundary

Record: `C3_LINUX_ACTUATOR_BOUNDARY.md`

Question: can the existing Linux streaming architecture expose safe
backend-neutral quality controls without disturbing validated playback?

State: source audit COMPLETE; Linux runtime evidence PENDING.

Next diagnostic: `C3.L1` — one loopback-only same-bitrate 7000 to 7000
encoder-only cycle on Linux, measuring RTP interruption while preserving the FEC
relay, process audio, persistent controller and emulator lifecycle.

Requires one narrow internal Linux encoder-only replacement seam that does not
call `_stop_locked()`. No such seam exists today.

Blocked downstream: Linux actuator capability classification, Linux
fixed-bitrate envelope revalidation, and the automatic bitrate controller.

## Deferred, not active

- UDP burst/gap pathology — awaiting representative Linux replay. See
  `DEFERRED.md` and `docs/KNOWN_ISSUES.md`.
- Adaptive FEC — C4.
- Linux host resource telemetry gap — recorded in `docs/KNOWN_ISSUES.md`; not an
  active investigation.
