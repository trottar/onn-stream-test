# Known issues and deferred work

<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:KNOWN_ISSUES:BEGIN -->
## 2026-09-16 current issue override

Current Phase-D blocker:
- **PS1 multiplayer / multitap parity on Linux** — active. Windows Phase A proved
  the intended Port-1 multitap behavior; Linux currently fails to reproduce it.
  Exact boundary is not yet classified.

Resolved/superseded:
- broad "Linux controller input is broken" — resolved for the tested paths by
  D-084/D-085 and runtime validated across three games / three input profiles;
- "native Games streaming host is Windows-specific" — superseded for Games by
  the current Linux X11/VAAPI/PulseAudio/uinput runtime.

Do not reopen the lower controller transport or D-pad mapping while debugging
multitap unless a fresh diagnostic contradicts the D-085 runtime acceptance.
<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:KNOWN_ISSUES:END -->

<!-- PRIVYHUB_C3_L0_AUDIT:KNOWN_ISSUES:BEGIN -->
## 2026-09-18 C3.L0 audit findings

Added by the `C3.L0` Linux actuator boundary audit. Neither item is fixed by
that work.

- **Linux host resource telemetry never starts.**
  `NativeStreamManager._host_telemetry.start()` is called only inside the
  Windows start path, gated on `_capture_process is not None`.
  `_start_linux_locked` never calls it, while `status()` still publishes a
  `host_telemetry` section, so the field reports an inactive profiler on every
  Linux session. The C2 telemetry contract is unaffected because its sender
  metrics come from the FEC relay `sendto()` boundary, which does run on Linux.
  Status: open, Phase E prerequisite. Does not block C3.

- **`_patches/` and `_probes/` are not covered by `.gitignore`.**
  Status: **RESOLVED 2026-09-18** by the STREAMLINE patch. `.gitignore` was
  deduplicated and now covers `_patches/`, `_probes/` and `Claude outputs/`
  explicitly, alongside the existing `privyhub_*` patterns. The directories
  themselves are left on disk; delete them when you want the space back.

- **Existing C3 probes cannot run on Linux.**
  `companion/diagnostics/c3_actuator_probe.py` and
  `companion/diagnostics/c3_fixed_bitrate_probe.py` require `_wgc_ready()`, an
  HWND capture target and `_build_ffmpeg_command`, and fail closed with
  `wgc_runtime_unavailable` before modifying anything. They are correct as
  written. Status: expected prototype limitation; resolved by the `C3.L1` Linux
  cycle implementation.
<!-- PRIVYHUB_C3_L0_AUDIT:KNOWN_ISSUES:END -->

<!-- PRIVYHUB_C3_L2A_E1:KNOWN_ISSUES:BEGIN -->
## 2026-09-18 C3.L2a E1 diagnostic retention findings

Found by the `C3.L2a` E1 evidence pass. Record:
`docs/memory/evidence/C3_L2A_E1_DECODER_EVIDENCE_PASS_2026-09-18.md`.

- **The decoder session report's slow-event list was a 128-entry ring that
  discarded the actuator cycle.** In the `C3.L1R1` session it held 128 of 128
  and covered only the last 29.4 s of a 64.8 s session, so the row explaining
  `max_output_gap_ms` 287 was already gone. Any session with more than 128
  slow events after a cycle lost the cycle's evidence. Status: **code fix
  installed 2026-09-18 by `C3.L2b`** (`docs/memory/patches/C3-L2B_DECODER_REPORT_CYCLE_RETENTION.md`)
  — segmented marked/recent retention plus `elapsed_ms`-anchored
  discontinuity and first-IDR-after-discontinuity lists. **Not yet
  runtime-confirmed**: no APK built with the real Android/Gradle toolchain has
  been installed on the onn device, and no actuator cycle has been run against
  it. `C3.L2a` itself stays open until that cycle runs and the new report
  fields are read. Diagnostic-only client work; no streaming constant changed.

- **The encoder swap is not visible in the native video host log tail.** The
  bundle carries the last 500 lines, which for the `C3.L1R1` session showed a
  single continuous frame counter with no restart banner while the receiver
  recorded one SSRC change. Status: open question for the probe source; either
  the replacement encoder does not write to that log or the swap fell outside
  the tail. Unaffected by `C3.L2b`.

