---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
durable_memory_updated: true
---

# D-BASE-P1 — stale-output threshold probe knob

## Purpose

`AvcLowLatencyDecoder` dropped any decoded frame whose receive-to-output
latency exceeded a hard-coded `60L`. Group A measured that rule as the cause
of the 3.5 fps gap between received-AU fps and rendered fps, and nobody had
measured what it buys or costs. This makes the threshold settable for a
characterization probe **without changing the product default**, and adds
the histogram the question actually needs.

The measurement is `evidence/D_BASE_P1_STALE_THRESHOLD_2026-09-20.md`.
Nothing is accepted or changed by it.

## Expected predecessor

- `PrivyHub/app/src/main/java/streaming/AvcLowLatencyDecoder.kt`:
  `375516b6d50fe3f069fd8befeb693ea7d20cd92f2d59e73bd98c32b613458485`
- `PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt`:
  `4ba8a7a659ef22d82e1a34323134739dfa60b74656a475adac2c7046ca57aff9`
- `PrivyHub/app/src/main/java/MainActivity.kt`:
  `983223ab247b88a23f191649073968a9f8bb56ca07c3e26007dbf411933c0629`

## Changed scope

**`AvcLowLatencyDecoder.kt`**
-> `1fcafa837bbcff1210753ffe47477915af9e52717d4a2ce774dda474dc038e81`.
The literal `60L` becomes a constructor parameter `staleOutputMs`
defaulting to `DEFAULT_STALE_OUTPUT_MS` = 60; `staleOutputThresholdMs()`
exposes the value in force. Adds a 10-bucket receive-to-output histogram
over **rendered frames** (20 ms buckets, last bucket > 180 ms),
incremented in the same place the frame is released, with
`rxToOutputHistogramSnapshot()`.

**`NativeStreamActivity.kt`**
-> `4e312415b0a795398067fe35367a98d6383065f7da0639b2c0cbf4434a90deb1`.
New `EXTRA_STALE_OUTPUT_MS` = `"privyhub.stale_output_ms"`, read once per
session by `requestedStaleOutputMs()`; a value outside 16-1,000 ms falls
back to the default, so a typo cannot silently disable the stale policy.
The report's decoder block gains `stale_output_ms`,
`rx_to_output_histogram_ms` and `rx_to_output_histogram_bucket_ms`.

**`MainActivity.kt`**
-> `a727f5155c5b8279f0c98ce1af4d64796a2c3b87f04ba2dac2b38a504e3c44e9`.
`openNativeGameStream()` forwards the extra into the
`NativeStreamActivity` intent **only when the launcher was itself started
with one**. This is how the value reaches a non-exported activity through
the launch path `TOOLS.md` records; **the companion was not touched and
`games.py` was not used.**

**The product default is 60 and is unchanged.** With the extra absent —
every product launch — the decoder constructs exactly as before and the
drop decision is byte-for-byte the same comparison. The final validation
session, launched with no extra, reported `stale_output_ms` 60.

**Unchanged:** every streaming constant, the decoder configuration, FEC,
transport, the emulator, the recovery state machine, and every existing
report field.

## Validation performed

- `git diff --check` clean; real `sh ./gradlew :app:assembleDebug
  --no-daemon`; `adb install -r`; companion restarted with 8765 checked
  free (D-068);
- a smoke session at 200 ms confirming `stale_output_ms` and the histogram
  reach the report;
- **twelve 90 s attract sessions**, thresholds 60 / 90 / 120 / 200, three
  each, interleaved, zero input, driven per `TOOLS.md`; every report's
  `stale_output_ms` equalled the threshold requested;
- **one final 60 s control session with no extra**, reporting
  `stale_output_ms` 60;
- teardown per `TOOLS.md`.

## Result

**Knob works; the measurement it enabled is a negative result.** Full
record: `evidence/D_BASE_P1_STALE_THRESHOLD_2026-09-20.md`.

Zero of thirteen sessions were rejected — none had a sequence resync at
all, and the largest `max_output_gap_ms` was 387 ms against a 1,000 ms
reject line.

| threshold | rendered fps | received-AU fps | stale/min | rendered frames > 60 ms |
| ---: | ---: | ---: | ---: | ---: |
| **60 (default)** | **59.65** | 59.83 | 9.3 | **0.000 %** |
| 90 | 59.56 | 59.67 | 3.1 | 0.143 % |
| 120 | 59.06 | 59.41 | 1.1 | 0.175 % |
| 200 | 59.27 | 59.39 | 0.0 | 0.279 % |

**The threshold has almost nothing left to do.** At 60 ms it discarded 6,
17 and 15 frames in three ~97 s sessions, so recovering every one of them
would add **0.06-0.18 fps** — a bound that needs no cross-arm comparison.
Raising the threshold recovers no fps in the medians, moves p50 and p90 of
rendered-frame latency not at all (both <= 20 ms in every arm), and shows up
only at p99.9 (<= 40 ms at the default, <= 120 ms at 200). `max_output_gap_ms`
shows no trend, as expected for a transport-owned tail.

**The premise is retired, with a date on it.** Group A's 3.5 fps
client-side deficit was measured before `C3.L2c`; on the current build the
deficit is 0.11-0.35 fps and 98.4 % of rendered frames are under 20 ms.
The stale policy is not costing fps on a healthy link.

**Confound, named in the record:** the interleave repeated a fixed
60 → 90 → 120 → 200 order, so each threshold always sat in the same cycle
position. The `spike_20_ms` arm differences (67.5 to 204.5 per minute) come
from that, not from the threshold — the counter is incremented before the
drop decision and cannot respond to it. Rotate the order in any re-run.

**Limits:** thirteen idle attract sessions on a quiet link with zero
resyncs, n = 3 per arm, no perceptual observation. On a session with real
transport trouble the policy may have much more to do; this characterizes
it on a healthy link on the current build, and nothing more.

**The knob stays in the tree** as a diagnostic with the product default.
