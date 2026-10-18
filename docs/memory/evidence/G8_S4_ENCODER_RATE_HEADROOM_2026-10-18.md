---
memory_schema: 1
as_of: 2026-10-18
baseline_commit: 1fc2e19
---

# G8-S4 — the encoder's rate headroom

**Classification: BUILT behind `PRIVYHUB_ENCODER_RC=<tight|headroom>`; proved offline on the host's VAAPI encoder and
in process through the shim; NOT ADOPTED; unvalidated live (G8-S5 proposed); nothing committed.**

- **What it does:** today's encoder is CBR over a **1-s** VBV (`-bufsize` = `-maxrate` = target). With the flag, a named
  profile narrows the window:
  - `tight`: `-rc_mode CBR -maxrate T -bufsize T×0.25` (driver: "100 % of T over 250 ms");
  - `headroom`: `-rc_mode VBR -maxrate T×1.10 -bufsize T×0.25` (driver: "90 % of 1.1 T over 227 ms").
- **`tight` does what it was built for, by less than predicted:** at 5000 the per-second p95 falls 5,605 → 5,298 kbit/s
  and the max 5,976 → 5,535; seconds over 1.10 T 11.7 % → 1.7 %. Through cap-6000 the tail drop falls **4.67 % → 3.42 %**
  and the per-second drop p95 **17.1 % → 8.0 %**. It does not fall toward 0: the shim's input mean (~6,030 kbit/s with
  FEC and headers) sits at the cap itself.
- **`headroom` is worse than today** on every cap cell (8.72 % and 14.34 % dropped): on busy content the VBR runs ~8.5 %
  over T on the mean (5,425 at 5000), 96 % of busy seconds over T.
- **Picture cost (numbers, no verdict):** `tight` against the lossless reference loses 0.45-0.47 dB PSNR avg at
  4000 / 5000 (≈ 0.1 at 7000), and its worst frame 2.4-3.4 dB; SSIM −0.0003 to −0.0004.
- **Host CPU:** within ±0.3 s of 10 s per 60 s for every profile (the encode is on the GPU; decode of the source dominates).
- **Flag absent: byte for byte as today** (14 builder cases, masked sha256; the start handler identical).

