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

- **`_patches/` and `_probes/` are not covered by `.gitignore`.** The existing
  patterns are `privyhub_*/` and `privyhub_*_v*.zip`. The local probe
  directories are named `PrivyHub_*`, which does not match on a case-sensitive
  filesystem. These directories are development-only and must not be pushed.
  Status: open. Confirm with `git status --short` before any commit. Do not fix
  this inside unrelated streaming work.

- **Existing C3 probes cannot run on Linux.**
  `companion/diagnostics/c3_actuator_probe.py` and
  `companion/diagnostics/c3_fixed_bitrate_probe.py` require `_wgc_ready()`, an
  HWND capture target and `_build_ffmpeg_command`, and fail closed with
  `wgc_runtime_unavailable` before modifying anything. They are correct as
  written. Status: expected prototype limitation; resolved by the `C3.L1` Linux
  cycle implementation.
<!-- PRIVYHUB_C3_L0_AUDIT:KNOWN_ISSUES:END -->

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
