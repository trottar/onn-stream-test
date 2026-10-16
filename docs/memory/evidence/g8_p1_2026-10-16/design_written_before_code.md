# G8-P1 — the design, written before any G8-P1 code

Flag: `PRIVYHUB_IMPAIRMENT=<spec>`. Absent or empty = today: `native_fec_relay`
never imports `impairment`, binds the same port, and sends to the same target;
no thread, no port, no file. The encoder command is the same **with or
without** the flag (below), so its masked hash cannot change.

## What the survey found (before the code)

- The encoder sends RTP to the loopback FEC sender (`rtp://` on the loopback,
  the sender's port, `pkt_size=1200`). That sink is built in two places
  (`native_stream.py`, the Linux and Windows builders).
- The FEC sender (`NativeVideoFecRelay`) forwards each RTP packet unchanged
  (same sequence number) to the client. It emits XOR parity per group of
  ≤ 8 **only when the group's sequence numbers are consecutive**; a group
  with a gap is skipped, with no parity.
- **So loss injected *before* the FEC sender can never be recovered by FEC.**
  The damaged group gets no parity, and the client sees a bare sequence gap.
  A real WAN, and the nft harness, lose packets *after* the FEC sender: RTP
  and parity alike, with parity able to repair a single loss per group. The
  task places the shim between the encoder and the FEC sender. Its own proof
  expects `loss-1` to be *recovered* by FEC, which that placement cannot
  give.
- **Audio does not share this hop.** The audio sender sends from its own
  socket. The shim impairs **video only** (RTP, plus parity in the post-FEC
  placement). The controller return path and the client → host direction are
  untouched. That is the shim's limit; the nft harness stays the whole-link
  tool.

## The design

- **`companion/impairment.py`** (new), a loopback UDP relay thread inside
  the companion: `Shim(listen, forward, profile, seed, log_path)`.
- **Two placements, one variable.** `PRIVYHUB_IMPAIRMENT=<profile>[@pre-fec|@post-fec][,seed=N]`:
  - **`@pre-fec` (the default: the task's placement).** The shim binds the
    sender's own port, so the encoder command is unchanged. The sender binds
    an ephemeral loopback port, and the shim forwards there. Encoder →
    shim → FEC sender → client.
  - **`@post-fec`.** The sender binds its port as today but sends to the
    shim's ephemeral loopback port; the shim forwards to the client.
    Encoder → FEC sender → shim → client. **This is the placement that
    matches a WAN or the nft harness** (FEC can repair what the shim drops).
    It is offered beside the task's, not instead of it, and the record says
    which to use for G8-S1.
- **The hook** in `native_fec_relay.py`, all inert when `impairment` is not
  imported:
  - a module-level guarded import;
  - in `start()`, the shim built from the environment, the bind port and
    the send target taken from it, and the shim started after the sender's
    socket is bound;
  - in `stop()`, the shim stopped.
- **Profiles** (names → parameters; `+` combines; seeded `random.Random`,
  default seed 1):

| name | effect |
| --- | --- |
| `loss-1`, `loss-5` | random loss, 1 % / 5 % of packets |
| `burst-50x20` | 50 consecutive packets dropped every 20 s (the first burst at 10 s) |
| `delay-50`, `delay-150` | a fixed one-way delay of 50 / 150 ms |
| `jitter-30` | an added delay, uniform 0-30 ms per packet; order preserved (FIFO release) |
| `reorder-5` | 5 % of packets held and released one packet later (a one-slot swap) |
| `cap-6000`, `cap-4500` | a token bucket at 6000 / 4500 kbit/s with a **bounded** FIFO queue (≤ 100 ms of the cap's bytes); over that, tail-dropped; the depth reported |

  The stages apply in a fixed order, as listed: burst, loss, reorder,
  delay + jitter, cap. A held packet with nothing behind it is released
  after 50 ms (no packet waits forever).
- **Telemetry:** `logs/impairment.jsonl`, one line per second:
  - the profile, placement and seed;
  - in / out / dropped (by stage) / delayed / reordered packets;
  - bytes in and out;
  - the queue depth now and its maximum;
  - the shim thread's CPU time.

  No address is written.
- **Cost:** the shim thread's CPU time per second (`time.thread_time`),
  measured in process at 7 Mbit/s (≈ 730 packets/s of 1200 B). The bar is
  ≤ 1 point of a core.

## The proof (in process, no stream)

1. **Per profile, 60 s:** a synthetic 7 Mbit/s RTP source → the shim → a
   capture socket. Measured: loss %, the burst count, mean / p95 added delay,
   jitter (p95 − p5 of added delay), reordered %, out rate, queue max, CPU.
   Each is checked against the profile within a stated tolerance (a table).
2. **The real FEC sender** (`NativeVideoFecRelay`, imported, loopback only),
   fed a synthetic 60-fps stream of multi-packet frames. A capture socket
   plays the client: it counts groups recovered (one missing, the parity
   present), groups unrecoverable, and packets lost after FEC.
   - Run for `loss-1` and `burst-50x20`, in both placements.
   - Expected: post-FEC `loss-1` → mostly recovered; post-FEC
     `burst-50x20` → unrecoverable groups; pre-FEC → nothing recovered.
   - The per-2-s reports (fps from complete frames, post-FEC lost) are read
     by G5-S1's `classify_window`.
3. **Flag absent:**
   - the encoder command builder's output, hashed with the window masked
     (E4-S5B's method), the same before and after;
   - the sender binds exactly its own port and sends to the client given;
   - `impairment` is not imported;
   - nothing else is bound.
   With the flag, the encoder command is the same too: the shim takes the
   port, not the command.
4. Unit tests; the redactor.
