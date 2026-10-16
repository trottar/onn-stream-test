---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 3107fb5 (plus the uncommitted G1-S1 / G3-S1 / G3-S2 / CL-B2 work)
durable_memory_updated: true
---

# G5-S1: WAN telemetry classification (behind `PRIVYHUB_WAN_TELEMETRY=1`)

## Purpose

ROADMAP §G5's eleven measures from Phase C's existing telemetry, plus the
overlay path, classified per 10-s window and per session, with thresholds
from existing records. Record:
`evidence/G5_S1_WAN_TELEMETRY_CLASSIFICATION_2026-10-16.md`.

## Change

- **New** `companion/wan_telemetry.py`. It classifies only; it never acts.
- **`companion/privyhub_service.py`** (predecessor `32a7d2ea…`): four
  guarded edits:
  - the import / construction;
  - `observe` in the client-health handler;
  - `wan` on `/diagnostics/stream-telemetry`;
  - `wan` on `/status`, through a guarded wrapper around `CONTROLLER.status`.

  **Flag absent = today, byte for byte.**
- **New** `docs/WAN_ADAPTATION_RULES.md` (rules, not implemented) and
  `tests/wan_telemetry/` (18 tests, three redacted run fixtures, two
  goldens).

## Validation

- `python3 -m unittest discover -s tests/wan_telemetry -v` → 18 OK. The
  replays reproduce the recorded loss: 649.94, 60.93 and 663.98 / min.
- The G1-S1 (17) and G3-S1 (38) suites still pass.
- The live smoke is pending on the stream. Not adopted.

## Rollback

There is no drop-in setting the flag; the code is inert without it.
