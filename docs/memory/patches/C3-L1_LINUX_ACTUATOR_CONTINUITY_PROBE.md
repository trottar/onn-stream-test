---
memory_schema: 1
as_of: 2026-09-18
durable_memory_updated: true
---

# C3.L1 — Linux encoder-only actuator continuity probe

## Purpose

Add the narrow Linux encoder-only replacement seam and its continuity
diagnostic, so the Linux actuator interruption cost can be measured.

The probe holds bitrate at the 7000 reference, encodes no acceptance threshold,
and implements no adaptation policy.

## Expected predecessor

The `C3.L0R1` commit.

## Changed scope

Added:

- `companion/diagnostics/c3_linux_actuator_probe.py` — Linux encoder-only cycle.
- `docs/memory/patches/C3-L1_LINUX_ACTUATOR_CONTINUITY_PROBE.md`.

Replaced:

- `companion/native_stream.py` — one method,
  `diagnostic_c3_actuator_continuity_cycle()`, now selects the probe
  implementation by platform and refuses unsupported hosts. No other production
  behavior is touched.
- `docs/memory/CURRENT.md`, `docs/memory/investigations/ACTIVE.md`,
  `docs/memory/investigations/C3_LINUX_ACTUATOR_BOUNDARY.md`,
  `docs/memory/2026-09-18.md`.

Generated and validated:

- `docs/memory/patches/PATCH_INDEX.md`.

## Intentionally unchanged scope

- `companion/plugins/games.py` — the existing loopback-only
  `c3-actuator-continuity-cycle` action is reused;
- `tools/probe_c3_actuator_continuity.py` — the existing runner is reused;
- `companion/diagnostics/c3_actuator_probe.py` — the Windows implementation;
- `companion/diagnostics/c3_fixed_bitrate_probe.py`;
- `native_stream_profiles.py`, `native_fec_relay.py`,
  `native_host_telemetry.py`, `native_session_io.py`;
- all Android source, including the streaming constants;
- `.gitignore`;
- every `C3.L0` audit conclusion.

## Why no new action and no new tool

The Linux cycle emits the same `privyhub_c3_actuator_cycle_probe_v1` schema and
the same three `video.*` timing fields the existing runner consumes. Reusing the
validated evidence path avoids a parallel implementation and keeps one evidence
format across both backends.

## Hazard found during implementation

`status()` calls `_reap_locked()`, which calls `_stop_locked()` when it observes
an exited encoder. During the swap the encoder is deliberately dead, so a
concurrent `status()` would have stopped the FEC relay and session I/O — the
exact lifecycle violation this probe exists to avoid.

The probe clears `manager._process` before killing the old process. A
behavioural check asserts that ordering rather than trusting the comment.

## Validation performed

- installer Python compile;
- 48 deterministic behavioural checks of the probe against a fake manager, with
  no real process, network or X11 access, covering: payload shape and schema;
  FEC, audio and controller continuity across the cycle; `_process` cleared
  before the kill; no bitrate override passed to the command builder;
  `_stop_locked` never called; replacement-exit and RTP-never-resumed failure
  paths each clearing `_process` while leaving FEC and session I/O intact; and
  twelve precondition rejections each asserted to modify nothing;
- installed-Python compile gate inside the installer;
- installer self-test covering correct install, wrong-state rejection before
  modification, idempotent reinstall, generated-index correctness, memory-health
  gate pass and failure-forcing-rollback, and forced-validation rollback with
  exact-byte restoration;
- payload and installed SHA-256 verification;
- LF line endings and trailing newline preserved;
- `git diff --check` and ZIP integrity executed by the delivery block.

Two defects were found by these checks during development and fixed before
packaging: the initial probe test fixture omitted the log handle a live stream
always has, and an inherited installer assertion still referenced the `C3.L0R1`
patch record name.

## Not claimed

**Runtime validation.** The probe has not been run against a live Linux game
session. The Linux encoder-only interruption cost remains unmeasured and the
automatic bitrate controller remains blocked.

This is a development patch until runtime evidence exists.

## Result

`INSTALLED SUCCESSFULLY` on the run recorded in `docs/memory/2026-09-18.md`.

## Next

Run the probe against a live Linux game session and record the measured
interruption in `docs/memory/evidence/`.
