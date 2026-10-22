# B1 design — the shim's blackout, both directions (written before any code edit, hashed; session B, 2026-10-22)

**What it must reproduce** (`UX_R3_FIND_THE_DEATHS_2026-10-21.md`): 04:54:55-04:54:59Z, the link dead both ways for
3-4 s.
- The uplink: control gaps 967 / 350 / 342 / 546 / 442 ms, the heartbeat held.
- The downlink: output gaps 410 / 307 ms, audio arrival stopped 406 ms, 61 packets lost after FEC.
- The host saw nothing, and the game ran on.

## The flag and the grammar (`PRIVYHUB_IMPAIRMENT`, G8-P1's flag; absent = today)

```
blackout-<D>s@both[,every=<P>s][,first=<F>s][,seed=N]
blackout-<D>s@down[,every=<P>s][,first=<F>s][,seed=N]
```

- **`blackout-<D>s`:** a parameterised profile name (D in seconds, 0.1-60, decimals allowed), matched by pattern, not
  in the `PROFILES` table. It combines with the table's names by `+` as today (`blackout-4s+loss-1@both`).
- **Placement:**
  - `@both` = the downlink at `@post-fec` (as the other bench profiles) **and the uplink**;
  - `@down` = the downlink only, at `@post-fec`;
  - `@pre-fec` / `@post-fec` with a blackout = the downlink only, at that hop;
  - `@both` / `@down` without a blackout name: `ValueError`.
- **Options:** comma-separated `key=value`, in any order: `every=<P>s` (default 120; P > D), `first=<F>s` (default
  = P), `seed=N`. Today's specs (`…,seed=N`) parse exactly as before.
- **Defaults:** D 4, P 120, so `blackout-4s@both` = 4 s dead both ways every 120 s.

## One scheduler (wall clock, both sides)

- **`Blackout(d_s, every_s, first_s, epoch)`**, pure: `active(now)` ⇔ `now ≥ epoch + F` and
  `(now − epoch − F) mod P < D`. Monotonic seconds.
- **`shared_blackout(profile)`**, a process singleton (one per spec):
  - its epoch is the monotonic time of the first call, which is the companion's import of the first hooked module;
  - **every user (the downlink shim and the three uplink gates) reads the same object**, so the drops are on one
    clock;
  - blackouts fall at epoch + F + k·P on the companion's clock, independent of stream starts (it is the link, not
    the stream).
- **The downlink:** `Impairer.offer` gains a first stage. While the blackout is active the packet is dropped, and the
  new counter `dropped_blackout` counts it.
- **The uplink: `UplinkGate`** (only for `@both`). `drop(kind)` returns True while the shared blackout is active and
  counts it, by kind (`controller`, `heartbeat`, `client_health`) and in total (`uplink_dropped`).
  - The downlink shim's per-second line and `status()` carry `uplink_dropped`. Every profile's line gains
    `dropped_blackout` and `uplink_dropped` (0 when unused); the flag-absent path writes no line at all.

## The uplink hooks (each behind a guarded module-level import; absent = not imported, `None`, the code unchanged)

1. **`native_session_io.py`, `NativeControllerBridge._receive_loop`** (port 48102, client → host), inside the `try`,
   right after `recvfrom`:
   `if _impairment_uplink is not None and _impairment_uplink.drop("controller"): raise socket.timeout`
   - The datagram is consumed and treated as never having arrived: the loop runs its own `socket.timeout` branch.
     That branch neutralizes a player after 250 ms, calls recovery's silence callback once per episode past its
     threshold, and flushes the gap log.
   - A plain `continue` would be wrong: during a blackout `recvfrom` would never time out, so the silence checks
     would never run. With the hook, the host sees what UX-R3's host saw.
   - **Disclosed difference:** a real dead link wakes the branch every 50 ms (the socket timeout). Here it runs at
     each dropped packet (~430 / s). The branch is idempotent (once per episode), so the outcome is the same.
