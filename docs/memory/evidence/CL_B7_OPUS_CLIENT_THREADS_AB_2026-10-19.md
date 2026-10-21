---
memory_schema: 1
as_of: 2026-10-19
baseline_commit: d3a8ee3
---

# CL-B7 — the Opus path's cost on the client, read per thread, three arms

**Classification: 3 of 3 arms VALID; every host gate held; every read-back held. The candidate APK `93d29b4a…1624` is
installed and now CONFIRMED (arm 2 read as today). The adopted state is unchanged** (the eight lines, Opus adopted, no
`e3_flag.conf`, `--check` ok). Measurement only; nothing adopted; nothing committed.

- **Where the Opus cost sits on the onn** (150 s into each window; Opus today minus PCM):
  - the PrivyHub process **+19.5 % of a core** (91.2 → 110.7);
  - **and `media.swcodec`, a separate process, +11.1 %** (0 → 11.1), where the `c2.android.opus.decoder` runs;
  - **together ≈ 0.31 core.**
  - Of the +31.2 (threads + `media.swcodec`), **the framework side carries 23.1**:
    - `MediaCodec_loop` +9.8: a second looper thread, 1 → 2;
    - binder +2.2 (`HwBinder` +2.0);
    - `media.swcodec` +11.1.
  - **Our own threads carry +7.5:**
    - the `PrivyHub-Native` group +6.8, 3 → 4 threads, the 4th being the Opus decode thread;
    - RTP +1.4 and the video drain −0.7.
  - **By the reading written beforehand: B's hypothesis (the MediaCodec per-buffer machinery) holds.** CL-B6's ~0.2
    core in the process was not overstated (+0.195 here). The process figure misses `media.swcodec`'s 0.11.
- **Lean moved nothing measurable.** Lean minus today:
  - framework codec −0.1, binder 0.0, `media.swcodec` +0.2;
  - the process −0.7 (threads −1.2).
  - The −1/5 of the framework share predicted if the call count were the cost is about −4.6.
  - **By the written reading: the per-call count is not the owner.**
- **Spikes ≥ 20 ms:** PCM 70.1, today 121.0, lean 108.7 per min.
  - Lean sits between today and PCM, a quarter of the way down. **By the letter of the written reading, the spikes
    follow the call count.**
  - That sits against a CPU delta of ~0. With one run per arm, the 12-per-minute difference is stated, not leaned
    on.
  - ≥ 50 ms: 1.98 / 2.41 / 2.58.
- **Underruns** (session / window): PCM 16 / 6, today **25** / 14, lean 12 / 7. Today is 5 over ≤ 20.
- **Decode queue** (depth / wait max): today 45 / 218 ms, lean 15 / 80 ms (CL-B6 today: 20 / 82).
- **The wire:** Opus −2,903 kbit/s against PCM on the LAN interface.
- **The user's lines (verbatim):**
  - arm 1 (PCM): "Sounds fine, maybe small (<1 second) stutter every 20 seconds or so";
  - arm 2 (Opus today): "Sounds good, no stutters noticed";
  - arm 3 (lean): "Sound is good, no stutters" (given after the arm ended, when asked).

- **Task:** `handoffs/CL-B7_OPUS_CLIENT_THREADS_AB_TASK.md`, session A.
- **Pre-registration:** `cl_b7_2026-10-19/cl_b7_preregistration.txt`, sha256 **`b7ac5b3b…f9f2a`**, hashed at 16:55:37Z,
  before the install, with the reading written beforehand.
- **Design and APK:** `CL_B7P_OPUS_CLIENT_COST_2026-10-19.md`. **Reference:** `CL_B6_AB_REPEAT_AFTER_RESTART_2026-10-19.md`.

## 0. Precondition (16:54-16:55Z)

- **The user power-cycled the onn and opened PrivyHub once.**
  - adb was off. It was reconnected by hand with `adb connect`, using the endpoint taken from the companion's journal
    inside one shell command; nothing was printed or written.
  - **Uptime 131 s** at the first read (`onn_reads.jsonl` `precondition`: 148 s).
- **`--check` ok on the eight lines** (`check_start.json`). No `e3_flag.conf`, no game, no G-unit.
- **APK `043891e1…` CONFIRMED;** one device paired, with the client's id in the hub's store (`client_start.json`).
- **`getprop debug.privyhub.opus_decode` empty.**
- **HEAD `d3a8ee3`** (`baseline_head.txt`). The tree carried only the prompt and the task file
  (`git_status_at_start.txt`).

