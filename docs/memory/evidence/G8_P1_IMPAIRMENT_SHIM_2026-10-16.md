---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 92e388e
---

# G8-P1 — the impairment shim

**Classification: HARNESS BUILT behind `PRIVYHUB_IMPAIRMENT=<profile>`;
proved in process; ENVELOPE NOT MEASURED; NOT ADOPTED; nothing committed.**

- All eleven profiles met their tolerances over 60 s.
- With the flag absent:
  - the FEC sender is byte for byte HEAD's;
  - the encoder command's masked hash is unchanged (it is unchanged with the
    flag set too);
  - no port, thread or file is added.
- **One bar is not met:** the shim thread costs **2.1-7.0 % of a core** at
  ~6.9 Mbit/s, against the task's ≤ 1 point (§3).

- Task: `handoffs/G8-P1_IMPAIRMENT_SHIM_TASK.md`, queue `QUEUE_2026-10-16C.md`
  item 2, session B, unattended. **Baseline `92e388e`.** The tree carried
  the user's uncommitted work and G5-S2's; neither was touched
  (`g8_p1_2026-10-16/git_status_at_start.txt`).
- No companion restart, no stream, no game, no adb, no nft, no sudo. Every
  socket was on the loopback, on ephemeral ports. The companion's own port
  was never bound, because every relay in the proof bound its own.

## 1. The design (written before the code)

`g8_p1_2026-10-16/design_written_before_code.md`, sha256 `c094cd80…36c3b`,
hashed at 19:00:56Z before the first G8-P1 code edit.

