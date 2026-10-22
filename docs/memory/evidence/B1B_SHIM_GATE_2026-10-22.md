---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 144e5c7 (+ B5-B7 in the tree, uncommitted; B1b's predecessor for plugins/games.py is B7's)
---

# B1b — the bench's `@both` gate now drops the client's desync too (the bench blackout is the real one)

**Classification: BUILT** (one guarded statement); **the proof ALL MET** (in process, as B1's).
- B1's suite is 29 OK, with one hook-shape test updated (disclosed).
- Flag absent = today byte for byte: the plugin module, minus B1b's guard, is AST-identical to its predecessor.
- **Not used by any run yet; nothing committed.**

Design `b1b_2026-10-22/design_written_before_code.md`, sha256 `87ab09a4…aca5`, hashed **06:00:23Z, before the code**.

## 1. What changed

- **The client's `native-stream-desync` is dropped while a `blackout-<D>s@both` span is dark.**
  - It is one guarded statement at the top of the plugin's desync branch (B1's form). The gate counts `desync` by
    kind, in `uplink_dropped`.
  - `@down` and every other profile have no uplink gate, so the desync passes. Cell 7 keeps its client desync.
- **What the client does with it, from its code:** the POST fails, and `desyncPostedForEpisode` stays set, so it is
  not retried. The host never hears that episode's desync, and the client posts its ready after its gate passes.
  - A real drop over TCP might instead deliver it late, by retransmission. The bench models the loss. Stated.
- **B7's stall datagrams were already dropped** by B1's controller-socket gate, before parsing. Proof §3: 270 dropped
  as `controller`, 0 parsed.

## 2. What still passes while dark, and why

| request | passes | why |
| --- | --- | --- |
| `native-stream-start` / `-stop` | yes | the suite's session control (the queue allows it) |
| `native-stream-ready` | yes | the client sends it only after ≥ 3 clean 500-ms ticks of frames, and under `@both` the frames are dark, so it can only be in flight at a span's edge. **A dropped ready is terminal for the client's session** (`failStabilization`), which would end the cell, not model the link |
| `decoder-session-log` (the report at stop) | yes | the suite's record at the session's end |
| UI / suite actions | yes | not the stream client's uplink |
| controller + stall datagrams, heartbeat, client-health, **desync** | **dropped** | the client's stream-time uplink |

## 3. Proof (`proof.py` → `proof.json` / `proof.md`, `proof_console.txt`; run on the copy and on the tree): ALL MET

1. **The gate:** `desync` dropped at 10.1 / 13.9 / 130.5 s (dark), passed at 9.9 / 14.1 s; counted 3.
2. **The plugin's real `handle_post_request`** (a stub `self`, a fake recovery):
   - dark: `impairment: uplink_blackout`, and the recovery is not called;
   - outside: accepted, and `note_client_desync("output_silence", 1200)` is called;
   - no gate: today.
3. **A stall datagram through the real receive loop while dark:** 0 parsed, 270 dropped (`controller`).
4. **AST:** one B1b guard; the module without it is identical to the predecessor; `@down` has no gate.

**The tests:**
- `tests/impairment` 29 OK.
- `Hooks.test_guarded_imports_and_hook_shape` pinned "one hook" in `plugins/games.py`. **It now expects the two kinds
  (`heartbeat`, `desync`)**, B1b's only change to an existing test.
- Also OK: stall_signal 12, input_hold 19, input_hold_b6 16, input_hold_rewind 22.

## 4. What it changes for BENCH-R2

**Every `@both` cell now has no desync during the dark span.** Without the hold, a 4-s blackout then runs:
- the core on, for the full 4 s;
- v2's controller-silence pause, if v2 is on: at 5 s + confirmation, i.e. after the return; otherwise
  `DESYNC_MS = 1 s` of silence;
- then the client's ready after its gate.

**The ready arrives while `PLAYING` in some paths. Today it is read as a `session_started` and resets the ladder.**
B6's R3 and B7's guard cover the hold's and the stall's own resumes. Without them, BENCH-R2 will see it: a finding to
expect, not a bench fault. **Cell 5's 85-frame figure will rise toward the raw ~234.**

## 5. Files

- **`b1b_2026-10-22/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/`, `predecessor_sha256.txt`, `after_sha256.txt`;
  - `design_written_before_code.md`, `design.sha256`, `design_hashed_at.txt`;
  - `b1b.diff`;
  - `proof.py`, `proof.json`, `proof.md`, `proof_console.txt`;
  - `tests_impairment.txt`;
  - `redact_check.py`, `redact_check.txt`, `manifest.sha256`.
- **Elsewhere:** `companion/plugins/games.py` (+3), `tests/impairment/test_blackout.py` (the hook-shape test);
  `patches/B1B_SHIM_GATE.md`; `logs/b1b_git_status.txt`.
