# G4-W2 — the Opus audio path (host side): the design, written before the code

Session B, 2026-10-18, baseline `1fc2e19`, after G4-W1 (audio = 3,212.8 kbit/s, the
largest wire term at every rung). Hashed before the first code edit of G4-W2.

## 0. What exists (read before this design)

- **The sender** (`companion/native_session_io.py`, `NativeAudioStreamer._linux_sender_loop`):
  a 5-ms SCHED_RR pacer; 960 B of s16le 48 kHz stereo per tick from the reader's
  buffer, or silence when short (`_linux_sender_underflows`); a 16-B header
  `PHA1 <4sBBHII>` = magic, **version 1**, channels 2, sequence u16, sample timestamp
  u32, frames u32 (240); then the copy of packet n − 4 (D-BASE-P10). 400 datagrams/s,
  1,004 B each IP-level.
- **The client** (`PrivyHub/.../streaming/NativeAudioReceiver.kt`): requires magic PHA1,
  **`version == 1`**, channels 2, frames 240, payload 960 — anything else is
  `continue`d (dropped silently, NativeAudioReceiver.kt:1112). De-duplicates by
  sequence (64-slot window); queue in 5-ms PCM packets; the cushion (D-BASE-P9,
  profile 12 / 17 packets = 60 / 85 ms) is applied from the start response's
  `audio_cushion` block. **It decodes only PCM; it links no Opus decoder** (no
  MediaCodec audio path in the file). Android's MediaCodec has `audio/opus` natively
  (API 21+) — that is the later APK task.
- **The host has:** `libopus 1.5.2` (`libopus.so.0`) and ffmpeg's `libopus` encoder
  (`ffmpeg -h encoder=libopus`: 2.5-120 ms frames, `-fec`, `-vbr off|on|constrained`,
  `-application voip|audio|lowdelay`). No Python binding is installed (`opuslib`, `av`
  absent) and nothing is fetched.

## 1. The flag

`PRIVYHUB_AUDIO_CODEC=opus[,bitrate=<kbps>][,frame=<ms>]`

- **Absent → today's PCM sender, byte for byte.** The new module is not imported; no
  hook body runs.
- **Defaults: bitrate 128 kbit/s, frame 10 ms.**
  - 128: the usual stereo-music range is 96-160; 128 is near-transparent for full-band
    stereo and still 1/12 of PCM's 1,536.
  - 10 ms: the latency cost (below) is +7.5 ms; 20 ms would halve the packet rate but
    cost +17.5 ms, and D-BASE-P9 fought for single milliseconds.
- **Accepted:** bitrate 48-256 (integer kbit/s); frame 5, 10 or 20 (multiples of the
  5-ms pipeline; 2.5 and ≥ 40 refused).
- **`pcm`, an unknown codec, or any malformed or out-of-range part → logged once and
  ignored** (today's PCM path; the module reports `invalid`).
- **Encoder settings (fixed in the module):**
  - `OPUS_APPLICATION_RESTRICTED_LOWDELAY` (CELT only, full band, 2.5-ms lookahead);
  - **hard CBR** (`OPUS_SET_VBR(0)`), so every packet is bitrate × frame / 8 bytes: 160 B
    at the defaults, and the wire rate is predictable to the byte;
  - complexity 10; no in-band FEC (§3).

## 2. The latency, added to the cushion's arithmetic

- **PCM today:** 5 ms of packetization, then the cushion (target 60 ms, capacity 85;
  measured residence 57-66 ms in D-BASE-P10).
- **Opus:** frame + lookahead = 10 + 2.5 = 12.5 ms before the first sample can leave,
  against PCM's 5 → **+7.5 ms**. Decode on the client is well under 1 ms.
- **The cushion itself is unchanged.** The client splits each decoded 10-ms frame into
  two 240-frame PCM packets for its existing queue, so the cushion stays in 5-ms
  packets and the profile's 12 / 17 is untouched.
- **Total:** the audio path's added delay is 7.5 ms at 10-ms frames (2.5 at 5 ms,
  17.5 at 20 ms).
