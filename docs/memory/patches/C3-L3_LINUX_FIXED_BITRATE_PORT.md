# C3-L3: Linux Fixed-Bitrate Cycle Port

Date: 2026-09-19
Tier: 1 (companion-side Python; no compile-time type/build check exists for
this language on this host, but no runtime architecture change either —
existing, validated restart primitive reused unchanged in method).

## Problem

`C3.L3`'s existing probe scripts
(`tools/probe_c3_fixed_{5000,5500,6000}_characterization.py`) drive a
loopback-only companion route (`c3-fixed-bitrate-{5000,5500,6000}-cycle`)
that calls `_run_c3_fixed_bitrate_cycle` in
`companion/diagnostics/c3_fixed_bitrate_probe.py`. That function is built
entirely around the Windows-only WGC (Windows Graphics Capture) replacement
mechanism: it requires `manager._wgc_ready()`, a real `hwnd`, and spawns
`manager._wgc_bridge_path()` as a separate capture subprocess. None of that
exists on Linux, so every attempt fails immediately with HTTP 503 /
`RuntimeError` (confirmed from a live crash log,
`logs/games/c3_fixed_5000_crash_20260919T044851Z.txt`:
`wgc_runtime_unavailable`-class failure surfaced only as
`"...characterization failed: RuntimeError"`, with the real reason hidden by
a `type(exc).__name__`-only error wrapper in `native_stream.py`).

## Root cause

Not a missing feature — an architecture mismatch. The Linux native-video
path already has its own validated encoder-only restart primitive
(`run_c3_linux_actuator_continuity_cycle`, `C3.L1`/`C3.L1R1`, COMPLETE /
RUNTIME VALIDATED), because Linux capture is a single x11grab ffmpeg
process, not a separate capture bridge. That primitive was written to
restart at the *same* (reference) bitrate only. Its call to
`manager._build_linux_ffmpeg_command(...)` was already written to accept
optional `bitrate_kbps` / `max_bitrate_kbps` overrides — nothing on the
Linux side had ever passed them.

## Fix

Additive. No existing Linux or Windows runtime behavior changed.

- `companion/diagnostics/c3_linux_actuator_probe.py`: added
  `FIXED_BITRATE_SCHEMA`, `FIXED_BITRATE_MODE`,
  `SUPPORTED_FIXED_BITRATES_KBPS = (5000, 5500, 6000)`, and
  `run_c3_linux_fixed_bitrate_cycle(manager, target_bitrate_kbps, ...)` — a
  parameterized copy of `run_c3_linux_actuator_continuity_cycle` that (a)
  validates the target is one of the three characterization bitrates, (b)
  requires the stream to already be at the 7000 kbps reference bitrate
  before starting (same starting-state requirement the Windows
  `reference_profile_not_7000` / `characterization_requires_reference_start`
  checks enforce), (c) passes `bitrate_kbps=target, max_bitrate_kbps=target`
  into `_build_linux_ffmpeg_command`, (d) sets
  `manager._active_bitrate_kbps = target` on success (restored to the
  pre-cycle value on failure, matching the Windows implementation's own
  rollback at `c3_fixed_bitrate_probe.py`), and (e) emits the same
  `privyhub_c3_fixed_bitrate_cycle_v1` schema and `video`/`fec`/`audio`/
  `controller` payload shape as the Windows path, confirmed field-for-field
  against what `tools/probe_c3_fixed_5000_characterization.py` actually
  reads from the cycle response (`schema`, `ok`, `target_bitrate_kbps`,
  `video.first_rtp_resume_ms`, `fec.send_errors_delta`,
  `audio.send_errors_delta`, `controller.bad_packets_delta`).
- `companion/native_stream.py`: `diagnostic_c3_fixed_bitrate_{5000,5500,6000}_cycle`
  now dispatch on `self._linux_host()` / `os.name == "nt"`, mirroring the
  existing `diagnostic_c3_actuator_continuity_cycle` pattern exactly. The
  Windows branch calls the existing, unmodified
  `run_c3_fixed_bitrate_{5000,5500,6000}_cycle` functions with no argument
  change. Their `except Exception as exc: raise NativeStreamError(...)`
  handlers now include `str(exc)`, not only `type(exc).__name__` — the
  defect that hid `wgc_runtime_unavailable`-class detail behind a bare
  `RuntimeError` in the crash log above.

## Intentionally unchanged

- `companion/diagnostics/c3_fixed_bitrate_probe.py` (Windows WGC
  implementation) — byte-for-byte untouched.
- Stream profile: resolution, FPS, GOP, B-frames, FEC group size, RTP
  payload type, packet size, ports. Only the encoder's requested bitrate
  changes; `_build_linux_ffmpeg_command`'s other arguments are unchanged.
- `run_c3_linux_actuator_continuity_cycle` itself — untouched; the new
  function is additive, not a refactor of it.

## Validation performed

- Predecessor SHA-256 verified for `native_stream.py`,
  `c3_linux_actuator_probe.py`, and `docs/memory/CURRENT.md` before any
  write.
- Backup of all three files under `archive/patch_backups/` before writing.
- `python3 -m py_compile` on both changed Python files.
- Installed-hash verification against the exact bytes this installer wrote.
- `git diff --check` (best-effort; a missing/unusable `git` does not fail
  the install, since the code and memory validation above are the real
  gate).
- `tools/check_memory_health.py` as the final gate; full rollback of all
  three files if it fails.

Not yet performed: a real run of any of the three characterization cycles
against a live native game stream. That is next.

## Status

CODE INSTALLED. Not yet runtime validated.
