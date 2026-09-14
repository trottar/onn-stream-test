---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 0c31c100ec721d687aff6aedbd79bc0cf9343810
---

# System Architecture

PrivyHub is intentionally modular, local-first, and capability-driven.

## Core roles

Current/future role boundaries:

- Android TV / portable clients: UI, media presentation, native video/audio
  receive, controller capture/transmit.
- Companion / future Linux hub: control API, source/provider orchestration,
  emulator lifecycle, native capture/encode/audio/input bridge, diagnostics,
  session policy and future remote-overlay integration.
- Home Opal: PrivyHub network/trust boundary.
- Ordinary household network: upstream connectivity only; not the PrivyHub
  trust domain.
- Persistent user content: media, ROMs, saves, states, cheat/mod profiles and
  runtime state remain separate from source.
- Future travel router: portable trusted client LAN and remote-uplink adapter;
  not itself an authorization credential.

Older split-network Prototype-1 evidence remains historical. The product
architecture does not place trusted PrivyHub server infrastructure on the
ordinary household-LAN side of the Opal boundary.

## Security layering

Future remote operation has two separate security layers:

1. secure network transport/overlay;
2. PrivyHub application identity, authentication and authorization.

Overlay membership or physical possession of a travel router must not grant
unrestricted application authority.

The local PrivyHub policy/permission layer remains authoritative.

## Evolution rule

Preserve proven behavioral contracts while replacing platform-specific
implementations.

The Windows companion may be replaced by Linux-capable server hardware and
additional inexpensive clients without changing user/session semantics merely
because the platform changes.

Generalize proven infrastructure when the phase calls for it; do not prematurely
force all sources into a single implementation.

Phase C is deliberately designed with future Phase G remote reuse in mind, but
Phase C does not implement WAN overlays, travel-router handling or remote
authentication.