- The copy (§3) still arrives 20 ms after its original, inside the 60-ms target, as
  today.

## 3. The framing and the protection

- **The same PHA1 header, same layout, `version = 2` meaning "Opus":**
  - channels 2;
  - the sequence counts Opus packets;
  - the timestamp is in 48-kHz samples;
  - frames = samples per channel in the packet (480 at 10 ms);
  - the payload is one Opus packet.
  - An old client drops v2 at its version check: silence, not a crash. That is why the
    host must not send v2 to it (§4).
- **Protection: today's duplication, the same 20 ms apart.** Copies = the profile's
  `audio_redundancy` copies. The offset in packets = round(offset × 5 ms / frame), at
  least 1 → **2 at 10 ms** (4 at 5 ms, 1 at 20 ms). The same time separation is kept,
  so the same burst tolerance.
- **Why not Opus's in-band FEC:**
  - libopus's LBRR exists only in the SILK and hybrid layers. RESTRICTED_LOWDELAY is
    CELT only, so in-band FEC would not apply.
  - In the modes where it does apply, it covers only the one previous frame, at a lower
    bitrate.
  - DRED (1.5's neural redundancy) needs its model built in and is not assumed.
  - Duplication gives independent random loss the same p² residual as PCM 2/4 today.
- **The wire at the defaults:**
  - 100 originals/s + 100 copies/s = **200 datagrams/s**;
  - 160 + 16 + 28 = 204 B IP-level → **326.4 kbit/s** (PCM 2/4: 3,212.8);
  - **−2,886.4 kbit/s = 1.30 GB/h saved**, plus 200 fewer packets/s on the overlay's
    underlay (~69 B each → ~110 kbit/s).
- **At the other frames:**

  | frame | datagrams/s | bytes each | kbit/s |
  | --- | ---: | ---: | ---: |
  | 5 ms | 400 | 124 B | 396.8 |
  | 20 ms | 100 | 364 B | 291.2 |
- **Predicted holes:** under independent loss p, a sequence is lost only when both its
  datagrams are, so the residual is p² of the sequences in both paths.
  - **PCM:** 12,000 sequences/min × p² holes of 5 ms each.
  - **Opus at 10 ms:** 6,000/min × p² holes of 10 ms each.
  - So **the same milliseconds of audio lost per minute, in half as many holes.**
  - At loss-1: PCM ≈ 1.2 holes/min (6 ms/min), Opus ≈ 0.6 (6 ms/min).
  - At loss-5: PCM ≈ 30 holes/min (150 ms/min), Opus ≈ 15 (150 ms/min).

## 4. The client contract and the negotiation (host side here; the APK part listed)

- **The capability:** the client adds `"audio_codecs": ["opus"]` (a list of strings;
  PCM is implicit) to its `/session/setup` body.
- **How the host captures it.**
  - `session/setup` is answered by `companion/session_identity.py`, which this task may
    not touch.
  - So, with the flag on and only then, `audio_codec.install_setup_capture(gate)`
    wraps the gate instance's `_setup` from outside. It calls the original unchanged and
    records the declared codecs for the session's declared hosts (media host and overlay
    host) on a 200 answer.
  - The file is not edited. The wrapper is installed by one guarded `if` in
    `privyhub_service.py`.
  - **Limit:** the field is not inside sig_v2's signed canonical (that canonical lives in
    `session_identity.py`). An on-path party could strip or add it, which only fails
    the session closed or makes an old client's audio silent. A sig_v3 that signs it is
    listed for the APK / identity task, not built.
