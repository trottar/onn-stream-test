---
memory_schema: 1
as_of: 2026-10-18
baseline_commit: f314126 (tree clean at the start)
---

# CL-B4 — the APK's Opus decode, and the first Opus session

**Classification: VALID; every host gate HELD; the new APK `8e10497e…d84e` is INSTALLED and CONFIRMED. The flag
`PRIVYHUB_AUDIO_CODEC=opus` is NOT ADOPTED (the user's call). Nothing committed.**

- **The first live Opus session** (one E1-PS1-STREAM `--e2 --window 600` on the LAN, 22:04:24-22:14:24Z):
  - PLAYING in 6.1 s. `token_issued` carried **`sig_v` 3, `audio_codecs` opus**. The companion logged
    `opus 128 kbit/s, 10-ms frames, libopus 1.5.2`, and 347 heartbeats echoed `audio_codec=opus` (0 `pcm`).
  - **The wire, as predicted:**
    - the audio sender ran **200.1 datagrams/s** (100.0 originals + 100.0 copies), which is **326.5 kbit/s** at the
      design's 204-B datagram;
    - **the LAN interface carried −2,951.5 kbit/s and −227 packets/s** against CL-B3 R1 at the same 7000 rung. The
      prediction on eno1 is −2,908.8 and −200.
  - **Audio:** 69,835 Opus frames decoded, **0 net lost** (68 recovered by their copy, 0 abandoned), against CL-B3
    R1's 132 net lost PCM packets (56.8 ms/min).
  - **Underruns 40, against CL-B3 R1's 9** (D-BASE-P10: 0 / 13; that task's bar was ≤ 20). The client's decode
    averaged **3.3 ms per frame, with a maximum of 84 ms**, synchronous on the receive thread: the likely cause, not
    proven (§4).
  - **Video:** decoder spikes ≥ 20 ms **178/min against CL-B3 R1's 87** (under the 200 bar); max output gap 501 ms
    against 410. The cause is not located (§4).
- **The user's listen:** *pending* — see §5.

Task: `handoffs/CL-B4_APK_OPUS_DECODE_TASK.md`, session A. Pre-registration: `cl_b4_2026-10-18/cl_b4_preregistration.txt`,
sha256 `afa3b96d…3a97`, hashed at 20:37:13Z, before any code edit and before the build (20:44:29Z).

## 0. Precondition

At 20:32Z: the seven lines, no `e3_flag.conf`, no game, the companion active, HEAD `f314126`, the tree clean.
`tools/e3_state.py --check` read **ok false on adb only**: adb was not connected after G4-S2's network change, and
`apk MISMATCH` followed from that (`check_start.json`).
- The user was asked to reconnect, and the offline part (code, tests, build) went on meanwhile.
- After the reconnect, at 21:58:29Z: ok, APK `59f736d2…` CONFIRMED (`check_before_install.json`).

## 1. The changes

**Host: `companion/session_identity.py`, sig_v 3** (`host_sig_v3.diff`; +26 / −4):
- `sig_v` 3 is v2's seven lines under `privyhub-session-setup-v3`, plus an eighth line, `audio_codecs` joined by
  `,`.
- `audio_codecs` is required under v3: a list of 1-8 strings `[a-z0-9]{1,16}`. A v3 claim without it, or with a
  malformed one, is refused (403 `audio-codecs-invalid`), and a tampered list fails the signature.
- `token_issued` for v3 carries `sig_v` 3 and `audio_codecs`. A v1 / v2 row gets no new key.
- **v1 / v2 byte for byte** (`v2_compare.json`). HEAD's module (`tests/session_identity/fixtures/session_identity_predecessor_cl_b4.py.txt`)
  and the edited one ran the same scenarios: 18 setups (accepted, tampered, invalid ports, overlay, unknown device
  and nonce, `sig_v` "3" / 4 / true under v1), with `secrets` made deterministic in both.
  - All 37 answers were equal, and the 19 audit rows were equal (sha256 `ed74b2fe…bd98` on both sides).
  - G3-S1's handler replay (`test_handler_replay.py`) passes on the edited module.

**Client: the debug APK** (`client.diff`). These are the seven items of G4-W2 §5.1:

1. **Setup:** `IdentitySession` signs v3 with `audio_codecs: ["opus"]`, declared always (under `identity_v2`, as
   setup is). If a host that predates v3 answers 401 `bad-signature`, the client gets one fresh nonce and sends
   today's v2 body, byte for byte (logged; `lastSigV` 2). This is what let the `-r` install talk to the
   pre-restart companion. In practice the client made no call before the restart, so it was never used live.
