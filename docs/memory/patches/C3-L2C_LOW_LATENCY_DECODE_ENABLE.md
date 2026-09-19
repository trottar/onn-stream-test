---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 41bbc6acd3534f79283e328596115a02c3acc296
durable_memory_updated: true
---

# C3.L2c — low-latency MediaCodec decode enable

## Purpose

`C3.L2b` telemetry (`evidence/C3_L2A_E2_ACTUATOR_IDR_RESOLVED_2026-09-18.md`)
showed `low_latency_enabled` false on `c2.realtek.video.avc.decoder`,
`max_codec_ms` 367, and the session's two worst output gaps (359 ms, 352 ms)
tracking `codec_ms` to within 8 ms at `feed_delay_ms` 0. Decoder time on a
single frame was the largest measured contributor to perceptible
interruption — larger than anything the `C3.L2` actuator does.

`AvcLowLatencyDecoder`'s `init` already requested `MediaFormat.KEY_LOW_LATENCY`
when `codec.codecInfo.getCapabilitiesForType(...).isFeatureSupported(FEATURE_LowLatency)`
returned true, but this decoder's own capability query never reported
support, so the request was never made. `KEY_LOW_LATENCY` is a `MediaFormat`
hint, not a negotiated contract — a decoder that does not implement it is
expected to ignore it. This patch drops the capability gate and requests the
key unconditionally on API >= R.

## Expected predecessor

- `PrivyHub/app/src/main/java/streaming/AvcLowLatencyDecoder.kt`:
  `22038e355f85bb8330d900bae64c37db54c902d4affdef12be4810bb03271c07`
- `docs/memory/CURRENT.md`:
  `43b40885dc078cdad286928154d149dbd6eaf48ea771c5c87ed2df53b81b07cd`

## Changed scope

Changed: the `init` block in `AvcLowLatencyDecoder.kt` (removes the
`getCapabilitiesForType` / `isFeatureSupported(FEATURE_LowLatency)` gate and
the now-unused `MediaCodecInfo` import; requests `KEY_LOW_LATENCY`
unconditionally on `Build.VERSION.SDK_INT >= Build.VERSION_CODES.R`).
`docs/memory/CURRENT.md` (Current Work Item, Verified State, Next Action,
Relevant References). Generated: `docs/memory/patches/PATCH_INDEX.md`.

Unchanged: resolution, frame rate, GOP, B-frames, FEC wire format, RTP
payload type, packet size, ports, process audio, controller transport,
emulator lifecycle, the decoder's input/output loop, metrics collection, and
`slow_events_marked` (that defect stays a separate item — not folded in
here). `docs/memory/PHASE_C_CONTEXT.md` unchanged by this patch.

## Validation performed

- per-file predecessor SHA-256 verification before any write;
- wrong-state rejection: refuses to run if this record already exists at its
  target path;
- backup of every changed file under `archive/patch_backups` before write;
- installed-file SHA-256 verification after write;
- `git diff --check`;
- the real `sh ./gradlew :app:assembleDebug --no-daemon` — the first actual
  compile against the Android/Activity framework;
- `tools/check_memory_health.py` as a post-write gate;
- exact-byte rollback of every changed file if any gate above fails.

**Deliberately not performed:** no installer self-test, no synthetic
fixture, no stub compiler, no mock Android framework, per
`AGENTS.md`'s execution budget and `PATCH_PROTOCOL.md`'s Tier 1 rule — this
is an ordinary change the real build validates. The predecessor hashes and
the real gradle build decide it, on the user's machine.

**Not performed, and explicitly out of scope for a decision:** runtime /
gameplay validation. This patch changes production client behavior and
needs its own focused gameplay acceptance from the user before `C3.L2c`
closes. A passing build is not that acceptance.

## Result

**ROLLED BACK** — 2026-09-19, after runtime acceptance.

Installed 20260919T034939Z, predecessor `22038e355f85bb8330d900bae64c37db54c902d4affdef12be4810bb03271c07` -> installed `dd67acfe8d9da918c21cd0767114956843a6c320091df979e0bc108af6e906e7`. Real build passed and the APK was rebuilt and reinstalled (`adb install -r`, device API level 34).

Runtime evidence, decoder session `native_decoder_20260919_042611_053.json` (2026-09-19T04:26:11Z, duration 55,333 ms), compared against the pre-patch `C3_L2A_E2` baseline:

| metric | baseline | this session |
|---|---:|---:|
| `low_latency_enabled` | false | true |
| `max_codec_ms` | 367 | 107 |
| `spike_250_ms` count | — | 0 |
| **`max_output_gap_ms`** | **359** | **385** |

Single-frame decode time improved sharply (367 -> 107 ms, `spike_50_ms` events down from a 64-per-session norm to 19). The worst-case output gap — the actual perceptible stall — got worse (359 -> 385 ms), and the user's subjective report ("gameplay was trash") matched the regression, not the improvement.

Source restored to its exact predecessor bytes by reversing the recorded diff and verifying the result against the predecessor SHA-256 above (match confirmed) before committing. The capability-gated `KEY_LOW_LATENCY` request (`FEATURE_LowLatency` self-report, false on this decoder) is back in place.

**Negative result.** Faster single-frame decode does not imply a shorter worst-case stall on `c2.realtek.video.avc.decoder`; the mechanism linking them is unknown. Do not retry the unconditional `KEY_LOW_LATENCY` request without new evidence explaining the `max_output_gap_ms` regression.

**Outstanding:** the rebuilt/reinstalled APK on the device currently runs the reverted (capability-gated) source only once it is rebuilt and reinstalled again — confirm with a fresh decoder-report session before treating the revert as runtime-verified.
