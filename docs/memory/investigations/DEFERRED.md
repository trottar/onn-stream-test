---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Deferred Investigations

## UDP transport pathology

Severe burst/gap timing transformation and duplication was observed in both directions in the Prototype 1 environment. Application-level sender/capture evidence and Android-local loopback did not support blaming the normal production application path. Preserve the diagnostics and replay them on representative Linux/network infrastructure in Phase D unless a real blocker appears earlier.

## Game Session banner latency

A multi-second appearance delay was observed during prior testing. It is UI-lifecycle polish, not a current blocker. Do not perturb stable session/audio/controller lifecycle without a dedicated latency diagnostic.

## BPS/UPS/XDelta mod specifics

Supported through the current path but not individually promoted into new investigations unless an actual mod/runtime failure is observed.

## Full clean-machine Windows bootstrap

Current runtime includes ignored/local dependencies. Defer comprehensive reproducibility work to the clean-baseline/Linux portability phases unless fresh-machine testing becomes necessary sooner.