## 1. The install (16:56Z)

- The candidate `/tmp/b_cl_b7p/PrivyHub/app/build/outputs/apk/debug/app-debug.apk` read sha256
  **`93d29b4a38d224fddbcf261dab72b40f1290f009b7dc506d60eb3104071e1624`** (9,600,146 B), equal to CL-B7P §3's pin
  (`candidate_apk_sha256.txt`). The `/tmp` copy was present, so no rebuild was needed.
- `adb install -r`: `Success` (`install.log`, `install_at.txt`).
- **The device read back `93d29b4a…`. Paired:** the secret and prefs are present, and the client's id is in the hub's
  store, which holds 1 device (`client_after_install.json`).
- **The thread script's parser was checked before the arms,** on a running system process's `top -H` and the process
  `top`, both state reads. It returned 2 iterations, 23 threads, the process names matched and the busy % parsed.
  **No parser patch was needed;** the first PrivyHub read (arm 1 +150 s) parsed 10 kept iterations.

## 2. The arms (`cl_b7_arms.py` → `arms_console.log`, `arms.jsonl`, `runs/<arm>/`)

Each arm was one suite invocation: `tools/e1_suite.py run --prereg cl_b7_preregistration.txt --plan … --window 600
--e2`, on the same PS1 title. The suite started the stream on the onn, as in CL-B5 / CL-B6.

| arm | idle gap | PLAYING | window (UTC) | read-backs |
| --- | --- | --- | --- | --- |
| **1 PCM** (`e3_flag.conf` `PRIVYHUB_AUDIO_CODEC=pcm`) | 120 s | 17:00:04Z (3.0 s) | 17:01:34-17:11:34 | environ at +150 s **`=pcm`, no `=opus`**, 8 lines (`environ_pcm.txt`); journal: **"ignored (codec 'pcm' is not opus); audio stays PCM"** (`journal_codec_lines_pcm.txt`); heartbeats **pcm 299, opus 0**; report `codec: pcm`; drop-in removed at teardown, `flags_absent` true |
| **2 Opus today** | 300 s | 17:17:42Z (3.0 s) | 17:19:12-17:29:12 | property **empty** before the start (`prop_reads.jsonl`); `token_issued` **`sig_v` 3 / opus** 17:17:28Z (`audit_token_issued.jsonl`); journal `opus 128 kbit/s, 10-ms frames`; heartbeats **opus 298**; **the report's `opus` has no `decode_mode` key** |
| **3 Opus lean** | 300 s | 17:35:30Z (4.1 s) | 17:37:00-17:47:00 | `setprop … lean` rc 0, **`getprop` read back `lean`** (17:29:40Z); `token_issued` `sig_v` 3 / opus 17:35:12Z; journal opus line; heartbeats **opus 299**; **the report's `opus.decode_mode` = `"lean"`**: the arm is not void |

- **The client also declared opus at setup in arm 1** (`sig_v` 3 / opus, 16:59:50Z). The host ignored it, as designed
  (CL-B6).
- **Teardown** (17:47:30Z):
  - `setprop debug.privyhub.opus_decode ""` rc 0, and `getprop` read back empty;
  - `systemctl --user restart privyhub-companion` (`restart_at_end.txt`);
  - the eight lines (`environ_end.txt`); `--check` ok after the hash pin (§6).
- **Validity** (`validity.json`): all three arms are status OK, with the gates and the read-backs held.

## 3. The onn per thread (`onn_threads.jsonl`, `tools/cl_b7_onn_threads.py`; `onn_reads.jsonl`, `cl_b6_onn_read.py`)

**How the reads were taken:**
- 150 s into each window: `top -H` of PrivyHub over 10 one-second iterations, then `top` by process over 10 more.
  The two calls are consecutive, not simultaneous.
- % of one core, mean (max).
- **Thread names are the kernel's 15-character `comm`.** So `PrivyHub-Native` is one name for
  `-Native-Audio-RX`, `-Native-Audio-Playback`, `-Native-Audio-Opus`, `-Native-Controller` and `-Native-Session`. Our
  RX, Opus decode, playback and controller **cannot be separated by name**, and TIDs are not written by design. The
  table gives the group and its thread count.