- **Decoder time dominates the large output gaps on the onn client.**
  `output_gap_ms` tracks `codec_ms` one-to-one in ordinary play, reaching 238 ms
  with no actuator involved; 2,696 spikes at or above 20 ms against 3,847 queued
  frames; `low_latency_enabled` is false on `c2.realtek.video.avc.decoder`.
  Status: open, unattributed. Enabling low-latency decode is `C3.L2c`, a
  separate production-behavior candidate, registered but not scheduled and
  not authorized; it was not folded into `C3.L2b`.
<!-- PRIVYHUB_C3_L2A_E1:KNOWN_ISSUES:END -->

Status as of 2026-09-11.

| Issue | Status | Blocks current Phase C work? | Resume / resolve when |
| --- | --- | --- | --- |
| Bidirectional UDP burst/gap distortion and duplication in the current test path | Deferred after deep isolation | No | Replay after representative Linux baseline; reopen earlier only if blocking |
| Native streaming host is Windows-specific | Expected prototype limitation | No | Phase D Linux migration |
| NES runtime coverage | No local A9 fixture | No | Representative NES fixture is available |
| Genesis runtime coverage | No local A9 fixture | No | Representative Genesis fixture is available |
| Android cleartext/exported diagnostics and companion network exposure without mature auth | Security/privacy debt | No for isolated prototype | Dedicated threat-model/auth/encryption/privacy work |
| WGC/FFmpeg/process-audio bootstrap is not fully portable | Portability debt | No | Phase D / clean-machine reproducibility work |
| Conventional automated CI is minimal | Engineering debt | No | Before productization / broader platform expansion |
| Large orchestration files | Maintainability debt | No | Dedicated refactor with its own validation objective |
| Remaining Live TV / EPG / guide polish | Planned product work | No | Phase F |
| Game Session banner latency | Low-priority polish | No | Dedicated measured latency investigation if prioritized |

Resolved items such as the historical `companion/games/` ignore defect,
four-player support, manual PS1 multitap, and Sunshine/Moonlight production
integration are not open issues.

## UDP transport pathology

### Symptom

The Prototype 1 environment can transform nominally paced UDP traffic into large
arrival bursts/gaps and can produce duplicates. Synthetic probes reproduced the
behavior without normal production game load.

### Current conclusion

The dominant transformation is outside normal application pacing and was
observed in both directions through the current Windows/consumer-network test
environment.

The investigation does **not** establish which individual network component is
at fault. Possible causes remain endpoint Wi-Fi/driver/firmware behavior,
network-device behavior, offload/bridging/routing effects, RF scheduling, or an
interaction among those layers.

### Product decision

Do not encode this environment’s measured jitter/duplicate rate into product
buffering or transport architecture.

Preserve the diagnostics. After Phase D establishes the representative native
Linux baseline, replay the acceptance suite during Phase E Linux
resource/transport characterization unless the issue becomes a blocker sooner.

Full record: `investigations/2026-09-07-udp-transport.md`.

## Runtime coverage gaps: NES and Genesis

NES and Genesis are configured/supported, and earlier user testing indicated
normal behavior, but the final A9 evidence did not have local fixtures for those
families.

Current durable status is therefore:

- NES — **not runtime validated**;
- Genesis — **not runtime validated**.

Do not infer validation from configuration or from another emulator family.
Upgrade status only after a normal launch/input/lifecycle regression with a real
fixture.

## Security/privacy debt

The isolated prototype still has security surfaces that require a dedicated
hardening phase:

- Android cleartext networking;
- exported diagnostic/probe activities;
- companion network listening without mature authentication;
- normal service logging that may contain operational requester information.

These should be handled together with a threat model, authentication,
encryption, authorization and privacy review. Do not mix ad-hoc security changes
into unrelated C1 streaming work.

## Windows/Linux portability debt

The current native path intentionally uses Windows-specific components,
including WGC, NVENC/FFmpeg integration, process-loopback audio and ViGEm.

Phase D owns Linux functional parity. Phase E owns representative Linux
resource/transport characterization. The current Windows implementation remains
the validated behavior reference until those phases execute.

## Maintainability / test debt

Large central files remain:

- Android `MainActivity.kt`;
- companion `games/emulator_manager.py`;
- companion `plugins/games.py`.

