# Current Handoff

The authoritative resumable state is `../CURRENT.md`.
The compact Phase C brief is `../PHASE_C_CONTEXT.md`; **start there**. It is
self-sufficient and does not require reading the wider hierarchy.

D5 media/server restoration remains COMPLETE / RUNTIME VALIDATED.
D4 Games remains COMPLETE / RUNTIME VALIDATED.

This handoff replaces the 2026-09-18 version below (kept for history further
down this file). Everything in the old "Next work item" / "C3 entry
conditions" sections has been superseded by the two items closed on
2026-09-19, `C3.L2c` and `C3.L3`.

## 2026-09-19 work, in order

1. **`C3.L2c` — MediaCodec low-latency decode. Installed, runtime tested,
   FALSIFIED, rolled back.**
   `AvcLowLatencyDecoder.kt` was changed to request `KEY_LOW_LATENCY`
   unconditionally instead of gating on the decoder's own
   `FEATURE_LowLatency` self-report (which reports unsupported on
   `c2.realtek.video.avc.decoder`). Real gradle build passed, installed on
   device. Runtime result: the flag flipped true and per-frame decode
   improved sharply — `max_codec_ms` 107 ms, the best of eight same-day
   sessions, with `spike_250_ms` at zero, the only session of the eight
   with none. But `max_output_gap_ms` was **385 ms, second worst of the
   eight**, and the user's own gameplay assessment ("trash") matched it.
   Reverted to the exact predecessor bytes (SHA-256
   `22038e355f85bb8330d900bae64c37db54c902d4affdef12be4810bb03271c07`,
   verified byte-exact); the first post-revert session reports
   `low_latency_enabled: false` and a 221 ms gap. **Do not retry the
   unconditional request without new evidence.** Records:
   `../evidence/C3_L2C_LOW_LATENCY_DECODE_FALSIFIED_2026-09-19.md`,
   `../patches/C3-L2C_LOW_LATENCY_DECODE_ENABLE.md`.

2. **`C3.L3` — Linux fixed-bitrate characterization. Ported, installed,
   runtime validated, CLOSED.**
   The existing probe scripts (`tools/probe_c3_fixed_{5000,5500,6000}_characterization.py`)
   called a Windows-only implementation (`companion/diagnostics/c3_fixed_bitrate_probe.py`,
   built around WGC replacement capture — `hwnd`, `_wgc_bridge_path()`) that
   fails immediately on Linux. Ported by reusing the validated `C3.L1`/
   `C3.L1R1` Linux encoder-only restart primitive instead of building
   something new: `run_c3_linux_fixed_bitrate_cycle()`, added to
   `companion/diagnostics/c3_linux_actuator_probe.py`, restarts the single
   x11grab/VAAPI ffmpeg process at a caller-chosen bitrate via
   `_build_linux_ffmpeg_command`'s pre-existing (but previously unused)
   `bitrate_kbps`/`max_bitrate_kbps` override parameters. `native_stream.py`'s
   three `diagnostic_c3_fixed_bitrate_*_cycle` methods now dispatch
   Linux/Windows the same way `diagnostic_c3_actuator_continuity_cycle`
   already did. The Windows implementation was not touched. Record:
   `../patches/C3-L3_LINUX_FIXED_BITRATE_PORT.md`.

   Runtime result after three full characterization runs (ten clean
   trigger/finalize cycles, zero cycle-level FEC/audio/controller errors
   throughout): `decoder_max_output_gap_ms` ranged **291-331 ms at 6000 kbps
   (tightest, 40 ms band)**, 242-367 ms at 5000 kbps, and 219-584 ms at
   5500 kbps (widest, one severe unexplained outlier). Full data:
   `../evidence/C3_L3_LINUX_FIXED_BITRATE_CHARACTERIZATION_2026-09-19.md`.
   **This does not authorize automatic in-session adaptation** — that is
   `C3.L4`, gated on a focused gameplay acceptance that nothing on
   2026-09-19 performed.

3. **`C3-L3R1` — memory correction.** The `C3.L3` evidence file, `CURRENT.md`
   and `docs/KNOWN_ISSUES.md` were written before the 6000 kbps rerun was
   read back, and declared that result invalid and still owing. It was not:
   the rerun was already on disk and valid. Corrected, with the three-run
   reading re-derived. `C3.L2c`'s result was also promoted from its install
   record into an evidence record. Record:
   `../patches/C3-L3R1_CHARACTERIZATION_CORRECTION.md`.

