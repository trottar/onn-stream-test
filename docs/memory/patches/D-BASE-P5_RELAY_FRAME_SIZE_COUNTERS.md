---
memory_schema: 1
as_of: 2026-09-21
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
durable_memory_updated: true
---

# D-BASE-P5 — packets per frame, counted in the relay

## Purpose

`O1` (2026-09-21) located the loss at a per-frame micro-burst meeting a
queue, and left two queues standing: the AP's per-station wireless queue
and the onn's own receive path. Separating them needs to know **how big
the bursts actually are**, and nothing on the host recorded it — the relay
counted packets, bytes and FEC groups, but a group is 8 packets or a
marker, not a frame.

This patch counts the packets of each encoded frame. **Diagnostic only.
Nothing forwards, delays, reorders, drops or inspects a payload
differently, and the pacing knob (`D-BASE-P3`) stays at its default 0.**

## Changed scope

**`companion/native_fec_relay.py`**
-> `94fd7fae42ac28569c089fd50c5af616aee6580919699d80635928f8a7a61b8d`
(was `6aa045831c05b2eec7e712176c0937d5e5a1b5312dfdf139e20f747a6cf0dba3`).

- `_handle_rtp` calls the new `_note_frame_packet(parsed)` **before the
  pacing branch**, so both arms are measured identically. An unparseable
  packet is not attributed to a frame — it has no timestamp to attribute
  it to.
- A **frame** is the run of packets sharing one RTP timestamp, ended by
  the marker packet. A frame ended instead by a timestamp change is
  counted too, and **separately** as `unmarked_frames`: an encoder restart
  mid-frame is the usual cause and folding it into the next frame would
  overstate the large ones.
- `_close_frame_locked` files each frame into a **one-second bucket** of
  relay wall time: `frames`, `packets`, `mean_packets`, `max_packets` with
  its own `max_at_utc`, `frames_ge_40`, `frames_ge_80`, `unmarked_frames`.
- A **packets-per-frame histogram** (512 buckets plus overflow) gives
  exact p50/p90/p99 over a whole session without keeping a sample per
  frame — the same bounded-instrument choice `D-BASE-P3` made for achieved
  spacing.
- `_frame_buckets` is a `deque(maxlen=1800)`: a **30-minute ring**,
  carried in full by `status()["frame_sizes"]["buckets"]`.
- A **separate 1 Hz writer thread** (`PrivyHub-Native-FEC-Frames`) closes
  the previous second's bucket and appends it to
  `logs/games/native_frame_sizes.jsonl`. **The file write is never on the
  receive thread**, so the forwarding path never waits on the filesystem.
  A bucket is closed only once the wall clock has passed its second, so no
  line is written while frames can still land in it.
- Rotation via the existing `games.log_rotation.append_line` at **4 MiB
  keeping 3**, into the same `stream_log_archive/` the heartbeat log uses,
  so `tools/diagnostic_retention.py`'s existing `stream_log_archive`
  family bounds it with no retention change.
- `stop()` closes the frame in flight and the open bucket and flushes,
  so the last second of a session lands like every other. All counters
  reset in `start()`, per session, like every other counter here.
- `OSError` on the write increments `log_errors` and is swallowed: a log
  that cannot be written must not stop the stream.

**`companion/native_stream.py`**
-> `caa4c70486ff8255a92ba14c1a9bfc3cf4479468dc45af65bad5d8cb2ed8c670`
(was `8be05fcfe406564252c8b414e5e5a4479b218bb0c6ef9e89e9d2258de7d07039`).

Passes `frame_size_log=<log_dir>/native_frame_sizes.jsonl` when
constructing the relay, and adds `fec_frame_size_status()` beside the
existing `fec_pacing_status()`.

**`companion/plugins/games.py`**
-> `23de0c410044b7291775145ac7239e52675cc2cdf8870b79e6e04cdec9e7a658`
(was `1d466421c2854033af372b2d3f438039610c2af751fdfd552e7bc0dd8c017415`).

`native-stream-status` **drops the 1,800-row ring unless `frame_series=1`
is asked for**, replacing it with `buckets_omitted: <n>`. The summary —
including the percentiles and the session maximum — is always present, and
the JSONL file holds every row regardless. Several `probe_c3_*` tools poll
this endpoint every couple of seconds for a whole session; the relay's own
contract (the full ring on `relay.status()`) is unchanged.

## Cost

**0.36 us per packet** on the forwarding thread, measured over 200,000
calls — **0.03 % of one core** at the stream's ~820 packets/s. One extra
uncontended `RLock` acquire per packet, against a `sendto` syscall that
was already there. One file append per second, off-thread.

Two 20-minute sessions with the counters live: relay `send_errors` **0**,
`log_errors` **0**, fps **59.74** both, `spike_20_ms`/min **47.2 / 46.8**
(inside `P4`'s 40.6–62.4 band and below `R5`'s 51.5). **No cost shows.**

## Validation

**`evidence/d_base_p5_2026-09-21/test_frame_sizes.py`** — 40 assertions
over synthetic RTP, no socket and no thread: packets per frame and the
marker ending it; the unmarked frame counted and flagged; exact
percentiles off the histogram; an unparseable packet not attributed; the
bucket's own maximum and mean; the ring bounded at 1,800 with the oldest
dropped; one JSON line per closed bucket with the right schema; the
no-log-path case still counting. **All pass.**

**Runtime**: 2,402 seconds of streaming, 2,414 log lines, 145,330 frames
counted, 0 log errors, 0 rotations. The distribution is stable across two
independent sessions — `frames_ge_80` per minute repeats at Pearson
**0.996**.

`git diff --check` clean. Python compiles.

## Not done

- **No client change.** The onn was not rebuilt; instruments 2 and 3 of
  `D-BASE-P5` are host-side reads.
- **No forwarding change**, and the pacing default stays **0**.
- **No retention change** — the new log inherits the existing
  `stream_log_archive` family.

Record: `evidence/D_BASE_P5_WHICH_QUEUE_2026-09-21.md`.