- Task: `handoffs/G8-S4_ENCODER_RATE_HEADROOM_TASK.md` (queue #3, `QUEUE_2026-10-18.md`), session B, software only. The
  task file is dated 2026-10-17; its record is written under today's date. **Baseline `1fc2e19`.**
  - The tree's uncommitted files at G8-S4's start (`g8_s4_2026-10-18/git_status_at_start.txt`) are the prompt, the queue,
    its tasks and G4-W1 / G4-W2's outputs; nothing of anyone else's was touched. `tools/claude_settings_local.json` shows
    modified in the tree after G8-S4's start; it is not session B's and was not touched.
- No companion restart, no stream, no game, no adb. Not touched: `~/.config/privyhub/`, the audit log, the drop-ins,
  `companion/session_identity.py`, `companion/overlay/`. ffmpeg ran on files only (the lossless reference in, matroska
  scratch files out, the render node for the encoder), never on the display, never with the companion's ports.

## 1. The design (written before the code)

`g8_s4_2026-10-18/design_written_before_code.md`, sha256 `74a57d10…266c`, hashed at 18:54:30Z, before the first G8-S4
code edit.

**What exists:**
- `native_stream._build_linux_ffmpeg_command`: `-c:v h264_vaapi -profile:v high -b:v T -maxrate T -bufsize T
  [-max_frame_size 90000] -g 15 -bf 0`, no `-rc_mode` → ffmpeg's `auto`, which the driver logs as **CBR, 100 % of T
  over 1000 ms, buffer T bits, initial fullness 3/4** (`rc_lines.txt`, all nine encodes).
- **The host's encoder** (`ffmpeg -h encoder=h264_vaapi`) offers `-rc_mode auto | CQP | CBR | VBR | ICQ | QVBR | AVBR`;
  **the driver (Mesa radeonsi) supports CQP, CBR and VBR only.**
- **The actuator:** every live rung change (`adaptive_level_transition` → the C3 validated / Linux level transition, an
  encoder-only restart), G8-S2's start rung and the sized 1080p rung build their argv with this same builder, with
  `bitrate_kbps = max_bitrate_kbps = target`.

**The flag and profiles:**

| profile | `-rc_mode` | `-b:v` | `-maxrate` | `-bufsize` | driver window |
| --- | --- | --- | --- | --- | --- |
| (absent) | auto → CBR | T | T | T | 1000 ms |
| **`tight`** | **CBR** | T | **T** | **T × 0.25** | **250 ms** |
| **`headroom`** | **VBR** | T | **T × 1.10** | **T × 0.25** | 227 ms, target 90 % of maxrate |

- Absent or empty → today's command, byte for byte; the module is not imported. Invalid → logged once, ignored.
- `-rc_mode` is inserted right after the `-bufsize` value; nothing else in the argv moves. The 90,000-B frame cap
  (D-BASE-P6 / P6a), the GOP, `-bf`, the profile, the filter and the sink stay. With a valid profile the profile owns
  `-maxrate` / `-bufsize`; the diagnostic `PRIVYHUB_ENC_BUFSIZE_K` is then overridden, logged once if both are set.
- **The hook:** one `if` at the end of `_build_linux_ffmpeg_command`, before the E4-S5 `-r` insertion:
  `if ENCODER_RC is not None: command = ENCODER_RC.apply(command, target_bitrate_kbps)`. **The rate options follow a live
  rung change inside that same `if`**, because the actuator builds every replacement argv through this function, and
  the profile is computed from each call's own target.

**Not in this task:** the frame cap, the GOP, the preset, the FEC, the client, the ladder.

## 2. The code

Predecessor sha256 values in `predecessor_sha256.txt` (HEAD, and HEAD + the G4-W2 hook); after values in
`after_sha256.txt` (re-checked at the record: unchanged); the diff in `g8_s4.diff`.

- **New `companion/encoder_rc.py`** (128 lines): `PROFILES`, `parse`, `rate_options`, `apply_to`, `EncoderRc` (the
  once-only log), `shared_from_environ`.
- **`companion/native_stream.py`:** the guarded global `ENCODER_RC` (import inside the `if`, +8 lines) and the one `if`
  in the builder (+3 lines).
- **New `tests/encoder_rc/test_encoder_rc.py`** (16 tests).

## 3. The proof (offline, on the host, no stream)

### 3.1 Flag absent (`flag_absent_proof.py` → `flag_absent_output.md`)

No `PRIVYHUB_*` in the process; today's `ENCODER_RC` is `None`. HEAD's builder (from git) and today's, on G8-S2's stub
manager, over 4000 / 5000 / 5500 / 6000 / 7000, 7000 with no kwargs and the sized 12,600 @ 1920×1080, each with
`PRIVYHUB_ENC_BUFSIZE_K` unset and set to 300: **14 / 14 identical** (masked sha256). The start handler
(`_start_linux_locked`): LAN and overlay targets identical (argv, level, payload, all 8 stub calls, the log).

### 3.2 The encodes (`encode_proof.py` → `encode_proof.json`, console `encode_console.txt`)

- **The source:** `runtime/c5_m3/reference.mkv`, C5-M3's 60-s lossless x11grab of the attract title through the
  companion's own scale / pad, 1280×720, 3,600 frames, sha256 `2df8ffe5…dd4e`. Real game content, but an attract
  sequence, not play (a limit). **Its first ~12 s are near-static** (headroom's VBR spends 33 kbit/s there; CBR pads
  them to T), so the tables give the busy seconds 12-59 alongside the whole minute.
- The argv is the companion's own builder's, with only the x11grab input → `-i reference.mkv` and the RTP sink →
  `-f matroska <scratch>` edited; each masked and hashed (E4-S5B's method). 9 encodes × 60 s through `h264_vaapi`;
  every one rc 0; the frame cap held (largest frame 88,571 B).
- Per-second sizes from the packets by pts (`frames/frames_<T>_<profile>.json`); the encodes' sha256 in
  `encodes_sha256.txt` (the 333 MB of scratch encodes stay outside the tree, under `/tmp`).

**Per-second output (kbit/s), whole minute and busy seconds 12-59:**

| target | profile | mean | p95 | max | over T | over 1.10 T | busy: mean / p95 / max / over T / over 1.10 T |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 4000 | absent | 4,008 | 4,481 | 4,807 | 60.0 % | 13.3 % | 4,026 / 4,522 / 4,807 / 52 % / 17 % |
| 4000 | **tight** | 4,011 | **4,164** | **4,382** | 60.0 % | **0.0 %** | 4,015 / 4,175 / 4,382 / 52 % / 0 % |
| 4000 | headroom | 3,605 | 4,569 | 4,676 | 76.7 % | 33.3 % | 4,358 / 4,611 / 4,676 / 96 % / 42 % |
| 5000 | absent | 5,007 | 5,605 | 5,976 | 61.7 % | 11.7 % | 5,033 / 5,616 / 5,976 / 54 % / 15 % |
| 5000 | **tight** | 5,014 | **5,298** | **5,535** | 56.7 % | **1.7 %** | 5,022 / 5,312 / 5,535 / 48 % / 2 % |
| 5000 | headroom | 4,458 | 5,745 | 5,831 | 76.7 % | 40.0 % | 5,425 / 5,757 / 5,831 / 96 % / 50 % |
| 7000 | absent | 7,007 | 7,280 | 7,606 | 63.3 % | 0.0 % | 7,043 / 7,318 / 7,606 / 56 % / 0 % |
| 7000 | **tight** | 7,010 | **7,211** | **7,328** | 58.3 % | 0.0 % | 7,020 / 7,246 / 7,328 / 50 % / 0 % |
| 7000 | headroom | 6,259 | 8,032 | 8,185 | 78.3 % | 40.0 % | 7,676 / 8,049 / 8,185 / 98 % / 50 % |

**Representativeness:** the flag-absent row has G8-S3's shape (p95 above the mean, ~half the seconds over T) but
**narrower**: at 5000, p95 / mean 1.119 and max / mean 1.193 here against 1.19 and 1.57 live (G8-S3: mean 5,012, p95
5,944, max 7,886). The attract sequence is less bursty than live play; the live gain from `tight` may differ in either
direction. Stated as a limit.

### 3.3 Through the shim, in process (`shim_proof.py` → `shim_proof.json`, console `shim_console.txt`)

G8-S2's harness: the real `NativeVideoFecRelay` → `RelayShim` @post-fec (no log file) → a loopback capture, fed each
encode's own per-frame sizes and pts, packetized at 1,188 B, 60 s each in real time.

| cell | profile | shim in mean / p95 (kbit/s) | tail-dropped | per-second drop median / p95 / max | lost after FEC | complete frames |
| --- | --- | --- | ---: | --- | ---: | ---: |
| 5000 @ cap-6000 | absent | 6,030 / 6,676 | 4.67 % | 2.95 / 17.12 / 29.34 % | 1,459 | 95.3 % |
| 5000 @ cap-6000 | **tight** | 6,034 / **6,333** | **3.42 %** | 2.85 / **8.02** / **10.80** % | 1,045 | 96.1 % |
| 5000 @ cap-6000 | headroom | 5,350 / 6,858 | 8.72 % | 9.08 / 12.25 / 18.10 % | 2,547 | 91.3 % |
| 4000 @ cap-4500 | absent | 4,832 / 5,383 | 9.86 % | 9.31 / 18.96 / 29.63 % | 2,498 | 87.9 % |
| 4000 @ cap-4500 | **tight** | 4,829 / **5,050** | **8.78 %** | 8.81 / **14.90** / **16.48** % | 2,208 | 88.9 % |
| 4000 @ cap-4500 | headroom | 4,380 / 5,544 | 14.34 % | 14.37 / 19.07 / 20.22 % | 3,522 | 87.7 % |

- `tight` cuts the spikes (per-second drop p95 and max roughly halved at 5000) but not the floor: the median per-second
  drop is unchanged, because the shim's input mean is at (5000 → ~6,030) or above (4000 → ~4,830) the cap. **The design's
  expectation ("toward 0") was wrong**: the cap-6000 cell's remaining drop is the mean, not the spread.
- This bench's flag-absent drop at 5000 / cap-6000 (4.67 %) sits between G8-S2's bench (1.8-2.4 %) and
  G8-S3 live (6.75 %).
- **No claim about PLAYING or the picture.**

### 3.4 Picture cost (`quality_content.py` → `quality_content.json`; whole-frame numbers in `encode_proof.json`)

PSNR avg / min (dB), SSIM All, whole frame; the content area (876×720, the pillarbox excluded) in `tables.md`.

| target | profile | vs lossless reference | vs flag absent |
| ---: | --- | --- | --- |
| 4000 | absent | 49.32 / 37.33 / 0.9933 | — |
| 4000 | tight | 48.85 / 34.90 / 0.9929 | 50.43 / 35.40 / 0.9958 |
| 4000 | headroom | 49.44 / 35.04 / 0.9936 | 50.81 / 35.42 / 0.9959 |
| 5000 | absent | 50.25 / 38.21 / 0.9944 | — |
| 5000 | tight | 49.80 / 34.77 / 0.9941 | 51.09 / 35.15 / 0.9961 |
| 5000 | headroom | 50.01 / 33.71 / 0.9945 | 51.16 / 33.92 / 0.9963 |
| 7000 | absent | 51.74 / 38.21 / 0.9958 | — |
| 7000 | tight | 51.64 / 39.18 / 0.9957 | 54.29 / 41.66 / 0.9979 |
| 7000 | headroom | 52.08 / 37.66 / 0.9961 | 53.41 / 38.25 / 0.9974 |

The minimum falls most (2.4-3.4 dB at 4000 / 5000 with `tight`), as the design expected: the 250-ms VBV starves the
I-frame of each 15-frame GOP on scene changes. Numbers only; no visual verdict.

### 3.5 Host cost (`encode_proof.json`)

ffmpeg's user + sys over each 60-s encode, the lossless decode included; decode-only baseline (same input and filter,
no hwupload / encode, `-f null`): 9.98 s.

| target | absent | tight | headroom |
| ---: | ---: | ---: | ---: |
| 4000 | 10.28 (+0.30) | 10.10 (+0.12) | 9.95 (−0.03) |
| 5000 | 10.06 (+0.08) | 10.16 (+0.18) | 9.96 (−0.02) |
| 7000 | 10.01 (+0.03) | 10.15 (+0.17) | 10.22 (+0.24) |

No measurable difference: the rate control runs in the GPU's encoder; one run each, so ±0.3 s is noise.

### 3.6 Tests

- `python3 -m unittest discover -s tests/encoder_rc -v` → **16 OK** (`tests_output.txt`): parsing and invalid values
  (logged once, inert); the rate options and `apply_to`; the bufsize override replaced and said once; the builder with
  and without the flag at each target; an invalid profile → today's command; the start carries the profile; the
  actuator's follow-through (a live rung change, the sized rung, and absent = today's); the guarded import by AST (one
  hook in the builder) and in a child interpreter.
