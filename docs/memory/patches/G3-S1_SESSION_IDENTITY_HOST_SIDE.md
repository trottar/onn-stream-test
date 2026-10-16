---
memory_schema: 1
as_of: 2026-10-15
baseline_commit: 3107fb5 (plus G1-S1)
durable_memory_updated: true
---

# G3-S1: session identity and authorization, host side (behind `PRIVYHUB_SESSION_IDENTITY=v2`)

## Purpose

ROADMAP §G3: client identity, session identity, declared endpoints and
fail-closed, auditable authorization, so the source address stops being
identity. Record: `evidence/G3_S1_SESSION_IDENTITY_HOST_SIDE_2026-10-15.md`
(the design is its §1, written before the code).

## Change

- **New** `companion/session_identity.py`: routing classes, the pairing
  window and the device store (`~/.config/privyhub/paired_devices.json`,
  0600), nonce + HMAC-SHA256 setup, expiring tokens, declared endpoints,
  per-device permissions, the legacy LAN path, `logs/session_audit.jsonl`
  (no address).
- **`companion/privyhub_service.py`** (predecessor `79041797…`, G1-S1's
  state): five edits, each guarded by `SESSION_IDENTITY is not None`. They
  build the gate under the flag, run `intercept` in `do_GET` / `do_POST`,
  add the session header in `_send_json`, and pass the declared target at
  the two plugin calls. **Flag absent = today, byte for byte.**
- **New** `tests/session_identity/` (38 tests and the baseline handler
  golden).

## Validation

`python3 -m unittest discover -s tests/session_identity -v` → 38 OK. The
in-process handler replay is byte for byte with the flag absent (14 / 14),
and a mutation check shows the comparison catches changes. The overlay
tests re-ran: 17 OK. The redactor passes on the audit sample. The live
smoke and the D6-R1 UDP runs are pending on the stream. Not adopted.

## Rollback

There is no drop-in setting the flag. The code is inert without it.
