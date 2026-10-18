---
memory_schema: 1
as_of: 2026-10-18
baseline_commit: 1fc2e19
durable_memory_updated: true
---

# G4-W2: an Opus audio path, behind `PRIVYHUB_AUDIO_CODEC=opus[,bitrate=<kbps>][,frame=<ms>]`

## Purpose

G4-W1 found the PCM audio with its 2/4 redundancy is the largest wire term: 3,212.8 kbit/s at every rung,
1.45 GB/h. With the flag, the host sends Opus instead, with the same duplication: 326.4 kbit/s at the defaults.
Only to a client that declared it; otherwise the start is refused. Record:
`evidence/G4_W2_OPUS_AUDIO_PATH_2026-10-18.md`.

## Change

- **New `companion/audio_codec.py`:**
  - parsing (defaults 128 kbit/s, 10 ms; bitrate 48-256, frame 5 / 10 / 20; invalid → logged once, PCM);
  - a ctypes binding to the host's libopus (RESTRICTED_LOWDELAY, hard CBR, complexity 10, no in-band FEC);
  - the capability capture from `/session/setup` (`audio_codecs`), by wrapping the gate instance's `_setup` from
    outside;
  - `prepare` (Opus, or the refusal text);
  - the Opus sender loop: the PCM loop's twin (same pacer, buffer, silence, duplication ~20 ms apart, counters),
    PHA1 version 2.
- **`companion/native_session_io.py`:**
  - a module global `AUDIO_CODEC`, built only under the flag, with the import inside the `if`;
  - one `if` in `_linux_sender_loop`, after the scheduler: when this start chose Opus, the module's loop runs
    instead.
- **`companion/native_stream.py`:** the same guarded global, and one `if` in `_start_linux_locked` before
  `_stop_locked`. A target that did not declare opus → `NativeStreamError` with the reason, before anything is
  stopped or spawned.
- **`companion/privyhub_service.py`:** one guarded `if` after the identity gate is built. With the flag and the
  gate, it installs the setup capture.
- **Not touched:** `companion/session_identity.py` (its instance's `_setup` is wrapped only under the flag; the
  file and the class are unchanged), `companion/overlay/`, the drop-ins, `~/.config/privyhub/`.
- **New tests:** `tests/audio_codec/test_audio_codec.py` (19).
- **Docs:** ROADMAP §G4 (the G4-W2 line).

## Validation

See the record:

- `tests/audio_codec` 19 OK; the suites green (C3-F1's pre-existing error aside), run from a /tmp copy of the
  tree;
- flag absent:
  - HEAD's and today's PCM sender are identical datagram for datagram (23,996 each, two 60-s sources);
  - HEAD's and today's start handler are identical (LAN and overlay targets);
- flag on: 200 datagrams/s, 326.4 kbit/s, as designed; encoder CPU 0.57-0.63 % of one core; decode SNR
  30.1 / 33.1 dB;
- loss-1 / loss-5 (30 seeds): the same audio-ms lost as PCM 2/4 within the sampling noise, in half the holes;
- old client: refused before any call; declaring client: Opus.

## Result

BUILT behind the flag, host side; NOT ADOPTED; the client's Opus decode not built (the APK part is listed in the
record); unvalidated live; nothing committed. `PATCH_INDEX.md` was not updated (not session B's file).