| at +150 s | **1 PCM** | **2 Opus today** | **3 Opus lean** | today − PCM | lean − today |
| --- | ---: | ---: | ---: | ---: | ---: |
| onn uptime (s) | 685 | 1,743 | 2,811 | | |
| **PrivyHub process** (`top`, 10 s) | **91.2** (97) | **110.7** (116) | **110.0** (119) | **+19.5** | −0.7 |
| PrivyHub process, single 1-s sample (`cl_b6_onn_read`) | 92.7 | 101.0 | 112.0 | | |
| threads total | 88.5 | 108.6 | 107.4 | +20.1 | −1.2 |
| **ours** (`PrivyHub-*`) | 62.5 | 70.0 | 68.9 | +7.5 | −1.1 |
| · `PrivyHub-RTP-H2…` (RTP-H264-FEC, video receive) | 30.0 (32) | 31.4 (35) | 31.2 (35) | +1.4 | −0.2 |
| · `PrivyHub-Native` (audio RX / Opus decode / playback / controller / session) | 19.8 (22), ×3 | 26.6 (29), ×4 | 25.9 (27), ×4 | **+6.8** | −0.7 |
| · `PrivyHub-MediaC…` (the video MediaCodec drain) | 12.7 (14) | 12.0 (12) | 11.8 (13) | −0.7 | −0.2 |
| **framework codec** | 13.1 | 22.9 | 22.8 | **+9.8** | −0.1 |
| · `MediaCodec_loop` | 12.1 (13), ×1 | 21.9 (24), ×2 | 21.8 (23), ×2 | **+9.8** | −0.1 |
| · `CodecLooper` | 1.0, ×3 | 1.0, ×3 | 1.0, ×3 | 0 | 0 |
| **binder** | 8.2 | 10.4 | 10.4 | **+2.2** | 0.0 |
| · `HwBinder:#_1` | 6.2 (7) | 8.2 (9) | 8.2 (9) | +2.0 | 0 |
| other (`HeapTaskDaemon` …) | 4.7 | 5.3 | 5.3 | +0.6 | 0 |
| **`media.swcodec`** (process) | **0.0** | **11.1** (12) | **11.3** (12) | **+11.1** | +0.2 |
| `android.hardware.media.c2@1.2-…-service` (the codec HAL) | 22.0 (23) | 21.9 (22) | 21.9 (23) | −0.1 | 0 |
| `audioserver` | 5.8 | 5.6 | 5.5 | −0.2 | −0.1 |
| `surfaceflinger` | 9.1 | 8.9 | 8.9 | −0.2 | 0 |
| onn busy % of 400 (10-s mean / 1-s sample) | 49.6 / 49.5 | 53.2 / 50.5 | 52.4 / 54.2 | | |
| thermal status; cpu-thermal °C | 0; 62.9 | 0; 64.3 | 0; 65.0 | | |

**Notes:**
- The "before" reads, at each arm's start, found PrivyHub idle or not running: 0.0, and not running after the install
  for arm 1. The onn was 5-26 % busy.
- The codec HAL's ~22 % runs in every arm, PCM included, so it is presumably the video decoder's (hardware H.264).
  It does not move with the audio codec.

## 4. The table across the arms, with CL-B6 as reference (`cl_b7_analysis.py` → `cl_b7_verdict.json`)