2. **PHA1 version 2 accepted** in `NativeAudioReceiver`: 2 channels, frames 240 / 480 / 960, payload 1-1,500 B,
   de-duplicated by sequence in today's 64-sequence window. The version-1 path is unchanged, except for one line
   that records the codec.
3. **MediaCodec `audio/opus`** (new `OpusAudioDecoder.kt`): synchronous, on the receive thread, so the queue keeps
   its one producer. The csd buffers:
   - csd-0 is the OpusHead (v1, 2 ch, pre-skip 120, 48 kHz, gain 0, family 0);
   - csd-1 is the pre-skip, 2,500,000 ns;
   - csd-2 is the seek pre-roll, 80,000,000 ns;
   - both ns values are 8-byte longs in native order.

   The device chose `c2.android.opus.decoder`.
4. **Concealment:** frames are decoded strictly in sequence order (new `OpusFraming.kt` `OpusReorder`).
   - A missing frame holds the frames after it until its copy can no longer come: a frame more than *k* = 2 ahead
     has arrived (the host sends the copy of n after the original of n + k).
   - It is then given up and becomes 2 of today's concealment slots (the continuity packet and the crossfade).
   - A jump of ≥ 64 sequences gets today's cap and crossfade.
5. **The split:** each decoded output becomes 240-frame packets for today's queue. An output that is not a whole
   number of them (the pre-skip's first, 360 frames) is left-padded with silence.
6. **Holes per 10 ms:** with Opus, `lost_packets`, `sequence_gap_*`, `recovered_by_duplicate` and `late_unplaced`
   count Opus frames.
7. **The codec in the reports:** the session report's audio block carries `codec` and an `opus` object (frames
   decoded / abandoned, decode errors, drain timeouts, max held, decode time, the decoder's name, *k*). The
   heartbeat query carries `audio_codec`, and the host's whitelist drops it, so it is visible only in the access log.

**Tests:**
- APK: `./gradlew --offline :app:testDebugUnitTest --rerun :app:assembleDebug` gave **62 / 62**
  (`tests_apk.txt`, `build_console.txt`). New:
  - `SessionProtocolV3Test` (4): three host-accepted vectors from `make_vectors_v3.py`. Each body, in the exact form
    `setupBodyV3` writes, was parsed and accepted by `SessionGate._setup` in process.
  - `OpusFramingTest` (12): the csd bytes, the copy offset against the host's, the split and pad, the reorder rule,
    and the host's send pattern under seeded loss of 1 / 5 / 20 % (in order, once each, given up only when both
    datagrams were lost).
  - `IdentitySessionTest` +2: v3 declares opus; a host without v3 gets today's v2 once.
- Host (`tests_host.txt`): overlay **17**, session_identity **88** (80 + 8 new), audio_codec **19**: all OK.
  `tools/test_c3_l4_nft_night.py` **33 / 33**. No file in `logs/` was written by the tests.

**Not touched:** `companion/audio_codec.py` and B's other G4-W1 / G4-W2 / G8-S4 work. The tree was clean at the
start, since those were committed in `f314126`.

## 2. Build, pin, install

