---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: a9885ea356de38fcda3d22637f73c4f60d6b24de
durable_memory_updated: true
---

# C3.L1R1 — RTP baseline measurement correction

## Purpose

Correct a measurement defect in the `C3.L1` Linux actuator probe that reported
encoder spawn time as video resume time, and record the `C3.L1` runtime
evidence.

## Expected predecessor

`a9885ea356de38fcda3d22637f73c4f60d6b24de`

## The defect

The probe watched the FEC relay packet counter rise above a baseline to detect
video resumption. It took that baseline from the status snapshot read during
precondition checks, before the old encoder was killed. Old-encoder packets
arriving in that window already exceeded the baseline, so the first poll after
spawning the replacement succeeded immediately.

Observed: `host_first_rtp_resume_ms` 215.017 ms against `host_ffmpeg_spawn_ms`
215.007 ms, 0.010 ms apart, while the poll sleeps 10 ms between checks.

The `C3.L1` conclusion survives because `decoder_max_output_gap_ms` is measured
independently on the Android receiver. The headline host figure was wrong.

## Correction

- baseline taken after `_kill_managed_process` returns;
- `rtp_baseline_residual_packets` reported so the baseline can be challenged;
- `rtp_silence_after_spawn_ms` and `encoder_down_ms` added;
- the spawn is deliberately not delayed to drain the relay queue, because that
  would lengthen the interruption under measurement.

## Changed scope

Replaced:

- `companion/diagnostics/c3_linux_actuator_probe.py`;
- `docs/memory/CURRENT.md`;
- `docs/memory/2026-09-18.md`;
- `docs/memory/LEARNINGS.md`;
- `docs/memory/investigations/C3_LINUX_ACTUATOR_BOUNDARY.md`.

Added:

- `docs/memory/evidence/C3_L1_LINUX_ACTUATOR_RUNTIME_2026-09-18.md`;
- `docs/memory/patches/C3-L1R1_RTP_BASELINE_MEASUREMENT_CORRECTION.md`.

Generated and validated: `docs/memory/patches/PATCH_INDEX.md`.

## Intentionally unchanged scope

- `companion/native_stream.py` — the platform dispatch is correct;
- `companion/diagnostics/c3_actuator_probe.py` — the Windows probe shares the
  same baseline pattern, but Windows is the outgoing platform and its evidence
  is historical. Recorded, not modified;
- `companion/plugins/games.py` and `tools/probe_c3_actuator_continuity.py`;
- all Android source; `.gitignore`;
- every `C3.L0` audit conclusion.

## Validation performed

- installer Python compile and installed-Python compile gate;
- 56 probe behavioural checks against a fake manager, all passing, including a
  new regression group: residual packets reported, `rtp_packets_delta` free of
  pre-kill residue, `rtp_silence_after_spawn_ms` positive, `encoder_down_ms`
  measured, and a silent-replacement cycle correctly raising
  `replacement_rtp_did_not_resume`;
- the same 56 checks run against the **shipped defective probe**, which fails
  6 of them including the silent-replacement case. A regression test is not
  trusted until it has been shown to fail against the defect;
- installer self-test: wrong-state rejection, clean install, idempotent
  reinstall, generated-index correctness, memory-health gate pass and
  failure-forcing-rollback, forced-validation rollback with exact-byte
  restoration;
- payload and installed SHA-256 verification; LF endings and trailing newline
  preserved.

## Not claimed

The corrected probe has **not** been re-run against a live session. The true
Linux video-resume time is still unmeasured. The focused gameplay observation
is still missing, and `C3.L2` classification must not proceed without it.

## Result

`INSTALLED SUCCESSFULLY` on the run recorded in `docs/memory/2026-09-18.md`.

## Next

Re-run the probe, then classify the Linux actuator in `C3.L2`.