## Issues found, not yet resolved

- **Probe-script finalize matched the wrong decoder-session file once.**
  On the run-3 first attempt, `tools/probe_c3_fixed_6000_characterization.py
  --finalize` — run immediately after `..._5500_... --finalize` — returned a
  result byte-identical to the 5500 kbps run and matched that run's
  decoder-session file. That attempt was discarded. The 6000 kbps **rerun
  matched correctly**: `c3_fixed_6000_characterization.json` records
  `payload.decoder_session_log = .../native_decoder_20260919_060325_369.json`,
  a distinct 64,840 ms session. So the defect is intermittent, not a
  guaranteed failure of back-to-back finalizes. Root cause not found.
  Affects `tools/probe_c3_fixed_*_characterization.py` only, not the `C3.L3`
  companion code. Logged in `../../KNOWN_ISSUES.md`
  (`PRIVYHUB_C3_L3_FINALIZE_MATCH_BUG`). **Check
  `payload.decoder_session_log` and `session_duration_ms` against the
  intended session before trusting any finalize result.**

- **File-bridge writes to `docs/memory/*.md` lagged behind their own commits
  on 2026-09-19.** Several times, a file that was just written and confirmed
  "written" read back as an older version. Retrying after a delay, and
  writing files in isolated single-file commits rather than rapid
  back-to-back batches, got the correct content to stick every time. Never
  affected code files or single-write new files. **If a new session sees
  `docs/memory/` content that looks stale relative to this handoff,
  re-stage the file rather than assuming the repo regressed** — check the
  raw file directly before trusting a summary of it, per standing practice.

## Standing workflow rules added 2026-09-19 (now in `../AGENTS.md`)

- Every response that asks the user to run something includes the exact
  command(s), inline, always — not a description of what to run.
- Diagnostic/probe output a script already persists to a file (`logs/`,
  `docs/memory/evidence/`) is read directly from the repository through
  the file bridge, not requested as a paste.
- Patch tiering and the execution budget: see `../AGENTS.md` and
  `../patches/PATCH_PROTOCOL.md`. Tier 1 is the default; the 2026-09-18
  patch records are **not** the model for validation effort.

## Next work item

**`C3.L3a` — gameplay acceptance probe.** REGISTERED / NEXT, design not yet
authorized. Ask for the design as a short plan first, no code; Tier 1 when
built. Scope: `../investigations/ACTIVE.md`.

`C3.L3a` is the `C3.L4` gate made performable — diagnostic-only, authorizes
nothing, reuses the validated `run_c3_linux_fixed_bitrate_cycle` as-is.
Required shape: several transitions in one session, at intervals the player
does not know in advance, at least one no-op control interval, marks compared
against `stream_discontinuities` `elapsed_ms` **after** the session, and time
parked at 5000/5500 kbps to judge the picture.

**`C3.L4` is not unblocked and cannot be unblocked by data.** Two things that
do *not* satisfy the gate, both proposed in good faith before: a manual cycle
with a subjective read (performed 2026-09-18, ruled insufficient by `C3.L2`
reason 3), and transport/decoder timing at any sample size (`C3.L2c` is the
proof — best `max_codec_ms` of eight sessions, verdict "trash"). Full
definition: `../decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`, section
"The `C3.L4` gate, stated so it can be satisfied".

---

# Superseded — 2026-09-18 handoff

Compressed 2026-09-19 to keep this file inside its size budget; `AGENTS.md`
defines the handoff as a small transfer note. Nothing is lost — that day's
state is recorded in full in `../2026-09-18.md` and in
`../evidence/C3_L2A_E2_ACTUATOR_IDR_RESOLVED_2026-09-18.md`.

Summary: C1/C2 complete on Linux; `C3.L0`, `C3.L1`, `C3.L1R1` complete;
`C3.L2` classified Linux `video_only_restart`; `C3.L2a` ANSWERED the same day
(27 ms actuator IDR against 195/210 ms for ordinary resyncs, so 287-318 ms was
not actuator cost); `C3.L2b` installed and runtime validated. `C3.L2c` was
registered but unauthorized then, and has since been authorized, installed,
falsified and rolled back — see above.
