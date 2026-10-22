# B1b — the bench's `@both` gate drops the client's desync too: design (hashed before any B1b code)

Queue `handoffs/QUEUE_2026-10-22C.md` item B1b, session B. Predecessors: `plugins/games.py` (B6 + B7 in the tree),
`impairment.py` and `tests/impairment/test_blackout.py` (HEAD).

## 1. Today (B1 §1, from the code)

B1's uplink gate (`impairment.UplinkGate`, the shared schedule) drops, while dark, at three receive points:
- `controller`: every datagram on the controller socket, before parsing. **So B7's stall datagrams (same socket) are
  already dropped**, counted as `controller`.
- `heartbeat`: the plugin's `native-stream-heartbeat`.
- `client_health`: the service's `/diagnostics/client-health`.

Everything else passes, among it the client's **`native-stream-desync`**. In BENCH-R1 cells 5-6 that let v2's
`client_output_silence` pause land 1.4-1.7 s into each 4-s dark span, which no real bidirectional drop allows.

## 2. The change

**One guarded statement**, B1's form, at the top of the plugin's `native-stream-desync` branch:
`if _impairment_uplink is not None and _impairment_uplink.drop("desync"): return {…, "ok": False, "impairment":
"uplink_blackout"}`.
- The gate counts it by kind (`desync`; the counter dict takes new kinds already). `uplink_dropped` in status shows
  it.
- The gate exists only for `blackout-<D>s@both` (`@down` and every other profile have no uplink gate). **Absent = today
  byte for byte:** the guard's name is `None`.

**What the client does with a dropped desync, from its code:** the POST fails, and `desyncPostedForEpisode` stays set,
so it is **not retried** in that episode. The client stays in its gate and posts `native-stream-ready` when its gate
passes after the return. That is what a request lost in a real drop does: the host never hears this episode's desync.
- A real drop over TCP could instead **deliver it late**, by retransmission within the client's timeouts. The bench
  models the loss, the queue's ask. Stated.

## 3. What still passes while dark, and why

| request | passes | why |
| --- | --- | --- |
| `native-stream-start` / `native-stream-stop` | yes | the suite's own session control (the queue: may pass); dropping them breaks the cell's lifecycle, not the link |
| `native-stream-ready` | yes | the client sends it only after its gate saw ≥ 3 clean 500-ms ticks of frames. Under `@both` the frames are dark, so a ready can only be in flight at a span's edge. **A dropped ready is terminal for the client's session** (`failStabilization`: "Release failed — game remains paused"), so gating it would end the cell rather than model the link |
| the decoder report (`decoder-session-log`, at stop) | yes | sent at the session's end, the suite's record |
| UI / suite actions (launch, status, save-state, …) | yes | not the stream client's uplink |
| controller datagrams, **stall datagrams (B7)**, heartbeat, client-health, **desync** | **no** | the client's stream-time uplink |

## 4. Proof (as B1's, in process; `proof.py`)

1. The gate: `desync` dropped inside a dark span and passed outside, counted.
2. **The plugin's real `handle_post_request`** (a stub `self` with a fake recovery):
   - a desync POST inside a dark span returns `impairment: uplink_blackout` and the recovery is not called;
   - outside, it is accepted and `note_client_desync` is called;
   - with the gate `None`, today's path.
3. A stall datagram through the real receive loop is dropped while dark (counted `controller`).
4. The AST: `handle_post_request` with B1b's guarded statement removed = the predecessor's. A `@down` profile has no
   gate.
5. B1's tests:
   - `Hooks.test_guarded_imports_and_hook_shape` pins "one hook" in `plugins/games.py`. **It is updated to expect the
     two kinds (heartbeat, desync), the one change to an existing test, disclosed.**
   - Everything else in `tests/impairment` stays unchanged and green.