- **At stream start, with the flag on (one guarded `if` in
  `native_stream._start_linux_locked`, before the encoder is spawned):**
  - the target declared `opus` in its latest setup → the audio streamer is configured
    for Opus, and the start log says so;
  - otherwise (an old client, a setup without the field, or no session identity at all,
    e.g. the legacy LAN path) → **the start is refused.** The error is
    `NativeStreamError`: "audio codec opus is required by this host
    (PRIVYHUB_AUDIO_CODEC) and the client did not declare it in session/setup". The
    plugin returns it as today's 503 with that text. **It fails closed and says so;**
    nothing is spawned.
- **The sender hook (one guarded `if` in `NativeAudioStreamer._linux_sender_loop`,
  after the scheduler is prepared):** when the module is loaded and this session was
  configured for Opus, the module's Opus loop runs in place of the PCM loop. It has
  the same pacer (`_linux_wait_until`), the same buffer, the same silence on underflow
  and the same counters (`_linux_packets_sent`, `_linux_duplicates_sent`, errors,
  intervals), so status and the 20-packets-in-1-s startup check work unchanged.
- **The APK part (listed, not built; session A, a CL-B task):**
  - send `audio_codecs` in setup;
  - accept PHA1 v2 and de-duplicate by sequence as today;
  - decode with MediaCodec `audio/opus` (csd-0 OpusHead 2 ch / 48 kHz / pre-skip 120,
    csd-1 / csd-2 the pre-skip and seek pre-roll in ns), with the decoder's PLC or the
    existing concealment on a hole;
  - split each 480-frame output into two 240-frame packets for the queue;
  - count holes per 10 ms;
  - echo the codec in the health report.

## 5. The host encoder

**A ctypes binding to the host's `libopus.so.0`, inside the module.** It uses
`opus_encoder_create` / `opus_encode` / `opus_encoder_ctl` and `opus_decoder_create` /
`opus_decode` (the decoder for the proof only). ffmpeg's `libopus` was rejected for the
live path: a second process and a container to parse for packet boundaries, where the
sender needs one packet per tick. The proof measures the encoder's CPU in process
(thread CPU time over 60 s of audio).

## 6. The proof (offline, no stream)

- **The source.** There is no game-audio capture in the tree.
  - The primary source is **synthetic: 60 s of stereo 48 kHz s16le**, a 440 + 660 Hz
    tone pair with swept amplitude plus pink-ish noise at −20 dB, generated
    deterministically (seeded). This is stated as a limit.
  - A secondary source of real music: RetroArch's bundled menu music (`assets/sounds/bgm.ogg`,
    44.1 kHz Vorbis), its first 60 s decoded to 48 kHz s16le **by ffmpeg on the file**.
- **Through the real sender code in process,** each source fed into a real
  `NativeAudioStreamer`'s buffer, with a deterministic pacer stub and a capturing socket:
  - wire bytes per second and datagrams per second;
  - encoder CPU;
  - decode with libopus and the **RMS error against the source**, after the decoder's
    pre-skip, as SNR dB. A sanity number, no listening verdict.
- **Flag absent:** HEAD's sender (from git) and today's patched sender, the same capture
  and stubs, compared **datagram for datagram** (bytes and order). In addition, the
  start handler with the flag absent is compared against HEAD's (argv, calls,
  payload), as in G8-S2.
- **Loss:** G8-P1's `Impairer` (`loss-1`, `loss-5`, seeds 1-5) applied in process to
  each path's datagram stream, originals and copies alike. A sequence is a hole if
  neither copy survives. Reported: holes per minute and audio-ms lost per minute, PCM
  + 2/4 against Opus + duplication, against §3's prediction.
- **Fail closed:**
  - an old-client setup (no field) → the start is refused, with the message, and nothing
    is spawned;
  - a declaring client → Opus;
  - the flag absent → the wrapper is never installed (the gate's `_setup` is the class
    function).
- Unit tests in `tests/audio_codec/`; the suites green; the redactor.
- **Not in this task:** the APK, adoption, the video, sig_v3.