- **The suites** (`tests_regression.txt`), run from a **slim** `/tmp` copy of the tree — `companion/`, `tools/`,
  `tests/` only, 5.7 MB; only the copy's `logs/` writable; deleted after the run:
  - overlay 17, session_identity 80, wan_telemetry 18, wan_adaptation 23, remote_ladder 26, remote_cap 16, impairment 14,
    start_rung 17, audio_codec 19, encoder_rc 16: **OK**;
  - adaptive_bitrate_live 126 and e1_remote 20: **OK**, after their three read-only fixtures in `docs/memory/evidence`
    (C5-M2's two golden argv files, E4-S5D's analysis script) were symlinked into the slim copy — not copied. Without
    them each errors once with `FileNotFoundError` (in the file, kept). The 1080p golden passing is the builder's own
    regression with the hook in place;
  - C3-F1 7 / 8: the same pre-existing error G8-S2 and G4-W2 recorded.
  - The tree's `logs/`: no file newer than the run's start.

## 4. Disclosed

- **The first suite run filled `/tmp`.** Session B's earlier runner copied `docs/memory` (2.1 GB) into each temp tree;
  four copies filled the 7.5 GB tmpfs and the step blocked (`SESSION_B_STATUS.txt`, 19:06Z). Its output is kept as
  `tests_regression_first_run_tmp_full.txt` (e1_remote's error there, with the fixture present in that copy, is most likely the full disk; not investigated further). On the user's
  instruction the four copies (`/tmp/b_suite_tree_*`) were deleted — only those — and the suites re-ran from the slim
  copy. Nothing else under `/tmp` and nothing in the repo was deleted.
- **Left in `/tmp`:** the scratch encodes (`/tmp/g8s4_scratch`, 333 MB, hashed) and the flag-absent proof's stub dir.
- The design's shim expectation (drop "toward 0" with `tight`) did not hold; §3.3 says why.

## 5. Proposed next (not run; nothing adopted)

**G8-S5** (session A, ~30 min): G8-S3's cell 1 (cap-6000, `PRIVYHUB_START_RUNG=floor`, the 5000 start) repeated with
`PRIVYHUB_ENCODER_RC=tight` (and `headroom` only if wanted for completeness; the bench predicts it worse): the shim's
tail-drop fraction and per-second drop p95, the client's rendered fps and loss/min, against G8-S3's 6.75 % and 53.1 fps.
The live per-second spread is wider than this source's, so the live result is the one that counts. Worth pairing with
G4-W2 (Opus) once the APK decodes it: −2.9 Mbit/s of audio puts the 5000 rung's wire mean well under cap-6000, which
this bench says is what the remaining drop needs.

## 6. Files

`g8_s4_2026-10-18/`:

- the design, its hash and the time: `design_written_before_code.md`, `.sha256`, `design_hashed_at.txt`;
- the code: `predecessor_sha256.txt`, `after_sha256.txt`, `g8_s4.diff`;
- flag absent: `flag_absent_proof.py`, `flag_absent_output.md`, `flag_absent_console.txt`;
- the encodes: `encode_proof.py`, `encode_proof.json`, `encode_console.txt`, `encodes_sha256.txt`, `frames/` (9),
  `rc_lines.py`, `rc_lines.txt`;
- the shim: `shim_proof.py`, `shim_proof.json`, `shim_console.txt`;
- the picture: `quality_content.py`, `quality_content.json`, `quality_content_console.txt`;
- `tables.py`, `tables.md`;
- the tests: `tests_output.txt`, `tests_regression.txt`, `tests_regression_first_run_tmp_full.txt`;
- `baseline_head.txt`, `git_status_at_start.txt`; `redact_check.txt`, `manifest.sha256`.

Also `patches/G8-S4_ENCODER_RATE_HEADROOM.md`, ROADMAP §G8 (one line) and `logs/g8_s4_git_status.txt`.