| | CL-B6 1 opus | CL-B6 2 pcm | **CL-B7 1 pcm** | **CL-B7 2 opus today** | **CL-B7 3 opus lean** |
| --- | ---: | ---: | ---: | ---: | ---: |
| onn uptime at the window | ~7-17 min | ~24-34 min | **~9-19 min** | **~27-37 min** | **~44-54 min** |
| RetroArch / capture / dup+drop (gates) | 59.999 / 59.997 / 0.1 | 59.999 / 59.998 / 0.1 | **59.999 / 59.997 / 0.1** ✓ | **59.999 / 59.998 / 0.1** ✓ | **59.999 / 59.998 / 0.1** ✓ |
| `flags_absent` after (gate) | true | true | **true** ✓ | **true** ✓ | **true** ✓ |
| PrivyHub % of a core (+150 s) | 107 (1 s) | 85 (1 s) | **91.2** (10 s) | **110.7** | **110.0** |
| `media.swcodec` % of a core | n/r | n/r | 0.0 | **11.1** | **11.3** |
| onn busy % | 51.0 | 46.0 | 49.6 | 53.2 | 52.4 |
| **underruns** (session / window; ≤ 20 of interest) | 22 / 13 | 11 / 8 | **16 / 6** | **25 / 14** | **12 / 7** |
| net audio loss (ms; per min) | 10; 0.9 | 450; 38.7 | 140; 12.1 | 90; 7.8 | 190; 16.3 |
| decode queue depth max / wait max ms | 20 / 81.8 | — | — | **45 / 218.1** | **15 / 79.9** |
| Opus decode avg / max µs | 3,094 / — | — | — | 3,157 / 34,804 | 3,023 / 33,811 |
| **decoder spikes ≥ 20 ms / min** | 104.7 | 61.4 | **70.1** | **121.0** | **108.7** |
| decoder spikes ≥ 50 ms / min | 2.92 | 2.24 | 1.98 | 2.41 | 2.58 |
| max output gap ms (report) | 261 | 209 | 242 | 260 | 405 |
| host ctrl gaps > 1 s (max ms) | 0 (688) | 0 (552) | **1** (1,172) | 0 (550) | 0 (383) |
| video loss / min | 12.9 | 51.0 | 14.6 | 27.7 | 48.3 |
| rendered fps | 59.92 | 59.83 | 59.93 | 59.85 | 59.82 |
| eno1 tx kbit/s | 8,995.8 | 11,912.1 | 11,909.1 | 9,006.0 | 9,010.3 |
| host CPU %; companion / encoder % of a core | 10.28; 20.9 / 36.8 | 10.32; 24.4 / 36.5 | 10.53; 24.9 / 35.9 | 10.44; 21.5 / 36.2 | 10.03; 21.5 / 36.1 |

(n/r = not read. CL-B6's onn CPU was one 1-s sample per window; CL-B7's is a 10-s mean.)

**On uptime:** the arms ran in a fixed order, PCM → today → lean, on one onn uptime. Lean ran last, ~45-55 min after
the power-cycle; CL-B6's evening suggested underruns rise with a long uptime. That is disclosed, not controlled.

## 5. The reading, as written beforehand

1. **Where the ~0.2 core is** (today − PCM by category):
   - the framework looper and binder threads, +12.0;
   - **plus `media.swcodec` +11.1;**
   - our own, +7.5 (the `PrivyHub-Native` group +6.8, RTP +1.4, the drain −0.7).

   The framework side carries 23.1 of 31.2, about three quarters. **→ "If the framework looper / binder threads and
   `media.swcodec` carry most of it, B's hypothesis holds": it holds.**
   - The whole-process delta is +19.5 % of a core, not "well under 0.2", so **CL-B6's single samples did not
     overstate it.** The cost on the device is larger than CL-B6 saw, ≈ 0.31 core, because `media.swcodec` is outside
     the process.
   - Our own +6.8 cannot be split by name between the Opus decode thread and RX / playback (§3). It includes the
     decode thread's own work. Its 3.0-3.2 ms per 10-ms frame is wall time (≈ 0.3 of the thread's time), and it
     includes the codec's synchronous calls; how much of it is CPU on our thread is not separable here.
2. **Lean:** lean − today on the framework codec / binder threads is −0.1 / 0.0, and `media.swcodec` +0.2. That is
   against the −1/5 of their Opus share (≈ −2.4, or −4.6 with `media.swcodec`) that the hypothesis predicted for the
   call count. **→ "If lean moves nothing, the per-call count is not the owner": lean moved nothing.**
   - The cost is the codec's per-frame work and its looper / binder traffic, not the fifth call. The 10-s means
     resolve about ±1 %.
3. **Spikes:** lean's ≥ 20-ms rate, 108.7 / min, sits between today's 121.0 and PCM's 70.1. **→ by the letter, "the
   spikes follow the call count".**
   - It is a quarter of the gap, on one run per arm, with lean last and on the longest uptime. Lean's CPU did not
     move, and its ≥ 50-ms rate is the highest of the three (2.58).
   - The letter of the reading is recorded; the files do not make it a mechanism.
4. **Underruns and the queue:** these were not in the reading, and are reported.
   - Today read 25 / 14, over the ≤ 20 bar on the session count, with the deepest queue (45 / 218 ms).
   - Lean read 12 / 7 with a shallower queue (15 / 80 ms); PCM read 16 / 6.
   - One run each.
5. **Nothing is adopted on this. What, if anything, is built next is the user's call.** The table names the owner as
   the platform's Opus MediaCodec (looper, binder, `media.swcodec`), not our threads and not the call count. A cut
   there means fewer frames through MediaCodec (bigger frames: a 20-ms Opus frame halves the frames, at +10 ms
   latency) or a decoder outside MediaCodec (libopus via JNI: no NDK on the host today, CL-B7P §2).