**The finding that shaped it.** The FEC sender forwards every RTP packet
unchanged. It emits XOR parity only for groups of ≤ 8 with **consecutive**
sequence numbers; a group with a gap gets none. So loss injected *before*
the sender (the task's placement) can never be recovered by FEC, which
contradicts the task's own expectation ("`loss-1` → recovered"). A WAN, or
the nft harness, loses packets *after* the sender. So the shim offers both
placements in one variable:

| placement | path | when to use |
| --- | --- | --- |
| `@pre-fec` (**the default**, the task's) | encoder → shim → FEC sender → client. The shim takes the sender's port; the sender binds an ephemeral loopback port behind it. **The encoder command is unchanged** | source-side loss (FEC sees the gaps as unprotected) |
| `@post-fec` | encoder → FEC sender → shim → client. The sender sends to the shim's ephemeral loopback port | **WAN-like:** RTP and parity both impaired, FEC can repair. **The placement G8-S1 should use** |

- **Spec:** `PRIVYHUB_IMPAIRMENT=<name>[+<name>…][@pre-fec|@post-fec][,seed=N]`,
  default seed 1.
- **Video only.** The audio sender and the controller return path do not use
  this hop. The client → host direction is untouched. The nft harness stays
  the whole-link tool.

**The profiles** (one table, `impairment.PROFILES`; stages in the order
burst, loss, reorder, delay + jitter, cap):

| name | effect |
| --- | --- |
| `loss-1`, `loss-5` | random loss 1 % / 5 % |
| `burst-50x20` | 50 consecutive packets dropped every 20 s (the first at 10 s) |
| `delay-50`, `delay-150` | a fixed one-way delay of 50 / 150 ms |
| `jitter-30` | an added delay, uniform 0-30 ms, in FIFO order (no reordering) |
| `reorder-5` | 5 % of packets held one slot (a held packet with nothing behind it is released after 50 ms) |
| `cap-6000`, `cap-4500` | a token bucket at 6000 / 4500 kbit/s; the FIFO holds ≤ 100 ms of the cap's bytes, then tail-drops; the depth is reported |

**Telemetry:** `logs/impairment.jsonl`, one line per second. Each line
holds:

- the profile, placement and seed;
- packets and bytes in and out;
- the drops by stage, the delayed and reordered packets;
- the queue depth and its maximum;
- the thread's CPU time.

There is no address.

**The hook** (`native_fec_relay.py`) is all guarded: a module-level
guarded import; in `start()` the shim built and attached; in `stop()` the
shim stopped. `native_stream.py` is not edited.

## 2. The proof (`proof.py` → `proof_tables.md`, `proof.json`, `proof_console.txt`)

**A. Each profile, 60 s.** A synthetic ~6.9 Mbit/s RTP source (60 fps × 12
× 1200 B) → the shim → a capture socket on its own thread. The baseline
loopback delay is subtracted (median 0.19 ms).

| profile | tolerance | measured | verdict |
| --- | --- | --- | --- |
| none | no loss, no reorder | 0 %, 0 % | PASS |
| `loss-1` | 0.7-1.3 % | 1.104 % | PASS |
| `loss-5` | 4.5-5.5 % | 5.178 % | PASS |
| `burst-50x20` | 3 bursts of exactly 50 | 3 × 50 | PASS |
| `delay-50` | mean 45-56 ms, no loss | 48.69 ms (p95 50.21) | PASS |
| `delay-150` | mean 145-156 ms, no loss | 148.70 ms (p95 150.22) | PASS |
| `jitter-30` | mean 10-30, spread 18-34 ms, order kept | 23.6 ms, 18.44 ms, 0 % reordered | PASS |
| `reorder-5` | 4-6 %, no loss | 4.991 % | PASS |
| `cap-6000` | out 5700-6300 kbit/s, queue within its bound | 6000.3 kbit/s; queue max 63 (bound 64); 13.1 % tail-dropped | PASS |
| `cap-4500` | out 4275-4725 kbit/s, queue within its bound | 4500.3 kbit/s; queue max 48 (bound 48); 34.8 % tail-dropped | PASS |
| `loss-1+delay-50+jitter-30` | loss 0.7-1.3 %, mean 55-80 ms | 1.032 %, 73.5 ms | PASS |

A note on the delay numbers. Source, shim and capture share one Python
process, so the capture's timestamps carry up to one frame (~16 ms) of
scheduling spread even with no impairment (the "none" row's p95-p5). The
delays read below the set value by ~1.3 ms for the same reason. Every
tolerance was met with that spread included.

**B. The real FEC sender** (`NativeVideoFecRelay`, imported), 60 s per
case. The capture plays the client:

- a group with exactly one missing packet and its parity present counts as
  **recovered**;
- more than one missing counts as **unrecoverable**;
- a missing packet in no parity-carrying group is lost.

The per-2-s reports (fps from complete frames, post-FEC lost) are read by
G5-S1's `classify_window`.

| case | parity groups | recovered | unrecoverable | lost after FEC | G5-S1 windows (primary) |
| --- | --- | --- | --- | --- | --- |
| `loss-1@pre-fec` | 6862 | **0** | 0 | 477 (all 477 the shim dropped) | lossy 6 |
| `loss-1@post-fec` | 7095 | **415** | 10 | 26 (of 546 dropped, parity included) | lossy 6 |
| `burst-50x20@pre-fec` | 7176 | 0 | 0 | 150 | clean 3, lossy 3 |
| `burst-50x20@post-fec` | 7182 | 0 | 3 | 132 | clean 3, lossy 3 |
| `cap-4500@post-fec` | 475 | 297 | 163 | 15217 | **capacity-limited 6** |

As expected:

- **pre-FEC loss is never recovered.** Note the 6862 groups against 7095:
  a group with a gap emits no parity.
- **Post-FEC, FEC repairs 1 % loss down to 26 packets a minute.** That is
  still over G5-S1's 10 / min `lossy` bar.
- A 50-packet burst defeats an 8+1 group. Post-FEC, three groups are
  partially hit. The fully-erased groups lose their parity too, so they
  count as lost, not as unrecoverable.
- `cap-4500` against a 6.9 Mbit/s stream is read as `capacity-limited`.

B is read, not gated.

**C. Flag absent** (each a PASS):

| check | result |
| --- | --- |
| the encoder command, masked hash (E4-S5B's method; a fixed fake window id masked), HEAD vs today × flag absent / set | **one hash** (`b3c78756…`) across all four; the sink `rtp://<loopback>:<the sender's port>?pkt_size=1200` in all |
| the FEC sender, HEAD's (from git) vs the edited one, 10 s of the same stream | **identical**: 8400 / 8400 datagrams, sizes, RTP headers and parity headers |
| a fresh process with no flag | the sender bound its own port (1), sent to the client (1), `impairment` not imported (0), no shim thread (0) |

The builder needs an X11 display *name* to build the command. The harness
set the variable for the build only; no display was opened.

**Unit tests** (`tests_output.txt`):
`python3 -m unittest discover -s tests/impairment -v` → **13 OK**.

- the parser;
- each stage on a fake clock: order, random loss, seeded repeatability,
  bursts exactly 3 × 50, delay, FIFO jitter, reorder, the cap's bounded
  queue;
- both placements against the real FEC sender (pre-FEC: the shim takes the
  port; post-FEC: RTP and parity both pass the shim);
- stop releases the port and thread;
- flag absent: not imported (AST), same port, same target, no thread.

The first run of two placement tests failed. The test's own capture socket
was read only after sending ended, so its receive buffer overflowed. The
shim had passed all 960 packets. The test now reads concurrently
(disclosed).

**Regression** (`tests_regression.txt`): `tests/overlay` 17, `tests/session_identity`
80, `tests/wan_telemetry` 18, `tests/wan_adaptation` 23, all OK.

## 3. The cost bar: NOT MET

The shim thread's CPU (`time.thread_time`), at ~6.9 Mbit/s (≈ 720 packets/s):

| profile | CPU, % of a core |
| --- | --- |
| none / loss / burst / reorder | 2.05-2.09 |
| delay | 2.33-2.38 |
| jitter / combination | 3.78-3.79 |
| cap-6000 / cap-4500 | 6.97 / 6.07 |

The task's bar is ≤ 1 point. A per-packet Python relay (select, recv,
sendto, a heap) costs about 28 µs a packet. The timed profiles add a wake-up
per release. The shim runs only in a characterization session, never in the
adopted state, and every line of `impairment.jsonl` carries its CPU, so an
envelope run can account for it. **Not tuned here, to decide:**

- (a) accept it as the harness's stated cost, reported beside every G8-S1
  host-CPU reading;
- (b) a release path batched to 1-ms ticks (it would reduce the timed
  profiles' wake-ups, not the 2 % floor);
- (c) a native helper (a build step; a decision for the user).

## 4. For the user — proposed next (not run)

**G8-S1, the first adverse-network envelope.**

- The E1 PS1-STREAM row under each profile, `@post-fec`, on the LAN, 10 min
  each.
- G5-S1 on; G5-S2 off, then on.
- Unattended, about 3 h, no hands.
- Reported per profile: the G5-S1 class, the ladder's decisions, recovery,
  and the shim's own CPU.

Before it: the user's call on the cost bar (§3). The drop-in to run with:
`Environment=PRIVYHUB_IMPAIRMENT=<profile>@post-fec`, a restart; removed
after.

## 5. Files; disclosures

- **`g8_p1_2026-10-16/`:**
  - `baseline_commit.txt`, `git_status_at_start.txt`,
    `predecessor_sha256.txt`, `after_sha256.txt`;
  - `design_written_before_code.md` / `.sha256`;
  - `g8_p1.diff`: the FEC sender's hook (zero-context), G8-P1's ROADMAP
    hunk, the new module and tests;
  - `proof.py`, `proof_tables.md`, `proof.json`, `proof_console.txt`;
  - `tests_output.txt`, `tests_regression.txt`;
  - `redact_check.txt`, `manifest.sha256`.
- Patch record: `patches/G8-P1_IMPAIRMENT_SHIM.md`. Not written:
  `CURRENT.md`, `CURRENT_HANDOFF.md`, `KNOWN_ISSUES.md`, `PATCH_INDEX.md`.
- **Disclosed:**
  - the placement deviation (§1: both placements built; the task's is the
    default);
  - the cost bar missed (§3);
  - the test-capture fix (§2);
  - the redactor's first pass hit the new module and its tests, which wrote
    the loopback as a literal. They now build it from an integer, as the
    rest of the tree does; the unit tests were re-run (13 OK);
  - the proof harness's first two attempts:
    - the encoder builder needed a display name: the harness's own `built`
      guard caught that four "hashes" were of one error string;
    - HEAD's module needed registering before it ran.

  Both were fixed before the recorded run.
- Temp files: `g8_p1_head_*` under the system temp directory, left in place.
  Nothing deleted, nothing fetched.
- **`logs/impairment.jsonl` was written.** The shims built through the FEC
  sender's hook take the project's log path, and those ran in the unit
  tests' placement cases, the 3-s smoke run and proof B. That is 335
  per-second lines (gitignored), which shows the telemetry line works. They
  were left in place. An earlier draft of this record said no line was
  written; that was wrong and is corrected here.
- Git status: `logs/g8_p1_git_status.txt`.