Minimal conventional CI also remains. Existing deterministic probes and runtime
evidence are strong, but they are not a substitute for future automated
multi-platform coverage.

Refactor only with a dedicated objective and explicit regression boundary.

<!-- PRIVYHUB_C3_L2A_E2:KNOWN_ISSUES:BEGIN -->
## 2026-09-18 C3.L2b reporting defect

- **`slow_events_marked` is emitted as an empty array.**
  `slow_event_retained_marked` reports 30 of 64, so the marked window's rows are
  counted and then dropped rather than serialized. Found on the first runtime use
  of `C3.L2b`. It did not block `C3.L2a`, which was answered from
  `stream_discontinuities` and `first_idr_after_discontinuity`, but the marked
  window cannot yet be inspected row by row. Status: open, diagnostic-only.

- **Decoder time correlates with perceptible interruption on the onn client,
  but is not its mechanism.** `low_latency_enabled` is false on
  `c2.realtek.video.avc.decoder`; `max_codec_ms` 367; the two largest output
  gaps in the `C3.L2a` E2 session, 359 ms and 352 ms, tracked `codec_ms` to
  within 8 ms with feed delay at zero. `C3.L2c` then cut `max_codec_ms` to
  107 ms and `max_output_gap_ms` got **worse** (385 ms), which falsifies
  `max_codec_ms` as a proxy for the gap. Status: open, owner unassigned —
  `C3.L2c` is closed as falsified and is not the owner. Any future candidate
  justified by "it lowers decode time" must measure `max_output_gap_ms`
  directly before acceptance. Record:
  `docs/memory/evidence/C3_L2C_LOW_LATENCY_DECODE_FALSIFIED_2026-09-19.md`.
<!-- PRIVYHUB_C3_L2A_E2:KNOWN_ISSUES:END -->

<!-- PRIVYHUB_C3_L3_FINALIZE_MATCH_BUG:KNOWN_ISSUES:BEGIN -->
## 2026-09-19 C3.L3 characterization probe finalize bug

Found during `C3.L3` Linux fixed-bitrate characterization (third run).
Corrected 2026-09-19 by `C3-L3R1`: the original entry misidentified the
decoder-session file involved and implied the 6000 kbps result was
unrecoverable. Neither was right. The defect itself is real and stays open.

- **`--finalize` can match the wrong decoder-session file.**
  `tools/probe_c3_fixed_6000_characterization.py --finalize`, run
  immediately after `tools/probe_c3_fixed_5500_characterization.py
  --finalize` in the same sequence, returned measurements byte-identical to
  the 5500 kbps result (`session_duration_ms` 66,638, every
  decoder/controller count, `sequence_resyncs`, `ssrc_changes`) apart from
  `target_bitrate_kbps` itself, and was missing several audio fields the
  5500 result had. It had matched the 5500 kbps run's own decoder-session
  file, `logs/games/decoder_sessions/native_decoder_20260919_055703_163.json`.
  That attempt was discarded.

  **The defect is intermittent.** The 6000 kbps rerun taken the same
  session matched correctly:
  `logs/streaming/c3_fixed_6000_characterization.json` records
  `payload.decoder_session_log =
  logs/games/decoder_sessions/native_decoder_20260919_060325_369.json`, a
  distinct 64,840 ms session written 9.4 s before that finalize, whose
  figures differ from the 5500 kbps session in every field. So back-to-back
  finalizes do not fail deterministically, and the data that was thought
  lost was never lost.

  Not root-caused. Status: **open**. Affects
  `tools/probe_c3_fixed_*_characterization.py`'s decoder-session matching
  only — the `C3.L3` companion-side Linux cycle
  (`companion/diagnostics/c3_linux_actuator_probe.py`) is not implicated.

  **Workaround until fixed:** after any `--finalize`, check
  `payload.decoder_session_log` and `session_duration_ms` in the written
  JSON against the session you intended to measure, before using the
  result. A finalize that reports the previous bitrate's duration has
  matched the wrong file.

  Records: `docs/memory/evidence/C3_L3_LINUX_FIXED_BITRATE_CHARACTERIZATION_2026-09-19.md`,
  `docs/memory/patches/C3-L3R1_CHARACTERIZATION_CORRECTION.md`.
<!-- PRIVYHUB_C3_L3_FINALIZE_MATCH_BUG:KNOWN_ISSUES:END -->
