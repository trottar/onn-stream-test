---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 92e388e
durable_memory_updated: true
---

# G8-P1: the impairment shim, behind `PRIVYHUB_IMPAIRMENT=<profile>`

## Purpose

A user-space network-impairment shim on the loopback media hop, so ROADMAP
§G8's adverse-network characterization can run without `nft` or `sudo`.
Record: `evidence/G8_P1_IMPAIRMENT_SHIM_2026-10-16.md`.

## Change

- **New** `companion/impairment.py`:
  - the profile table and the parser:
    `<name>[+<name>…][@pre-fec|@post-fec][,seed=N]`;
  - `Impairer`, pure, on a given clock. Its stages are burst, loss,
    reorder, delay + jitter (FIFO), and a cap with a bounded queue;
  - `Shim`, the loopback relay thread, which writes one line per second to
    `logs/impairment.jsonl`;
  - `RelayShim`, the FEC sender's side: where to bind and where to send.
- **`companion/native_fec_relay.py`** (predecessor and after in
  `evidence/g8_p1_2026-10-16/predecessor_sha256.txt` / `after_sha256.txt`).
  Every hook is inert while `_impairment` is `None`:
  - a module-level guarded import;
  - in `start()`, the shim built from the environment, the bind port and
    the send target taken from it, and the shim attached after the bind;
  - in `stop()`, the shim stopped.

  `native_stream.py` is **unchanged**: in the pre-FEC placement the shim
  takes the sender's port, so the encoder command is the same with or
  without the flag.
- **New tests:** `tests/impairment/test_impairment.py` (13).

## Validation

- `python3 -m unittest discover -s tests/impairment` → 13 OK.
- `evidence/g8_p1_2026-10-16/proof.py`:
  - A: each profile, 60 s, against its tolerance;
  - B: the real FEC sender in both placements;
  - C: flag absent — one masked encoder hash, the FEC sender byte for byte
    against HEAD, and a fresh process binding its own port with no shim.

  The results are in the record.

## Result

BUILT behind the flag; the envelope NOT MEASURED; NOT ADOPTED; nothing
committed. `PATCH_INDEX.md` not updated (not session B's file).
