---
memory_schema: 1
as_of: 2026-10-18
baseline_commit: 1fc2e19
---

# G4-W2 — the Opus audio path (host side)

**Classification: BUILT behind `PRIVYHUB_AUDIO_CODEC=opus[,bitrate=<kbps>][,frame=<ms>]`, host side; proved in
process; NOT ADOPTED; the client's decode not built; unvalidated live; nothing committed.**

- **What it does:** with the flag, a stream to a client that declared `opus` in `/session/setup` gets Opus audio
  instead of PCM:
  - 128 kbit/s CBR in 10-ms frames, with the same duplication as today (the copy ~20 ms behind);
  - **200 datagrams/s and 326.4 kbit/s on the wire, against PCM 2/4's 400 and 3,212.8.**
  - That saves **2,886 kbit/s = 1.30 GB/h at any rung**: 35 % of the tailnet's data at 4000 and 25 % at 7000
    (G4-W1).
  - The audio path gains +7.5 ms.
- **A client that did not declare it** (every APK today) **is refused at stream start, with the reason,** before
  anything is stopped or spawned.
- **Flag absent: byte for byte as today.**
  - HEAD's and today's PCM sender are identical datagram for datagram: 23,996 datagrams on each of two 60-s
    sources.
  - The start handler is identical to HEAD's.
- **Protection:** under G8-P1's loss-1 and loss-5 (30 seeds), Opus with duplication loses the same audio-ms per
  minute as PCM 2/4 within the sampling noise, in half as many holes. It is not shown better.

- Task: `handoffs/G4-W2_OPUS_AUDIO_PATH_TASK.md` (queue #2), session B, software only. It ran because G4-W1 found
  audio the largest term. **Baseline `1fc2e19`.**
  - The tree's uncommitted files from the start were not touched (`g4_w2_2026-10-18/git_status_at_start.txt`):
    the prompt, the queue, its tasks, and G4-W1's own outputs.
- No companion restart, no stream, no game, no adb. Not touched: `~/.config/privyhub/`, the audit log, the
  drop-ins, `companion/session_identity.py`, `companion/overlay/`. ffmpeg ran only on a file, once: the music
  source (§2).

## 1. The design (written before the code)

`g4_w2_2026-10-18/design_written_before_code.md`, sha256 `7ce56142…6619b`, hashed at 18:42:02Z, before the first
G4-W2 code edit.

**What exists:**
- **The sender:** PHA1, a 16-B header, version 1, 960 B of s16le 48 kHz stereo every 5 ms, then the copy of
  n − 4.
- **The APK** (`NativeAudioReceiver.kt`) drops any datagram that is not version 1 / 240 frames / 960 B (`:1112`).
  It has no Opus decoder. Android's MediaCodec has `audio/opus`.
- **The host:** libopus 1.5.2 and ffmpeg's `libopus` encoder (`ffmpeg -h encoder=libopus`: frames 2.5-120 ms,
  `-fec`, `-vbr`, `-application`). No Python binding is installed.

**The choices:**

| | chosen | why |
| --- | --- | --- |
| defaults | **128 kbit/s, 10 ms** | 128 is mid-range for stereo music (96-160). 10 ms costs +7.5 ms; 20 ms would cost +17.5. |
| accepted | bitrate 48-256; frame 5 / 10 / 20 | multiples of the 5-ms pipeline. `pcm`, unknown or malformed values → logged once, PCM. |
| encoder | libopus via ctypes; RESTRICTED_LOWDELAY (CELT, 2.5-ms lookahead), hard CBR, complexity 10 | one packet per tick, in the sender thread. ffmpeg would need a second process and a container to parse. |
| framing | today's PHA1 header, **version 2 = Opus**; frames = samples / channel; the payload one Opus packet | an old client drops v2 (silence, no crash), so the host must not send it to one |
| protection | **today's duplication**, offset = round(4 × 5 / frame) → 2 at 10 ms: the same ~20 ms apart | in-band FEC (LBRR) is SILK / hybrid only, so it would be absent in CELT-only. It covers one frame back, at a lower rate. DRED needs its model. |
| negotiation | the client sends `"audio_codecs": ["opus"]` in `/session/setup`. With the flag, the gate instance's `_setup` is wrapped from outside and records it per declared host. At start, an undeclared target → `NativeStreamError` | `session_identity.py` may not be touched. Fails closed and says so. |

**The latency, added to the cushion's arithmetic:**
- Opus adds frame + lookahead − PCM's 5 ms = **+7.5 ms at 10 ms** (2.5 at 5 ms, 17.5 at 20 ms).
- The cushion stays as it is (12 / 17 packets = 60 / 85 ms; residence 57-66 ms in D-BASE-P10). The client is to
  split each decoded 10-ms frame into two 5-ms PCM packets for its existing queue.
- The copy still arrives ~20 ms after its original, inside the 60-ms target.

**The wire, predicted:**

