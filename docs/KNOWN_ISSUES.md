# Known issues and deferred work

Status as of 2026-09-11.

| Issue | Status | Blocks current Phase C work? | Resume / resolve when |
| --- | --- | --- | --- |
| Bidirectional UDP burst/gap distortion and duplication in the current test path | Deferred after deep isolation | No | Replay after representative Linux baseline; reopen earlier only if blocking |
| Native streaming host is Windows-specific | Expected prototype limitation | No | Phase E Linux migration |
| NES runtime coverage | No local A9 fixture | No | Representative NES fixture is available |
| Genesis runtime coverage | No local A9 fixture | No | Representative Genesis fixture is available |
| Android cleartext/exported diagnostics and companion network exposure without mature auth | Security/privacy debt | No for isolated prototype | Dedicated threat-model/auth/encryption/privacy work |
| WGC/FFmpeg/process-audio bootstrap is not fully portable | Portability debt | No | Phase E / clean-machine reproducibility work |
| Conventional automated CI is minimal | Engineering debt | No | Before productization / broader platform expansion |
| Large orchestration files | Maintainability debt | No | Dedicated refactor with its own validation objective |
| Remaining Live TV / EPG / guide polish | Planned product work | No | Phase D |
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

Preserve the diagnostics. After Phase E establishes the representative native
Linux baseline, replay the acceptance suite during Phase F Linux
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

Phase E owns Linux functional parity. Phase F owns representative Linux
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