**The user's lines** (verbatim; nothing perceptual is a gate; `user_reports.tsv`):

| arm | at (UTC) | the line |
| --- | --- | --- |
| 1 PCM | 17:02:12Z (38 s into the window) | "Sounds fine, maybe small (<1 second) stutter every 20 seconds or so" |
| 2 Opus today | 17:19:13Z (1 s into the window; the user had played the 1.5-min warm-up) | "Sounds good, no stutters noticed" |
| 3 Opus lean | 17:54:11Z (after the arm ended, when asked) | "Sound is good, no stutters" |

## 6. The CONFIRMED APK

- All three arms were valid and arm 2 read as today (no `decode_mode` key). **By the pre-registered rule, the
  candidate stays and becomes CONFIRMED,** the step CL-B5 took. Flag-absent is the predecessor by construction
  (CL-B7P §2).
- **Pinned** (patch `CL-B7_LEAN_APK_HASH`, `cl_b7_hash.diff`, `predecessors/`, `predecessor_sha256.txt`,
  `after_sha256.txt`): `tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`, and its
  test.
- **Tests** (`tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK;
  `git diff --check` clean.
- **`--check` ok, APK CONFIRMED** (`check_end.json`).
- **The APKs, copied, nothing deleted:**
  - the installed candidate → `PrivyHub/app/build/cl_b7_installed/app-debug.apk` (`93d29b4a…`);
  - the previous CONFIRMED one → `PrivyHub/app/build/cl_b7_preserved/app-debug.apk` (`043891e1…`, the tree's build
    output, untouched);
  - both are gitignored.
- **On the onn now:** `93d29b4a…1624`, CONFIRMED, with the property empty, so the drain is CL-B5's (today's).

## 7. State at the end (17:48Z)

- **The eight adopted lines (Opus adopted); no `e3_flag.conf`; no game; `--check` ok; APK `93d29b4a…` CONFIRMED**
  (`check_end.json`, `environ_end.txt`).
- The property read back empty. One device paired (`client_end.json`). The adopted state is unchanged.

## 8. Files; disclosures

- **`cl_b7_2026-10-19/`:**
  - **the start:** `baseline_head.txt`, `git_status_at_start.txt`, `check_start.json`, `client_start.json`;
  - **the pre-registration:** `cl_b7_preregistration.txt` / `.sha256`, `preregistration_hashed_at.txt`,
    `tools_at_preregistration_sha256.txt`;
  - **the install:** `candidate_apk_sha256.txt`, `install_at.txt`, `install.log`, `client_after_install.json`;
  - **the arms:** `cl_b7_arms.py`, `arms_started_at.txt`, `arms_console.log`, `arms.jsonl`, `runs/{pcm,opus_today,opus_lean}/`
    (suite outputs), `prop_reads.jsonl`, `environ_*.txt`, `journal_codec_lines_*.txt`, `audit_token_issued.jsonl`;
  - **the onn:** `onn_reads.jsonl`, `onn_threads.jsonl`;
  - **the user:** `user_reports.tsv`;
  - **the analysis:** `cl_b7_analysis.py`, `cl_b7_analysis_console.txt`, `cl_b7_verdict.json`, `validity.json`;
  - **the pin:** `predecessors/`, `predecessor_sha256.txt`, `cl_b7_hash.diff`, `after_sha256.txt`, `tests.txt`;
  - **the end:** `restart_at_end.txt`, `check_end.json`, `environ_end.txt`, `client_end.json`;
  - `redact_check.txt`, `manifest.sha256`.
- **The session reports** are in `logs/games/decoder_sessions/` (`native_decoder_20261019_171135_706.json`,
  `…172913_626.json`, `…174701_533.json`), read, not copied.
- **adb:** the install, the two pre-registered `setprop`s, the suite's own stream start (as in CL-B5 / CL-B6), and
  state reads (`uptime`, `/proc/uptime`, `top`, `top -H`, `dumpsys thermalservice`, `/proc/meminfo`, `pidof`,
  `getprop`, `pm path` / `sha256sum` of the APK, the client prefs via `run-as`). Nothing else.
- **Not done:** no sudo, no nft, no Opal access, nothing fetched, nothing deleted, nothing adopted, nothing committed.
- **Not written:** no address, PID / TID, token or identifier. Thread names have digit runs masked (`binder:#_3`).
