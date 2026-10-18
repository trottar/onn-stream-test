---
memory_schema: 1
as_of: 2026-10-18
status: TASK HANDOFF — G4-W2 (session B, software only, after G4-W1): a compressed audio path behind `PRIVYHUB_AUDIO_CODEC=opus` (absent = today's PCM path, byte for byte), host side, proved in process; the client's Opus decode is a later APK task (session A). Run only if G4-W1 finds audio among the two largest terms; otherwise write one line in SESSION_B_STATUS.txt and skip to G8-S4
---

# G4-W2 — the Opus audio path (host side)

Read first: `G4_W1_…` (the audio term's size: payload, redundancy, packets), the audio sender and its receiver contract (the client's audio decode path in the APK — `android/…`: what format it expects, whether it already links an Opus decoder — Android's MediaCodec has `audio/opus` natively; say what the APK uses), `D_BASE_P10_…` (why 2/4 redundancy exists: the audio holes; a compressed stream must keep the same protection or better), `D_BASE_P9_…` (the cushion: ms of audio buffered), `E3_S5_…` (the sender's pacing; 400 datagrams/s = 2.5 ms per datagram — Opus frames are 2.5–60 ms; the frame size changes the packet rate).

## 1. The design (in the record §1 before the code, hashed)

- **The flag:** `PRIVYHUB_AUDIO_CODEC=opus[,bitrate=<kbps>][,frame=<ms>]` — defaults stated (a bitrate in the 96–160 kbit/s range and a frame of 10 or 20 ms are the usual choices; the record picks defaults and says why, with the latency cost of the frame size added to the cushion's arithmetic). Absent → today's PCM sender, byte for byte (the handler comparison; the sender's datagrams compared on a recorded capture).
- **Framing:** RTP with the Opus payload type; the same redundancy scheme as today (2/4) or Opus's own in-band FEC — the record states which and why, and the resulting packets/s and kbit/s on the wire (the point of the task: the number G4-W1 said to cut).
- **The host encoder:** `libopus` via the companion's existing ffmpeg or a Python binding — say which the host has (`ffmpeg -h encoder=libopus`), its CPU cost measured on the host offline.
- **The client contract:** the audio datagram header gains a codec field; a PCM client ignoring it keeps working with the flag absent; with the flag on and an old client the session must fail closed and say so (the handshake: the client's capability in `session/setup`, G3's fields) — the negotiation designed here, implemented host-side, the client part listed for the APK task.
- **Not in this task:** the APK; adoption; the video.

## 2. The proof (offline, no stream)

- A 60-s PCM capture of real game audio if one exists in the tree (say which), else a synthetic tone+noise source stated as a limit: encoded through the new path in process — bitrate on the wire per second, packets/s, encoder CPU, and decoded back with `libopus` for a PESQ-free sanity number (RMS error vs the source; no listening verdict).
- Flag absent: the sender identical (the handler comparison; a datagram-for-datagram diff on the capture).
- The redundancy/FEC behaviour under G8-P1's `loss-1` and `loss-5` in process: audio holes per minute, PCM+2/4 vs Opus+(chosen scheme) — the same protection or better, shown.
- Unit tests; the suites green; the redactor.

## 3. The record

`evidence/G4_W2_OPUS_AUDIO_PATH_2026-10-18.md` + `g4_w2_2026-10-18/`; `patches/G4-W2_…md`; ROADMAP §G4/§F (the audio path); `logs/g4_w2_git_status.txt`. **Proposed next (not run):** the APK's Opus decode and the capability field (session A, a CL-B task), then a LAN smoke with the flag, then an off-site run at 4000 with it (the data per hour measured again). Nothing adopted.
