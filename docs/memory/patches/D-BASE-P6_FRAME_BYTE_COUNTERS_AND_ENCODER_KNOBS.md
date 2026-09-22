---
memory_schema: 1
as_of: 2026-09-21
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
durable_memory_updated: true
---

# D-BASE-P6 — per-frame byte counters, and two diagnostic encoder knobs

## Purpose

`D-BASE-P5` measured frame size in **packets** and found the loss tracks
the large-frame count. `D-BASE-P6` had to *intervene* on that variable, and
the encoder's knob — `h264_vaapi -max_frame_size` — is set in **bytes**. A
cap can only be checked in the unit it is set in, so the counters needed a
byte series; and an arm needed a way to be set without editing source
between sessions.

**Diagnostic only.** The counters count; the knobs default off and, unset,
the encoder argv is byte for byte what it was before. **Nothing is
adopted** — `D-BASE-P6` restored the default and verified it.

## Changed scope

**`companion/native_fec_relay.py`**
-> `20cd678684abaec31721f5a18e53c52ad64777e3b80147b069d41c5608e833a1`
(was `94fd7fae42ac28569c089fd50c5af616aee6580919699d80635928f8a7a61b8d`).

- `_note_frame_packet` accumulates `len(parsed.payload)` beside the packet
  count, so a frame's size is carried in **payload bytes** — no RTP
  headers, no FEC parity.
- `_close_frame_locked` files `payload_bytes`, `max_bytes` with its own
  `max_bytes_at_utc`, `mean_bytes` and `frames_over_cap` into the same
  one-second bucket the packet columns already use. **The packet columns
  are unchanged**, so every `P5` reading still parses.
- A whole-session **1 KiB byte histogram** (256 buckets plus overflow)
  gives exact byte percentiles without keeping a sample per frame, the
  same bounded-instrument choice `P3` made for spacing and `P5` for
  packets. `_frame_byte_percentile_locked` returns the **upper edge** of
  the bucket rather than interpolating: the histogram knows the bucket,
  not the value inside it, and a fabricated interpolation would read as a
  measurement.
- `PRIVYHUB_FRAME_BYTE_CAP` (bytes, default unset) is the **yardstick** the
  frames are measured against, read at `start()`. It sets nothing on the
  encoder; it only decides what `frames_over_cap` counts.
- `status()["frame_sizes"]` gains `payload_bytes`, `mean_bytes`,
  `p50/p90/p99_bytes`, `max_bytes`, `max_bytes_at_utc`,
  **`bytes_per_packet`** (measured, 1,063-1,069 on this stream — not the
  1,188 an `pkt_size=1200` maximum would suggest, because the last packet
  of a frame is partial), `byte_cap`, `frames_over_cap`, and the
  whole-session `packet_histogram` and `byte_histogram`.

**`companion/native_stream.py`**
-> `21874eefc66692b44f313bb25d3fd1a297ab30138a5b0ffb5f5ec63c01e1e9f3`
(was `caa4c70486ff8255a92ba14c1a9bfc3cf4479468dc45af65bad5d8cb2ed8c670`).

- Two diagnostic encoder overrides, **both DEFAULT OFF**, read from the
  environment at command-build time so a companion restart is the only
  thing needed to change arms (the `D-BASE-P3` pattern):
  **`PRIVYHUB_ENC_MAX_FRAME_SIZE`** (bytes, appends
  `-max_frame_size N`) and **`PRIVYHUB_ENC_BUFSIZE_K`** (kbit, overrides
  `-bufsize`, which otherwise tracks `-maxrate` at 7000k).
  `_env_int` treats anything unparseable as unset rather than raising: a
  malformed diagnostic knob must not stop a stream starting.
- `encoder_overrides()` reports which are in force, and `status()` gains
  **`encoder_command`** — the argv actually used for the running encoder,
  so an arm is *confirmed* before a hold rather than inferred. The argv is
  also written to the encoder log at launch.
- The argv is cleared on stop.

**Verified byte for byte**: with neither variable set, the built command is
identical to the pre-P6 command, and identical again after the variables
are set and removed. The `D-BASE-P6` run confirmed this in the live system
by diffing `encoder_cmd_A0r2.txt` against `encoder_cmd_A0.txt`.

## Cost

The byte accumulation is one `len()` and one add per packet inside the
`RLock` the packet counting already held. `P5` measured that path at
**0.36 us per packet**; `P6`'s seven 20-minute sessions show encoder CPU
**26.6-26.9 %** median and relay `send_errors` **0** in every arm, i.e.
nothing that rises above the noise.

## Validation

**`evidence/d_base_p6_2026-09-21/test_frame_bytes.py`** — 8 groups over
synthetic RTP, no socket and no thread: payload summed per frame with the
RTP header excluded; percentiles as bucket upper edges (including the case
where the 90th percentile frame is still a small one); no cap giving
`byte_cap: None` and `frames_over_cap: 0`; a cap counting only the frames
above it, per second and per session; a malformed cap reading as no cap;
the histogram overflowing into its last bucket while `max_bytes` stays
exact; and the `P5` packet counters untouched. **All pass**, and
`d_base_p5_2026-09-21/test_frame_sizes.py` still passes unchanged.

**Runtime**: seven 20-minute arms plus three smokes, ~508,000 frames
counted, 0 log errors, 0 send errors. The knobs were shown to bite in 60 s
smokes before any arm was spent: `-max_frame_size 40000` took the maximum
frame from 142,517 to **39,745 bytes**; `-bufsize 117k` took it to
**17,254**.

`git diff --check` clean. Python compiles.

## Not done

- **No client change.**
- **No forwarding change**; pacing default stays 0.
- **Nothing adopted.** Both knobs default off and the run ended with the
  default in force, confirmed by argv diff and a `status` read.
- No retention change — the frame-size log is the one `P5` created.

Record: `evidence/D_BASE_P6_FRAME_TAIL_CONTROL_2026-09-21.md`.