- APK sha256 **`8e10497ef43850d54165593a680f68a41b89114536a806f0788b9a04945fd84e`** (9,810,323 B; `apk_sha256.txt`).
- **The rollback was preserved before the build:** `PrivyHub/app/build/cl_b4_preserved/app-debug.apk` =
  `59f736d2…f65f` (CL-B3's; `rollback_apk_sha256.txt`).
- `adb install -r` at 21:59Z: `Success` (`install.log`). The device read back `8e10497e…`
  (`client_after_install.json`).
- **The pairing survived:** the device secret and the prefs are present, the client's id is in the hub's store
  (compared in process; only booleans are written), and the store holds 1 device. `identity_v2` is on, and the hub
  host is empty.
- **Pinned** (patch `CL-B4_OPUS_APK_HASH`, `cl_b4_hash.diff`): `tools/e1_suite.py` `EXPECT_APK`,
  `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`, and its test. `--check` gave ok, CONFIRMED
  (`check_after_install.json`).

## 3. The run (`runs/E1-PS1-STREAM_flag/run1`; `cl_b4_analysis.py` → `cl_b4_verdict.json`)

- **The flag:** the suite wrote `e3_flag.conf` = `PRIVYHUB_AUDIO_CODEC=opus` and restarted the companion. The
  environ read eight lines (`environ_with_flag.txt`).
- PLAYING at 22:02:54Z (6.1 s), then the window. At teardown the drop-in was removed, followed by daemon-reload and
  a restart: `flags_absent` true and seven lines.

| | **CL-B4 Opus** | CL-B3 R1 PCM (10-16) |
| --- | ---: | ---: |
| RetroArch fps (gate ≥ 59.9) | **59.999** ✓ | 59.999 |
| capture fps (gate 60 ± 0.1) | **59.996** ✓ | 59.988 |
| dup+drop / min (gate ≤ 0.2) | **0.10** ✓ | 0.10 |
| `flags_absent` after (gate) | **true** ✓ | true |
| rung kbps | 7000 | 7000 |
| host CPU % | 9.99 | 11.57 |
| companion / RetroArch / encoder / Xorg, % of a core | 20.91 / 33.90 / 36.62 / 9.74 | 24.80 / 34.39 / 36.01 / 9.59 |
| eno1 tx, kbit/s (decimal) / packets/s | 8,996.8 / 1,178.1 | 11,948.3 / 1,405.3 |
| rendered fps (heartbeat) | 59.73 | 59.67 |
| video loss / min | 32.66 | 80.05 |
| decoder spikes ≥ 20 / ≥ 50 ms (session) | 2,084 / 91 (178 / min) | 1,010 / 65 (87 / min) |
| max output gap (report / telemetry) | 501 / 77 ms | 410 / 70 ms |
| ctrl gaps > 1 s (host gap log) | 1 (1,704.6 ms) | 0 (max 603.2) |
| **audio codec** | **opus** (480 frames) | pcm |
| audio unique datagrams received | 69,836 | 139,048 |
| **net lost** (unit) | **0** (10-ms frames) | 132 (5-ms packets) = 56.8 ms / min |
| recovered by the copy | 68 | 868 |
| **underruns (session report / heartbeat window)** | **40 / 32** | 9 / 5 |
| arrival holes > 15 ms | 10,495 (899 / min) | 4,034 (347 / min) |
| queue residence avg / max | 55.1 / 143 ms | 68.0 / 95 ms |
| stale drops / concealed underruns / prolonged starvation | 1,427 / 1,360 / 165 | 1,844 / 1,858 / 209 |
| Opus: decoded / abandoned / decode errors / drain timeouts / max held | 69,835 / 0 / 1 / 4 / 3 | — |
| Opus: decode time avg / max | **3,329 µs / 84,041 µs** | — |

**D-BASE-P10 for reference** (B1 / B2, redundancy on, 2026-09-23):
- 28 / 14 lost packets, i.e. 2.77 / 1.38 per minute of 5-ms packets;
- underruns 0 / 13;
- holes > 15 ms 1,924 / 1,895;
- residence 56.9 / 62.2 ms;
- spikes 31-36 / min.

- **The wire:**
  - The sender's counters over 10 s at ~22:03Z read 100.0 + 100.0 datagrams/s.
  - No capture was taken (no sudo), so the per-datagram size is the design's CBR figure (160 B Opus + 16 + 28).
  - The interface closes the arithmetic. With Ethernet's 14 B, PCM is 400 × 1,018 B and Opus 200 × 218 B, a
    predicted −2,908.8 kbit/s. Measured: −2,951.5 (+1.5 %), at −227 packets/s against −200.
  - The two runs are two days apart and are not paired arms (video loss 32.7 against 80.1 / min). The residual is
    reported, not explained.
- **The arrival holes are not comparable one to one:**
  - Opus datagrams are de-duplicated to one per 10 ms (PCM: one per 5 ms), so a gap over 15 ms is 1.5 Opus
    intervals but 3 PCM ones.
  - The receive thread also spends ~3.3 ms decoding per frame, which delays the arrival stamps.
  - The comparable figure is net loss: 0.
- **The +7.5 ms** (Opus framing and lookahead) is upstream of the queue, so it is not in the residence figure
  (55.1 ms, lower than R1's 68.0). The decode's wait is not in it either.
- **CPU:** the companion is 20.91 % of a core, against 24.80 (−3.9 points). The host is 9.99 % against 11.57. The
  encoder is the same (36.6 / 36.0).
- **Validity** (`validity.json`): OK.
  - PLAYING;
  - `token_issued` with `sig_v` 3 and `audio_codecs` opus (`audit_run.jsonl`: 22:02:14Z, 22:02:36Z, and 22:14:42Z
    after the teardown restart, flag absent);
  - no refusal;
  - the Opus line in the journal (`journal_codec_lines.txt`);
  - the client's report `codec: opus`.

  No PCM fallback.

## 4. Findings, not gated

1. **Underruns 40 against 9.** The likely cause, not proven: MediaCodec in synchronous mode on the receive thread.
   - Each frame waits on the Codec2 handoff: 3.3 ms on average and **84 ms at most**, with 4 drain timeouts.
   - While it waits, the socket is not read and the queue is not fed.
   - The next step (a CL-B item): decode off the receive thread, or MediaCodec's async callback with the release
     order kept, then a paired A/B (PCM / Opus on one day).
2. **Decoder spikes 178 / min against 87**, and one 1.7-s host control gap. The cause is not located.
   - It could be the link (the runs are not paired) or the onn's CPU shared with the Codec2 thread.
   - It is under the < 200 bar, but about twice CL-B3.
3. **Off-site:** `audio_codec.py`'s capture (`note_setup`) records the overlay address only for `sig_v` == 2.
   - A v3 client's overlay host is not recorded, so **an off-site Opus start would be refused** (fail closed).
   - It is not fixed here (B's file, not in this task's list). A one-line change (`sig_v` in (2, 3)) is needed
     before the off-site run at 4000 with Opus (`docs/KNOWN_ISSUES.md`).

## 5. The user's listen

*Asked at 22:03Z; not yet answered when this record was written.* It will be recorded here verbatim as the user's
report: audio present, in sync, artefacts. Nothing perceptual is a gate. The user's confirmation that the TV shows the
app paired is also pending; the device read paired at 21:59:09Z and 22:16:57Z.

## 6. State at the end (22:16Z)

- **Seven adopted lines; no `e3_flag.conf`; no game; APK `8e10497e…` CONFIRMED; `--check` ok** (`check_end.json`).
- One device paired, `identity_v2` on, the hub host empty (`client_end.json`). The client set up again after the
  teardown restart at `sig_v` 3.
- Nothing adopted; nothing committed (`logs/cl_b4_git_status.txt`).

## 7. Files

**`cl_b4_2026-10-18/`:**
- the run's context: `baseline_head.txt`, `git_status_at_start.txt`, the pre-registration, its hash and the time
  it was hashed;
- the code: `predecessors/`, `predecessor_sha256.txt`, `after_sha256.txt`, `host_sig_v3.diff`, `client.diff`,
  `cl_b4_hash.diff`;
- the tests: `make_vectors_v3.py`, `setup_vectors_v3.json`, `v2_compare.json`, `tests_host.txt`, `tests_apk.txt`,
  `tests_nft_night.txt`, `build_console.txt`, `build_started_at.txt`;
- the install: `apk_sha256.txt`, `rollback_apk_sha256.txt`, `install.log`, `install_at.txt`, `cl_b4_client_read.py`,
  `client_*.json`, the `check_*.json` readings;
- the run: `runs/` (`suite.log`, `E1-PS1-STREAM_flag/run1`), `runs_console.log`, `run_launched_at.txt`, the log
  offsets, `environ_with_flag.txt`, `audit_run.jsonl` (event, sig_v, codecs, permissions, booleans;
  `paired-device` / `host-local`; no id, token or address), `journal_codec_lines.txt` (addresses masked);
- the analysis: `cl_b4_analysis.py`, `cl_b4_verdict.json`, `validity.json`;
- `redact_check.txt`, `manifest.sha256`.

**Elsewhere:**
- tests: `tests/session_identity/test_cl_b4_sig_v3.py` and its fixture; `PrivyHub/app/src/test/java/identity/SessionProtocolV3Test.kt`,
  `…/streaming/OpusFramingTest.kt`, `…/resources/cl_b4/setup_vectors_v3.json`;
- patch `patches/CL-B4_OPUS_APK_HASH.md`; `logs/cl_b4_git_status.txt`.

No sudo, no nft, the Opal untouched. adb was used only for the install and the state reads (`run-as` cat / ls, `pm
path`, `sha256sum`). Nothing fetched (the build ran `--offline`), nothing deleted.
