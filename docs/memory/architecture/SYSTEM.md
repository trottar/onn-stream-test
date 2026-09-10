---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# System Architecture

PrivyHub is intentionally modular and local-first.

Current Prototype 1 roles:

- Android TV client: user interface, local TV/media presentation, native video/audio receive, controller capture/transmit.
- Windows companion: control API, media/source orchestration, Games plugin, emulator lifecycle, native capture/encode/audio/controller bridge, diagnostics.
- Isolated network boundary: untrusted/IoT client devices live on a secondary network; trusted host infrastructure remains on the trusted/home side with explicitly routed service access.
- Persistent user content: media, ROMs, saves, states, cheat/mod profiles, and runtime state are kept separate from source.

Long-term architecture should preserve these role boundaries while allowing the Windows companion to be replaced by Linux-capable server hardware and additional cheap clients.

Key principle: generalize proven infrastructure when the phase calls for it; do not prematurely force all sources into a single implementation.