| frame | datagrams/s | bytes each | kbit/s |
| --- | ---: | ---: | ---: |
| 10 ms | 200 | 204 B | **326.4** |
| 5 ms | 400 | 124 B | 396.8 |
| 20 ms | 100 | 364 B | 291.2 |

**Holes, predicted:** with independent loss p, the hole rate is p² of the sequences. That gives PCM 12,000 / min
× p² holes of 5 ms, and Opus 6,000 / min × p² holes of 10 ms: **the same ms lost, half the holes.** At loss-5 that
is 30 / 15 holes per minute, 150 ms / min each.

## 2. The code

Predecessor sha256 values are in `predecessor_sha256.txt`; after values in `after_sha256.txt`; the diff in
`g4_w2.diff`.

- **New `companion/audio_codec.py`:**
  - the flag;
  - the libopus binding (an encoder, plus a decoder for the proof and tests);
  - the setup capture, `prepare`, and the Opus sender loop (`run_opus_sender`).
- **`companion/native_session_io.py`:** the guarded global, and one `if` in `_linux_sender_loop`, after the
  scheduler (+11 lines).
- **`companion/native_stream.py`:** the guarded global, and one `if` in `_start_linux_locked` before
  `_stop_locked` (+11 lines). The refusal is raised there.
- **`companion/privyhub_service.py`:** one guarded `if` that installs the capture when the identity gate exists
  (+7 lines). Without the identity gate there is no declaration, so every start is refused (fails closed).
