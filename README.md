# PrivyHub

PrivyHub is an experimental, local-first media and smart-home platform built around an isolated IoT network. The current prototype uses an onn Android TV device as the first client and a Windows companion host as the temporary server/streaming platform. A later project phase will move host/server responsibilities toward dedicated Linux infrastructure.

## Current prototype

The project currently includes:

- local media/VOD serving;
- camera and browser/live sources;
- a mature local TV/IPTV catalog and EPG stack;
- NES, SNES, Genesis, and PlayStation emulation through a project-managed RetroArch runtime;
- native low-latency game video, audio, and controller transport experiments;
- diagnostic tooling for measuring UDP behavior across the host, isolated network, and Android client.

The native game-streaming baseline is intentionally conservative while transport behavior is being characterized. Video and input are viable. Process-specific audio capture is viable, but the current Windows/USB-Wi-Fi/household-network/GL-iNet/onn test environment exhibits severe UDP burst/gap timing distortion and packet duplication outside the application layer. That infrastructure investigation is **deferred until the dedicated Linux infrastructure phase** rather than being masked by production buffering changes.

## Documentation

Start with:

- [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) — current architecture, stable baselines, and roadmap;
- [`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md) — deferred issues and technical debt;
- [`docs/investigations/2026-09-07-udp-transport.md`](docs/investigations/2026-09-07-udp-transport.md) — complete UDP transport investigation and evidence;
- [`docs/DIAGNOSTICS.md`](docs/DIAGNOSTICS.md) — reusable transport diagnostics and Linux acceptance tests;
- [`docs/REPOSITORY_AUDIT_2026-09-07.md`](docs/REPOSITORY_AUDIT_2026-09-07.md) — repository/reproducibility audit before the next checkpoint push.

## Network ports used by the current prototype

| Purpose | Port |
| --- | ---: |
| Companion control API | TCP 8765 |
| Media serving | TCP 8000 |
| Native game video | UDP 48100 |
| Native game audio | UDP 48101 |
| Native controller input | UDP 48102 |
| Local video FEC relay input | UDP 48110 on loopback only |
| Forward synthetic transport diagnostic | UDP 48120 |
| Android-local loopback diagnostic | UDP 48121 |

Diagnostic ports and implementation details may evolve; production code should not depend on diagnostic-only paths.

## Project principles

- Local-first and privacy-oriented operation.
- IoT devices isolated behind a dedicated network boundary.
- Prefer modular components and replaceable infrastructure.
- Preserve known-good baselines while testing one layer at a time.
- Do not broaden capture from the managed game window to the desktop as a fallback.
- Do not treat temporary test-environment behavior as a product requirement without reproducing it on representative infrastructure.
