---
memory_schema: 1
as_of: 2026-09-21
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
durable_memory_updated: true
---

# D-BASE-P3 — a sender pacer in the FEC relay, diagnostic, default off

## Purpose

`B2` left the production-path loss still bursty (median 4.46 packets per
forward-gap event) and `R3a`'s resume burst dropped 690 packets with no
restart — packets minted by the host and lost before the onn's decoder. The
encoder emits a frame's packets back to back at line rate, so every frame is
a micro-burst into the Opal's wireless queue and the onn's receive buffer. If
the ordinary loss is that queue overflowing, spreading a frame's packets
across part of the frame interval should cut loss and burst size sharply; if
the loss is air, it should change nothing.

**This patch builds only the instrument.** It is diagnostic, **default off**,
and adopting pacing remains a product decision for the user. Result:
`evidence/D_BASE_P3_SENDER_PACING_2026-09-21.md` — **INDETERMINATE**, not
adopted, knob left at 0.

## Changed scope

**`companion/native_fec_relay.py`**
-> `6aa045831c05b2eec7e712176c0937d5e5a1b5312dfdf139e20f747a6cf0dba3`
(was `ffcd71d8faa2a16f7cfd2f18030c976f4b15659f080ca1769eaab877fdc3faed`).

Configured by the **environment variable `PRIVYHUB_FEC_PACING_US`**, not a
companion config key, read in `start()` so the arm is whatever the companion
process was started with. `0`, unset, non-numeric and negative all mean off.
An explicit `pacing_us=` constructor argument exists for the offline check and
wins over the environment.

- **Off is the old code path, untouched.** `_handle_rtp` branches to the paced
  implementation only when `pacing_us > 0`; otherwise it forwards on arrival
  and `_emit_group_locked` sends parity immediately, exactly as before. The
  only edit on that path is that `_emit_group_locked` now calls
  `_emit_locked(...)`, which with pacing off is a direct `_send(...)`.
- **On**, `_handle_rtp_paced` accumulates a frame's packets in arrival order
  keyed by RTP timestamp, inserts each group's parity directly after the group
  it protects, and hands the whole frame to a dedicated
  `PrivyHub-Native-FEC-Pacer` thread when the marker lands. **The FEC wire
  format, group size, parity contents and packet order are untouched.**
- **Hard cap:** spacing is clamped to `PACING_FRAME_BUDGET_US (8000) /
  packets-in-frame`, and the budget is measured from the **arrival** of the
  frame's first packet, so accumulating and waking are inside it and 8 ms is
  the whole added latency — under half a 16.7 ms frame at 60 fps.
- `_wait_until` sleeps only while more than 300 µs remains and busy-waits the
  last ~200 µs. **Measured on this host first:** `time.sleep` carries a ~55 µs
  overshoot floor (`sleep(150 µs)` returns after a median 205.5 µs) so it
  cannot place a 150 µs gap; the busy-wait lands at 150.1 µs p50, 150.3 max.
- A frame whose marker never arrives is flushed on the receive socket's 0.25 s
  timeout, so nothing can sit in the pending buffer.
- `status()` gains a `pacing` block, also returned alone by the new
  `pacing_status()`: `enabled`, `configured_us`, `source`, `frame_budget_us`,
  `paced_frames`, `paced_packets`, `clamped_frames`, `late_frames`,
  `last_spacing_us`, `achieved_spacing_p50_us`, `achieved_spacing_p99_us`,
  `max_start_delay_us`, `queue_depth`, `max_queue_depth`. Achieved spacing is
  a **bounded 5 µs-bucket histogram** (800 buckets plus overflow), so a long
  session cannot grow it.

**`companion/native_stream.py`**
-> `8be05fcfe406564252c8b414e5e5a4479b218bb0c6ef9e89e9d2258de7d07039`
(was `11a182e7993f47891111018d40ef84342c1a2a018d1c890094df6857729d1162`).
One accessor, `fec_pacing_status()`, returning `self._fec_relay.pacing_status()`.
No behaviour change.

**`companion/games/decoder_session_log.py`**
-> `b14fd191fad326785f4c3d600be5e674c4668fc4857a5631125624ccfc8cd74c`
(was `a4815182eb66bb1ad2eedecfa87a0775ffabadf5d4607a9317c484479a997c5f`).
`write_decoder_session_log` takes an optional `host_extra` dict merged into
the existing `host` block beside `host_thermal_c`. Default `None` = today.

**`companion/plugins/games.py`**
-> `47b008280b416be393a8def7dfc8daffb8e80e8e35ee9e4d2ffb6a28ceff8af5`
(was `9545f03939c36a07323071ae75a1c0a991887bf2d71b4b5cb90f5ca5635bd928`).
The `decoder-session-log` action passes
`host_extra={"fec_pacing": self._native_stream.fec_pacing_status()}`, so every
report records which arm produced it.

**Not changed:** the Android client (the task forbade it), the encoder command,
`pkt_size`, the FEC group size, the profile, and every other companion path.

*Hash note:* `native_stream.py`, `decoder_session_log.py` and `plugins/games.py`
already carried uncommitted working-tree edits from earlier work before this
patch; their "was" hashes above are of that working tree, not of HEAD.
`native_fec_relay.py` was clean at HEAD.

## Validation

**Offline equivalence check** — `evidence/d_base_p3_2026-09-21/test_pacer.py`,
output `p3_pacer_offline_check.txt`. The same synthetic frames are driven
through both paths and the emitted byte strings compared:

- **identical bytes and identical order**, 128 packets each arm;
- `rtp_packets`, `parity_packets`, `groups`, `skipped_packets`, `send_calls`,
  `send_errors`, `sent_bytes` all equal;
- with pacing on, achieved spacing p50 **147.5 µs**, p99 152.5, against a
  configured 150;
- clamp exercised: 40-packet frames at `PACING_US` = 400 report
  `clamped_frames` 3 of 3 and a reduced `last_spacing_us`, `late_frames` 0.

**One correction the check caught.** The first version anchored the send
schedule on the first packet's *arrival*; because a frame is only queued once
its marker lands and waking the sender costs more again, the early packets
were already due and went out back to back — achieved p50 **7.5 µs instead of
150**. The schedule is now anchored on the moment the sender thread starts the
frame, with the budget still measured from arrival, so the latency bound is
unchanged.

**Runtime**, 15 sessions on the production path, companion restarted for every
one with the port confirmed free, the serving pid confirmed to be the one just
launched and the relay's reported `configured_us` confirmed before the stream
opened (D-068). `send_errors` **0** in all 15. Zero discontinuities in all 15.
Achieved 147.5 µs p50 at a configured 150 in all five sessions; 187.5 at a
configured 400, the 8 ms budget clamping 30 % of frames. Full numbers in the
evidence record.

`python3 -m py_compile` clean on all four files; `git diff --check` clean.

## Status

**DEVELOPMENT / DIAGNOSTIC. Default off, and it ends this run off.** The
environment variable is set nowhere in the repository, in no service unit and
in no harness that outlives the run; the last session of the run,
`S3off`, records `fec_pacing.enabled: false`.

The instrument is kept because it is the only way to vary sender burstiness on
this stack, and because the null it produced is bounded by its own 8 ms budget
— a stronger test needs a larger budget, which costs latency, and that is the
user's call.