- **Known limit:** `audio_codecs` is not inside sig_v2's signed canonical, which lives in `session_identity.py`.
  An on-path party could strip it (the start is refused) or add it (an old client's audio goes silent). A sig_v3
  that signs it is listed below, not built.

## 3. The proof (offline, in process)

`g4_w2_2026-10-18/proof.py` → `proof.json`, console `proof_console.txt`. The real `_linux_sender_loop` ran on a
real `NativeAudioStreamer` rooted in a temp directory, with three stubs:

- the pacer returns at once;
- a "reader" feeds the buffer at the real-time rate;
- a capturing socket.

**The sources:**

- **No game-audio capture exists in the tree.**
- **Synthetic (the stated limit):** 60 s of stereo 440 / 660 Hz with a slow amplitude sweep plus seeded low-passed
  noise (nominally −20 dB, not calibrated).
- **Real music:** RetroArch's bundled menu music (`assets/sounds/bgm.ogg`, sha256 `62c828f0…8b80`), its first
  60 s decoded by
  `ffmpeg -i bgm.ogg -t 60 -ac 2 -ar 48000 -f s16le` to a scratch file in `/tmp` (sha256 `c872f543…732c`; not
  copied into the tree: 11.5 MB, reproducible).

**Flag absent:** HEAD's (git) and today's PCM sender over each source.

- **Identical, datagram for datagram:** 23,996 each, sha256 equal.
  - synthetic `0d7f8b89…3fe4`;
  - music `2e4f5f69…12d2`.
- 400 datagrams/s, 976 B UDP each, **3,212.8 kbit/s** in every second. The payload equals the source, byte for
  byte.
- **The start handler** (G8-S2's stub manager): HEAD's vs today's are identical for LAN- and overlay-class
  targets (argv, level, payload, all 8 stub calls, the log).

**Flag on** (the hook path: `prepare`, then the real `_linux_sender_loop`):

| profile | source | datagrams/s | UDP bytes | kbit/s (IP) | predicted | encoder CPU (% of one core) | decode SNR (RMS error) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| PCM 2/4 (today) | both | 400 | 976 | 3,212.8 | — | — | bit-exact |
| **opus (128, 10 ms)** | synthetic | **200** | 176 | **326.4** | 326.4 | **0.57** | 30.06 dB (209.7, −43.9 dBFS) |
| **opus (128, 10 ms)** | music | **200** | 176 | **326.4** | 326.4 | **0.63** | 33.09 dB (9.4, −70.8 dBFS) |
| opus, frame=5 | synthetic / music | 400 | 96 | 396.8 | 396.8 | 0.85 / 0.87 | 30.58 / 34.51 dB |
| opus, frame=20 | synthetic / music | 100 | 336 | 291.2 | 291.2 | 0.52 / 0.64 | 30.29 / 34.73 dB |

- The SNR is waveform SNR after the decoder's 120-sample pre-skip. It is a sanity number, not a listening verdict.
  The synthetic source's noise floor dominates its error.
- CBR held exactly: one size per profile, every second the same.
- 0 underflows.

**Loss** (G8-P1's `Impairer`, in process, on each path's datagrams, originals and copies alike; seeds 1-30; a
hole is a sequence neither of whose datagrams survived):

| profile | path | holes / min | audio ms lost / min | holes (30 min of audio) | predicted |
| --- | --- | ---: | ---: | ---: | --- |
| loss-1 | PCM 2/4 | 1.34 | 6.7 | 40 | 1.2 / 6 |
| loss-1 | Opus + duplication | **0.53** | **5.3** | 16 | 0.6 / 6 |
| loss-5 | PCM 2/4 | 30.64 | 153.2 | 918 | 30 / 150 |
| loss-5 | Opus + duplication | **16.01** | **160.1** | 479 | 15 / 150 |

- **Read plainly:** the same protection in audio-ms within the sampling noise. At loss-5 the difference is 6.9 ms
  / min, against a combined Poisson σ of ≈ 9. There are half as many holes, each twice as long. **Not shown
  better.**
- Both sources give identical loss rows: CBR makes the datagram sequence the same length, and the Impairer's draws
  depend only on the order.

**Fail closed:**

- An old-client setup (no field) → `_start_linux_locked` raises `NativeStreamError`: "audio codec opus is
  required by this host (PRIVYHUB_AUDIO_CODEC) and the client did not declare it in session/setup". **0 stub calls
  were made before it:** nothing stopped, nothing spawned.
- A declaring client → it starts, and the audio streamer carries the Opus session.

**Tests** (`tests_output.txt`): `python3 -m unittest discover -s tests/audio_codec -v` → **19 OK**. They cover:

- parsing and invalid values (logged once, PCM);
- the wire numbers and the copy offset;
- libopus: CBR 160 B, lookahead 120, the round trip, concealment;
- the capture: only on 200 answers, the overlay host only with sig_v 2, a later setup overriding, the wrapper
  installed once with the class unchanged;
- `prepare`;
- the start: refused with 0 calls, declaring → Opus, an invalid flag → PCM;
- the sender: PCM unchanged when the session is not Opus or the client is undeclared; the Opus datagrams' header,
  sequence, timestamps and copy pattern; encoded silence on underflow;
- the guarded imports, by AST, in all three files;
- a child interpreter: one shared instance with the flag; with it absent, `None` and the module not imported.

**The suites** (`tests_regression.txt`), run from a copy of the tree in `/tmp`, so only the copy's `logs/` could be
written:

- overlay 17, session_identity 80, wan_telemetry 18, wan_adaptation 23, remote_ladder 26, remote_cap 16,
  impairment 14, start_rung 17, audio_codec 19, adaptive_bitrate_live 126, e1_remote 20: **OK**;
- C3-F1 7 / 8: the same pre-existing error G8-S2 recorded.
- The tree's `logs/`: no file newer than the run's start.

## 4. Disclosed

- **Bytecode written.** Python wrote `.pyc` files (gitignored) for `audio_codec`, `native_session_io` and
  `native_stream` into `companion/__pycache__/` when I imported them in two sanity checks without
  `PYTHONDONTWRITEBYTECODE`.
  - The running companion keeps its loaded modules. A future start recompiles from source anyway.
- **Temp-copy cleanup.** My first suite runner removed the `__pycache__` directories inside two temp copies of the
  tree that it had just made under `/tmp`.
  - This was a `find … -exec rm`, before I replaced the runner with one that deletes nothing. Nothing in the tree,
    and nothing pre-existing, was deleted.
  - Those temp copies, a third one, and the music scratch file are left in `/tmp`.

## 5. Proposed next (not run; nothing adopted)

1. **The APK part (session A, a CL-B task):**
   - send `"audio_codecs": ["opus"]` in setup;
   - accept PHA1 v2 in `NativeAudioReceiver`, de-duplicating by sequence as today;
   - decode with MediaCodec `audio/opus`: csd-0 OpusHead (2 ch, 48 kHz, pre-skip 120); csd-1 / csd-2 the
     pre-skip and seek pre-roll in ns;
   - conceal a hole with the decoder's PLC or the existing concealment;
   - split each 480-frame output into two 240-frame packets for the queue;
   - count holes per 10 ms;
   - echo the codec in the health report.
   - With it, a sig_v3 in `session_identity.py` that signs `audio_codecs` (an identity task).
2. A LAN smoke with the flag and the new APK: holes, residence, the listen.
3. The next off-site run at 4000 with it. Predicted ~5.4 Mbit/s on the tailnet, ~2.4 GB/h, against 8.28 and 3.7.

## 6. Files

`g4_w2_2026-10-18/`:

- the design, its hash and the time it was hashed: `design_written_before_code.md`,
  `design_written_before_code.sha256`, `design_hashed_at.txt`;
- the code: `predecessor_sha256.txt`, `after_sha256.txt`, `g4_w2.diff`;
- the proof: `proof.py`, `proof.json`, `proof_console.txt`;
- the tests: `tests_output.txt`, `tests_regression.txt`;
- the baseline and the tree: `baseline_head.txt`, `git_status_at_start.txt`;
- `redact_check.txt`, `manifest.sha256`.

Also `patches/G4-W2_OPUS_AUDIO_PATH.md`, ROADMAP §G4 (one line) and `logs/g4_w2_git_status.txt`.
