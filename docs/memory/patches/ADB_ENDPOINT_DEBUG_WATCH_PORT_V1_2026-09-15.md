---
memory_schema: 1
as_of: 2026-09-15
status: development-only
runtime_validation: pending
---

# ADB endpoint debug watch-port v1

Adds targeted scan observability to `tools/probe_adb_wireless_recovery.py`.

New local-only option:

`--debug-watch-port <1-65535>`

The option implies endpoint debug and emits markers for:
- configured watch port;
- in-range vs outside-range status;
- scheduling batch containing that port;
- TCP result OPEN vs CLOSED/UNREACHABLE;
- abnormal non-completion if scan termination occurs first.

The ordinary shareable probe log remains redacted. This patch does not alter the
production onn installer or recovery policy.