2. **`plugins/games.py`, `action == "native-stream-heartbeat"`** (HTTP, the client's 2-s heartbeat), first statement:
   `if _impairment_uplink is not None and _impairment_uplink.drop("heartbeat"): return {plugin, ok False,
   impairment "uplink_blackout"}`
   - Nothing is appended to the heartbeat log and recovery's `note_heartbeat` is not called: the host has no
     heartbeat, as in UX-R3.
   - **Disclosed difference:** a real dead link leaves the client's POST hanging up to its 1.5-s read timeout. Here
     it gets an immediate answer. The client ignores the answer either way, and it sends the next heartbeat on its
     own 2-s tick.
3. **`privyhub_service.py`, `POST /diagnostics/client-health`**, right after the body is read (so the connection
   stays well formed):
   `if _impairment_uplink is not None and _impairment_uplink.drop("client_health"): send 503 and return`
   - Not accepted: no client-health snapshot, no stream telemetry, no ladder observe, no WAN classify for that
     report.

Every other uplink request (start, stop, ready, desync) passes. They are one-shot and outside a running stream's
continuity, and that is stated.

## Flag absent = today (the proofs)

- **The AST method:** for `_receive_loop`, the `handle`-level heartbeat branch's enclosing function and the HTTP POST
  handler, the edited function's AST with the guarded `if _impairment_uplink …` statements removed equals the
  predecessor's AST (`ast.dump`).
- The module-level import in each file is guarded on `PRIVYHUB_IMPAIRMENT` (an AST test, as G8-P1's).
- In a fresh process with no flag: `impairment` not in `sys.modules` after importing `native_session_io` (the other
  two files import the service stack and are covered by the AST checks).
- With a downlink-only profile (`loss-1`, `@pre-fec` / `@post-fec`): `uplink_gate_from_environ` returns `None`, so
  the loops are untouched by today's profiles too.
- The existing `tests/impairment` suite, unchanged apart from the new tests, green.

## Proof in process (as G8-P1's; 60 s per case; loopback only)

- **A. The downlink:** G8-P1's synthetic 60-fps × 12-packet source through `Shim` with
  `blackout-4s@down,every=20s,first=10s` for 60 s.
  - Tolerance: exactly 3 dark spans at 10 / 30 / 50 s (± 1 frame), each 4.0 s ± 1 frame (17 ms).
  - Nothing dropped outside them; the dropped share 20 % ± 0.5.
  - Also the default `blackout-4s@both` over 60 s: no blackout before 120 s, 0 dropped.
- **B. The uplink:** a real `NativeControllerBridge` on the loopback (its socket, its 50-ms timeout, its receive loop
  thread), `_apply_report` / `_neutralize` / the gamepads stubbed. It gets controller packets at 430 / s for 60 s
  with `blackout-4s@both,every=20s,first=10s`, recovery's silence callback set at 1,000 ms.
  - Tolerance: 3 applied-packet gaps of 4.0 s ± 60 ms at 10 / 30 / 50 s, and no other gap > 60 ms.
  - The callback fired exactly 3 times; every player neutralized once per blackout.
  - `uplink_dropped` = the packets sent in the dark spans ± 2.
- **C. Both on one clock:** the downlink and the uplink run together, from one shared `Blackout`. Their dark spans
  start within 20 ms of each other.
- **D. The HTTP gates:** the heartbeat and client-health hooks called through the gate in and out of a dark span: drop
  / pass as the schedule says, counted by kind.
- **The cost:** the gate's per-packet cost (`time.perf_counter_ns` over 10⁶ calls), and the shim thread's CPU at
  ~720 packets / s against G8-P1's 2.1-7.0 % (the cost bar G8-P1 reported as not met; stated again, not re-litigated).

## Not in B1

No stream, no restart, no adoption. The bench cells are BENCH-R1 (session A).
