---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: efa4240
---

# B16 — the stall resume's speed and the saves, inside `PRIVYHUB_STALL_RESUME=1` (+ `PRIVYHUB_INPUT_HOLD_REWIND=1`)

**Result: SETTLED + BUILT; host 7 tests (`tests/stall_resume_speed`), client 3 JVM tests (125 / 125); host AST proof
(the plugin identical with B16's item removed), client textual proof (50 added lines, 0 changed); NOT ADOPTED; no live
run.** Record: `evidence/B16_STALL_RESUME_SPEED_2026-10-24.md`. Nothing committed.

- **Settled:**
  - `@down`: the client's ready is its recovery gate's release, on the 500-ms tick. It needs the IDR (≤ 250 ms), then a
    baseline tick and 3 clean ticks (≥ 45 fps over the tick), so ~2-3 s after the frames return. It is not the
    heartbeat, and not the audio cushion.
  - v2's 5-s hold expired first in all 5. Blackout 5's restart acted on a heartbeat built before the return.
  - `@both`: B8's resume waits for the next fresh heartbeat (2-s cadence), hence 2,130 ms.
  - The saves: B12 saved at every client stall ≥ 150 ms.
- **Built (client):** the host's start response `"stall_resume": {"fast_ready": true}` arms a 50-ms recovery-gate tick.
  It sends the ready at the first frame rendered since the recovery began, with the receiver not waiting for an IDR
  and the output ≤ 100 ms old.
- **Built (host):**
  - the key, only with B12's owner wired;
  - the resume on that ready, through B12's / B8's existing `ready_resume`;
  - the stall's save only at age ≥ the stall signal (400), synchronous before B7's pause;
  - v2 past its 5 s only while the newest stall datagram (≤ 300 ms) shows the client stalled.
- **Rows (tests):** a 4-s `@down` drop resumed 301 ms after the return with no restart and no handover; a 4-s `@both`
  drop 301 ms after the packets. Zero saves under 400 ms. Net 24 (the save at 400 ms).
- **Files:** `companion/stall_owner.py` (B12's module), `companion/plugins/games.py` +4, `FastReady.kt` (new),
  `NativeStreamActivity.kt` +50, `FastReadyTest.kt` (new), `tests/stall_resume_speed/` (new),
  `tests/stall_owner/test_stall_owner.py` (one line: B12's net 8-14 → 20-30).
- **Validation performed:** every `tests/` suite from the /tmp copy, the JVM suite offline, both proofs, the redact
  check.
- **Rollback:** unset `PRIVYHUB_STALL_RESUME` (the client then gets no key and runs today's gate). Or revert the files
  above.
