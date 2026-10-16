---
memory_schema: 1
as_of: 2026-10-15
baseline_commit: 3107fb5
durable_memory_updated: true
---

# G1-S1: the overlay provider boundary (behind `PRIVYHUB_OVERLAY_PROVIDER`)

## Purpose

ROADMAP §G1: a provider boundary instead of one overlay product hard-coded
into the session architecture. Record:
`evidence/G1_S1_TRUST_TOPOLOGY_AND_OVERLAY_PROVIDER_2026-10-15.md`.

## Change

- **New** `companion/overlay/` (`provider.py`, `none.py`, `tailscale.py`,
  `__init__.py`, `__main__.py`): the contract, the `none` provider (default),
  the read-only `tailscale` provider (binary only if present), selection by
  `PRIVYHUB_OVERLAY_PROVIDER=none|tailscale`, the status reporter (one log
  line per change), `python3 -m companion.overlay --state`.
- **`companion/privyhub_service.py`** (predecessor `27d31b58…5fbc`):
  `OVERLAY_STATUS` built only when the flag is non-empty (the import is inside
  that `if`); `PrivyHubController.status()` adds `overlay` after the lock when
  it is set. **Flag absent = today, byte for byte.**
- **New** `tests/overlay/` (17 tests, fixtures, the predecessor `status()`
  golden).

## Validation

`python3 -m unittest discover -s tests/overlay -v` → 17 OK
(`evidence/g1_s1_2026-10-15/tests_output.txt`), including the status
document byte-for-byte with the flag absent. No companion restart; the live
smoke is pending on the stream (session A). Not adopted.

## Rollback

Remove the drop-in that sets `PRIVYHUB_OVERLAY_PROVIDER` (none exists today).
The code itself is inert without it.
