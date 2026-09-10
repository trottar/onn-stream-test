---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Closed Investigations

## A4 audio/host lifecycle

Runtime validated: TV game audio works, local duplicate audio is suppressed, controlled shutdown restores session state, and plugin shutdown reuses the normal Games stop path. Do not reopen absent regression evidence.

## A8 mapping assignment boundary

Resolved: physical controller semantics remain canonical through PHI1/ViGEm; A8 session mapping applies later in RetroArch bindings. Controller preflight ordering was corrected so XInput devices exist before RetroArch initializes.

## A6 artwork transient

A temporary cover-art disappearance after repeated APK reinstall activity repopulated without persistent regression. Do not touch artwork unless repeatable in normal launches.

## Cheat/mod isolation

Resolved and runtime validated: normal save/state namespaces are protected; cheat/mod profiles use isolated namespaces; deterministic IPS derived content is verified.
