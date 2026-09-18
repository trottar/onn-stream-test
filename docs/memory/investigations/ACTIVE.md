# Active investigations

## C3 Linux actuator boundary

Record: `C3_LINUX_ACTUATOR_BOUNDARY.md`
Decision: `../decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`

Question: can the existing Linux streaming architecture expose safe
backend-neutral quality controls without disturbing validated playback?

State: source audit COMPLETE; Linux encoder-only actuator COMPLETE / RUNTIME
VALIDATED across two cycles at 287-318 ms decoder output gap; `C3.L2`
classification COMPLETE.

Linux is `video_only_restart`: authorized for start-time profile selection,
manual and loopback-only diagnostic changes, fallback and recovery, and `C3.L3`
characterization; not authorized for automatic adaptation during play.
`live_bitrate_reconfigure` is not available under the current architecture.

Next diagnostic: `C3.L2a` — why the receiver's first accepted IDR is late after
an encoder-only cycle, when the replacement stream's first frame is a keyframe.
Start from existing decoder-session evidence and the Android receiver's resync
policy, not from a code change. The `C3.L1R1` "request an immediate IDR" lead is
premise-corrected: a fresh FFmpeg RTP stream already begins with in-band
parameter sets and an IDR.

Blocked downstream: the automatic bitrate controller (`C3.L4`), gated on the
`C3.L2a` result. `C3.L3` fixed-bitrate envelope revalidation is unblocked for
manual characterization and is sequenced after `C3.L2a`.

## Deferred, not active

- UDP burst/gap pathology — awaiting representative Linux replay. See
  `DEFERRED.md` and `docs/KNOWN_ISSUES.md`.
- Adaptive FEC — C4.
- Linux host resource telemetry gap — recorded in `docs/KNOWN_ISSUES.md`; not an
  active investigation.
