---
memory_schema: 1
as_of: 2026-09-16
patch: D-096R3_PROBE_LISTENER_LIFECYCLE
durable_memory_updated: true
---

# D-096R3 listener/process lifecycle classifier

Production code changed:
none.

Probe changed:
`tools/probes/d096_storage_boundary_probe.py`

Corrections:
- lifecycle waits for absence of LISTEN sockets on 8765 and 8000;
- lifecycle also requires no matching PrivyHub process;
- raw TCP bindability is no longer used as the lifecycle criterion;
- exact confirmed-classification equality controls exit code;
- `D096_STORAGE_BOUNDARY_NOT_CONFIRMED` now returns nonzero.

Evidence:
direct diagnostic found no PrivyHub processes, no listeners, and no port owners
after the prior probe.
