---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 555cc4f
---

# Current State

Section headings below are fixed by `tools/check_memory_health.py`. Do not
rename or duplicate them; the checker requires each exactly once.

## Active Objective

Phase C Linux continuation: establish a safe, backend-neutral adaptive decision
boundary for the validated Linux native game stream.

## Current Work Item

`C3.L2` — Linux actuator classification.

Start from `PHASE_C_CONTEXT.md`. It is the compact, self-sufficient Phase C
continuation brief and should not require reading the wider memory hierarchy.

## Verified State

- C1 Linux profile/backend: COMPLETE / RUNTIME VALIDATED
  (`native_game_720p60_reference`, `x11grab_window`, `h264_vaapi`,
  `rtp_udp_xor_fec`, fail-closed render-node behavior).
- C2 stream telemetry: COMPLETE / RUNTIME VALIDATED. Linux baseline
  measurements are recorded in
  `evidence/C1_C2_LINUX_REVALIDATION_2026-09-18.md`.
- `C3.L0` actuator boundary audit: COMPLETE. Full map in
  `investigations/C3_LINUX_ACTUATOR_BOUNDARY.md`.
- `C3.L1` / `C3.L1R1` Linux encoder-only actuator: COMPLETE / RUNTIME
  VALIDATED across two clean cycles.
  Lifecycle preservation confirmed: FEC, process audio, controller and
  emulator all survived the cycle with zero errors and exactly one SSRC
  change.
- Linux decoder max output gap **318 ms** against Windows 791 ms on the
  directly comparable D-062 same-bitrate run: materially better, so the
  `C3.L0` boundary is met and Linux actuator classification is reopened.
  Evidence: `evidence/C3_L1_LINUX_ACTUATOR_RUNTIME_2026-09-18.md`.
- D4 Games and D5 media/server restoration: COMPLETE / RUNTIME VALIDATED.

Blocked or incomplete:

- automatic bitrate controller is **blocked**; D-070 rejected
  `video_only_restart` for seamless automatic in-game adaptation on Windows, and
  Linux has no measured actuator interruption cost yet;
- whether a ~287 ms automatic mid-game interruption is acceptable is **not
  decided**; that is the `C3.L2` question;
- whether an immediate-IDR request on the replacement encoder would shrink the
  gap is an **unauthorized open lead**, not an approved action;
- Linux host resource telemetry never starts; see `docs/KNOWN_ISSUES.md`.

## Next Action

Classify the Linux actuator in `C3.L2` and record it as a decision:
`live_bitrate_reconfigure`, `video_only_restart` or `unsupported`, plus whether
`video_only_restart` is acceptable for automatic mid-game adaptation.

Evidence needed for that decision already exists; no new probe is required to
make the classification itself. See section 5 of `PHASE_C_CONTEXT.md`.

## Success Criteria

Raw interruption and recovery measurements are captured with FEC, audio,
controller and game lifecycle demonstrably preserved. No acceptance threshold is
encoded in the probe.

Decision boundary:

- interruption materially below the Windows 0.84-0.95 s — reopen Linux actuator
  classification and proceed to `C3.L3` fixed-envelope revalidation;
- interruption comparable to Windows — `video_only_restart` is fallback-only on
  Linux too, the controller stays blocked, and the next item is the encoder-host
  architecture question.

Do not change during C3: resolution, frame rate, GOP, B-frames, FEC wire format,
RTP payload type, packet size, ports, process audio, controller transport,
emulator lifecycle, Android streaming constants, or any non-loopback control
surface.

## Do Not Reopen Without New Evidence

- D4 Games and D5 media/server restoration.
- The Windows-era C3 record (D-063, D-067, D-068, D-069, D-070, D-071).
- The deferred UDP burst/gap pathology, which is a Windows measurement awaiting
  representative Linux replay.

## Relevant References

- `PHASE_C_CONTEXT.md` — **start here**; compact Phase C continuation brief.
- `investigations/C3_LINUX_ACTUATOR_BOUNDARY.md` — actuator boundary map.
- `architecture/ADAPTIVE_BITRATE.md` — adaptation architecture and history.
- `architecture/STREAM_TELEMETRY.md` — C2 measurement contract.
- `evidence/C1_C2_LINUX_REVALIDATION_2026-09-18.md` — Linux baseline.
- `roadmap/STATUS.md` — roadmap position.
- `MAINTENANCE.md` — memory maintenance policy and required validation gate.
- `docs/KNOWN_ISSUES.md` — open gaps and deferred work.
