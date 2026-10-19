---
memory_schema: 1
as_of: 2026-10-18
baseline_commit: f9a8260 (CL-B4 committed; the tree carried only the user's prompt and this task file)
---

# CL-B5 — the Opus decode off the receive thread, and the paired A/B

**Classification: both runs VALID; every host gate HELD in both. The new APK `043891e1…1607` is INSTALLED and
CONFIRMED. `PRIVYHUB_AUDIO_CODEC=opus` is NOT ADOPTED (the user's call). Nothing committed.**

- **Paired on one evening, the same PS1 title, the same seven lines and the new APK.** A ran PCM 2/4 with no drop-in;
  B ran Opus, 5 min later.
  - **Underruns: A 19, B 11.** B is under D-BASE-P10's ≤ 20 (CL-B4: 40, with the decode on the receive thread).
  - **The wire, paired:** the LAN interface carried **−2,909.5 kbit/s and −200.7 packets/s** in B against A. The
    prediction was −2,908.8 and −200.
  - **Net audio loss:** A 27 PCM packets (135 ms; 11.6 ms/min); B 30 Opus frames given up (300 ms; 25.8 ms/min).
    That is about the same number of holes, each twice as long (2.32 / 2.58 per min). Recovered by the copy: 441 /
    155.
  - **The decode thread:** queue depth max 19 frames, queue wait max 185.5 ms, 0 drops. The codec call is unchanged
    (avg 3.2 ms, max 102 ms), but the socket read no longer waits on it.
  - **Video:** decoder spikes ≥ 20 ms **144/min in B against 100/min in A**, max output gap 227 against 180 ms. B is
    still higher on the same evening: the CL-B4 finding stands, smaller (CL-B4: 178 against CL-B3's 87).
- **The user's reports, verbatim:** A, "Sound is fine". B, "Run B nothing is running so I can't determine sound" —
  given after B had ended, so **B has no listen** (§4).
- **Run L, the listen** (the user asked: "Yep I'd like to hear"): one more Opus session, the same as B, 2026-10-19
  00:16-00:28Z. It was VALID, every host gate held, and the user said, while it played: **"No visual or audio
  problems"**. Its numbers repeat B's (§4a).

Task: `handoffs/CL-B5_OPUS_DECODE_THREAD_AND_AB_TASK.md`, session A. Pre-registration:
`cl_b5_2026-10-18/cl_b5_preregistration.txt`, sha256 `09e0ea93…19ea3`, hashed at 23:24:04Z, before any code edit
and before the build (23:25Z).

## 0. Precondition (23:23Z)

`check_start.json`, `client_start.json`:
- the seven lines; `--check` ok (adb to the onn); APK `8e10497e…` CONFIRMED;
- no `e3_flag.conf`, no game;
- one device paired, the client's id in the hub's store; `identity_v2` on;
- HEAD `f9a8260`. The tree carried the user's `_cowork_prompt.txt` and the task file, which were not touched.

## 1. The changes

**Client** (`client.diff`; the receiver's hunks are in `receiver_hunks.txt`):
- **New `streaming/OpusDecodePipeline.kt`:**
  - a bounded queue (64 items, about 640 ms) and one decode thread, with the decoder and the sink injected;
  - the receive thread offers what `OpusReorder` releases (a frame, a given-up frame, an outage's concealment) in
    order, and never waits: if the queue is full, the item is dropped and counted;
  - the decode thread makes the MediaCodec on its first frame and releases it at its end. It decodes, splits and
    conceals in queue order, so for an Opus session it is the PCM queue's only producer.
- **`OpusAudioDecoder` implements the pipeline's `FrameDecoder`.** Its decode is unchanged.
- **`NativeAudioReceiver`:** `receiveOpus` offers to the pipeline instead of decoding inline. The Opus state,
  the snapshot's Opus fields and the end-of-loop release changed with it. **The PCM path is unchanged:** no hunk
  touches the version-1 receive path, `enqueuePacket` or the playback loop.
- **The session report's `opus` object gains** `decode_queue_depth_max`, `decode_queue_wait_max_us`,
  `decode_queue_drops` and `decode_failures`. `decode_max_us` is kept: the codec call itself.

**Host, one line, disclosed** (B's file; `host.diff`): `companion/audio_codec.py` `note_setup` records the overlay
host for `sig_v` in (2, 3), with bool still excluded. This closes CL-B4 §4.3. The new test
`test_overlay_host_with_sig_v3`: a v3 setup over the overlay records both hosts, an overlay-class start prepares Opus,
and `sig_v` true / 4 / "3" record no overlay host.

**Tests:**
- APK: `./gradlew --offline :app:testDebugUnitTest --rerun :app:assembleDebug` gave **67 / 67** (`tests_apk.txt`).
  - New: `OpusDecodePipelineTest` (5): the order kept, with concealment and crossfade interleaved; 20 offers return
    in < 200 ms while the decoder blocks (8-9 accepted, the rest dropped and counted, depth max 8); a failed decode
    concealed and counted; no decoder means concealment; stop releases the decoder and ends the thread.
  - The existing streaming tests (`OpusFramingTest`, `FecRs82Test`, `DecoderReportUploadTest`) are unchanged
    (`git diff` empty) and green.
- Host (`tests_host.txt`): overlay **17**, session_identity **88**, audio_codec **20** (19 + 1): all OK.
  `test_c3_l4_nft_night` OK (`tests_nft_night.txt`). No file in `logs/` was written by the tests.

## 2. Build, pin, install

- APK sha256 **`043891e1cc7d643dc496eb6f6dcef50472418e9444300f667ac6abb7d0201607`** (9,810,323 B).
- The rollback was preserved first: `PrivyHub/app/build/cl_b5_preserved/app-debug.apk` = `8e10497e…` (CL-B4).
- `adb install -r` at 23:26Z: `Success`. The device read back `043891e1…`.
- **Paired:** the secret and prefs are present, the client's id is in the hub's store, and the store holds 1
  device (`client_after_install.json`).
- Pinned (patch `CL-B5_DECODE_THREAD_APK_HASH`, `cl_b5_hash.diff`): `EXPECT_APK`, `ADOPTED_APK_SHA256` and its
  test. `--check` gave ok, CONFIRMED.

## 3. The paired A/B (`runs/`, one suite invocation; `cl_b5_analysis.py` → `cl_b5_verdict.json`)

- **The plan:** `E1-PS1-STREAM:1:120,E1-PS1-STREAM:1:300:PRIVYHUB_AUDIO_CODEC=opus`, window 600 s, `--e2`.
- **A:** no drop-in. PLAYING at 23:29:34Z (3.1 s; the suite's stream-start wait reported `attempt: 2`). Window
  23:31:04-23:41:04Z.
- **The gap:** B's drop-in written, restart, eight lines (`environ_run_b.txt`), 300 s idle.
- **B:** PLAYING at 23:46:54Z (3.1 s). Window 23:48:24-23:58:24Z.
- **Teardown:** the drop-in removed, restart, `flags_absent` true, seven lines, `--check` ok, APK `043891e1…`
  CONFIRMED (`check_end.json`).
- **The order was fixed, A then B, not randomised.** This is disclosed.

| | **A — PCM 2/4** | **B — Opus** |
| --- | ---: | ---: |
| RetroArch fps (gate ≥ 59.9) | **59.999** ✓ | **59.999** ✓ |
| capture fps (gate 60 ± 0.1) | **59.998** ✓ | **59.998** ✓ |
| dup+drop / min (gate ≤ 0.2) | **0.10** ✓ | **0.10** ✓ |
| `flags_absent` after (gate) | **true** ✓ | **true** ✓ |
| rung kbps | 7000 | 7000 |
| **underruns** (session report / heartbeat window; P10's ≤ 20 of interest) | **19** / 17 | **11** / 7 |
| net audio loss | 27 × 5 ms = 135 ms (11.6 ms/min) | 30 × 10 ms = 300 ms (25.8 ms/min) |
| holes / min (sequences neither copy of which arrived) | 2.32 | 2.58 |
| recovered by the copy | 441 | 155 |
| arrival holes > 15 ms (not comparable one to one, CL-B4 §3) | 9,635 (829 / min) | 10,864 (935 / min) |
| queue residence avg / max | 65.3 / 106 ms | 57.5 / 145 ms |
| stale drops / concealed underruns / prolonged starvation | 868 / 869 / 110 | 1,001 / 953 / 120 |
| decode queue depth max / wait max / drops | — | **19 / 185.5 ms / 0** |
| decode call avg / max; drain timeouts; decode errors | — | 3,161 µs / 102,342 µs; 4; 6 |
| decoder spikes ≥ 20 ms (session; per min) | 1,167 (100.4) | 1,673 (144.0) |
| decoder spikes ≥ 50 ms | 54 | 51 |
| max output gap (report / telemetry) | 180 / 63 ms | 227 / 80 ms |
| video loss / min | 19.91 | 25.23 |
| rendered fps (heartbeat) | 59.88 | 59.85 |
| host ctrl gaps: > 1 s / max | 0 / 694 ms | 0 / 981 ms |
| **eno1 tx, kbit/s (decimal)** | 11,913.0 | **9,003.5** (−2,909.5) |
| **eno1 tx, packets/s** | 1,378.9 | **1,178.2** (−200.7) |
| host CPU % | 10.29 | 10.10 |
| companion / RetroArch / encoder / Xorg, % of a core | 24.76 / 34.39 / 36.18 / 9.64 | 21.25 / 34.10 / 36.76 / 9.78 |

- **The saving, paired:** −2,909.5 kbit/s and −200.7 packets/s against the eno1 prediction of −2,908.8 / −200 (PCM
  400 × 1,018 B against Opus 200 × 218 B, with Ethernet's 14 B). That is within 0.03 %. CL-B4's +1.5 % residual was
  the unpaired days.
- **Underruns:** B is 11, under ≤ 20 and below A. The move off the receive thread did what CL-B4 §4.1 proposed.
  - The codec call is as slow as before (3.2 ms average, 102 ms at most), and the decode thread fell up to
    185.5 ms behind once (19 frames queued).
  - The PCM queue's capacity then trims the backlog: stale drops 1,001 against 868.
  - No item was dropped.
- **Loss:** about the same holes per minute (2.32 / 2.58), each twice as long in B. G4-W2's prediction was the same
  ms and half the holes. One evening is not enough to tell.
- **Video:** B's decoder spikes are +43 % over A's on the same evening (144 against 100 / min), and its max output
  gap is 227 against 180 ms.
  - With the decode now off the receive thread, the remaining candidate is the onn's CPU shared with the Codec2
    thread, not located.
  - The onn's CPU was not read: the task allows it only "if adb reads it", and nothing beyond the state reads was
    attempted.
- **Validity** (`validity.json`, `audit_runs.jsonl`, `journal_codec_lines.txt`):
  - both runs PLAYING;
  - every `token_issued` at `sig_v` 3 with `audio_codecs` opus (23:29:11, 23:29:21, 23:41:22, 23:46:40, 23:58:43Z);
  - **A on PCM:** 298 heartbeats `audio_codec=pcm`, 0 `opus`, and no Opus line from A's companion;
  - **B on Opus:** the journal's single `opus 128 kbit/s, 10-ms frames` line at 23:46:48Z (B's start); 299
    heartbeats `opus`, 0 `pcm`; the report's `codec: opus`;
  - no refusal.

## 4. The user's reports (verbatim; nothing perceptual is a gate)

| run | at (UTC) | the user's line |
| --- | --- | --- |
| A — PCM | 23:36:15Z (mid-window) | "Sound is fine" |
| L — Opus (the listen, §4a) | 2026-10-19T00:19:32Z (mid-window) | "No visual or audio problems" |
| B — Opus | 2026-10-19T00:12:43Z (after B ended at 23:58:57Z) | "Run B nothing is running so I can't determine sound" |

(`user_reports.tsv`)

- B's line was asked for at 23:59Z, after its teardown. **No listen of B was taken**, so the A/B has no perceptual
  comparison.
- Nothing was rerun: the pre-registration says no rerun unless the user says.
- A listen of Opus needs a session the user hears while it plays. That is the user's option (CURRENT.md, Next
  Action).

## 4a. Run L — the listen of Opus (2026-10-19)

- **Why:** B had no listen. The user then asked to hear Opus ("Yep I'd like to hear").
- **The addendum** was written and hashed before the run: `cl_b5_listen_preregistration.txt`, sha256 `c1a32df5…7a44`,
  00:13:52Z. The precondition read ok at 00:13Z (`check_before_listen.json`).
- **The run:** one E1-PS1-STREAM `--e2 --window 600`, the same title and the same drop-in as B (`runs_listen/`,
  `runs_listen_console.log`).
  - PLAYING at 00:16:35Z (7.1 s; the suite's stream-start wait `attempt: 2`). Window 00:18:05-00:28:05Z.
  - Teardown: the drop-in removed, restart, `flags_absent` true, seven lines, `--check` ok on `043891e1…`
    (`check_end_listen.json`).
- **Valid** (`validity_listen.json`):
  - PLAYING;
  - `token_issued` at `sig_v` 3 with `audio_codecs` opus (00:16:07Z, 00:16:17Z; `audit_listen.jsonl`);
  - the journal's Opus line at 00:16:24Z, and 348 heartbeats `opus`, 0 `pcm` (`journal_codec_lines_listen.txt`).
- **The user, verbatim, while it played (00:19:32Z): "No visual or audio problems".**
- **Its numbers, beside A** (`cl_b5_listen_analysis.py` → `cl_b5_listen_verdict.json`). They are not paired: L ran
  35 min after A. Each item reads L, then B in brackets:
  - **host gates:** RetroArch 59.999, capture 59.999, dup+drop 0.1 ✓;
  - **underruns 13** (B 11; A 19);
  - net loss 28 frames = 280 ms (23.9 ms/min; 2.39 holes/min), 81 recovered;
  - **decode queue depth max 20, wait max 86.5 ms, 0 drops**; the decode call avg 3.1 ms, max 45.5 ms;
  - residence avg / max 58.1 / 94 ms;
  - decoder spikes ≥ 20 ms 1,598 (136.7 / min; B 144, A 100); max output gap 310 ms; video loss 48.5 / min;
    1 resync; one host ctrl gap of 1,007 ms;
  - eno1 9,005.6 kbit/s, 1,178.2 pkt/s (−2,907.4 / −200.7 against A);
  - companion 21.33 % of a core, encoder 36.68.
- **Read plainly:**
  - L repeats B: underruns under 20, the same wire saving, and the decode queue bounded with no drops.
  - The user heard no visual or audio problem in it.
  - The video spikes over A's are in L too, and they were not perceived.

## 5. State at the end (2026-10-19 00:29Z, after run L; first written 23:59Z after B)

- **Seven lines; no `e3_flag.conf`; no game; APK `043891e1…` CONFIRMED; `--check` ok** (`check_end.json`,
  `check_end_listen.json`).
- One device paired; the client set up again after the teardown restart at `sig_v` 3.
- Nothing adopted; nothing committed (`logs/cl_b5_git_status.txt`).

## 6. Files

**`cl_b5_2026-10-18/`:**
- the run's context: `baseline_head.txt`, `git_status_at_start.txt`, the pre-registration, its hash and the time
  it was hashed;
- the code: `predecessors/`, `predecessor_sha256.txt`, `after_sha256.txt`, `client.diff`, `host.diff`,
  `receiver_hunks.txt`, `diffstat.txt`, `cl_b5_hash.diff`;
- the tests and build: `tests_apk.txt`, `tests_host.txt`, `tests_nft_night.txt`, `build_console.txt`,
  `build_started_at.txt`;
- the install: `apk_sha256.txt`, `rollback_apk_sha256.txt`, `install.log`, `install_at.txt`, the `client_*.json`
  reads (CL-B4's `cl_b4_client_read.py`), the `check_*.json` readings;
- the runs: `runs/` (`suite.log`, `E1-PS1-STREAM/run1` = A, `E1-PS1-STREAM_flag/run1` = B), `runs_console.log`,
  `run_launched_at.txt`, `audit_offset_before_run.txt`, `environ_run_b.txt`;
- the readings: `audit_runs.jsonl` (no id, token or address), `journal_codec_lines.txt` (host name and addresses
  masked), `user_reports.tsv`;
- the analysis: `cl_b5_analysis.py`, `cl_b5_analysis_console.json`, `cl_b5_verdict.json`, `validity.json`;
- `redact_check.py`, `redact_check.txt`, `manifest.sha256`.

**Elsewhere:** `PrivyHub/app/src/test/java/streaming/OpusDecodePipelineTest.kt`; `tests/audio_codec/test_audio_codec.py`
(+1 test); patch `patches/CL-B5_DECODE_THREAD_APK_HASH.md`; CL-B4's §5 completed; `logs/cl_b5_git_status.txt`.

No sudo, no nft, the Opal untouched. adb was used only for the install and the state reads. Nothing fetched (the build
ran `--offline`), nothing deleted.
