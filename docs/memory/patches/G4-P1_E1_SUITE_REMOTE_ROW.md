---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 3107fb5 (plus the uncommitted work of 10-15 / 10-16)
durable_memory_updated: true
---

# G4-P1: the suite's off-site row (`tools/e1_suite.py run --remote`)

## Purpose

A PS1-STREAM row against a client reached over the overlay, for G4-S1.
Record: `evidence/G4_P1_OFFSITE_TEST_PREP_2026-10-16.md`.

## Change

- **`tools/e1_suite.py`** (predecessor `602d7696…`, with session A's CL-B2
  line): one guarded dispatch at the top of `main()`. **Without `--remote`,
  today's suite.**
- **New `tools/e1_remote.py`:**
  - the preflight (both host flags read back);
  - waiting for the user's launch;
  - the endpoint class and its hash from the control port's peers (never
    the address);
  - `path.jsonl` every 10 s;
  - adb optional; the home row's figures.
- **New `tools/test_e1_remote.py`** (13 tests).

## Validation

`python3 -m unittest tools/test_e1_remote.py -v` → 13 / 13. No live run:
the blockers (CL-B2's pairing, the overlay flag) come first.

## Rollback

Do not pass `--remote`.
