---
memory_schema: 1
as_of: 2026-10-18
status: TASK HANDOFF — CL-B4 (session A, the user at the keyboard; one hand step at the TV if pairing is lost): the client side of G4-W2 — the APK declares and decodes Opus audio; the host's session identity signs the declaration (sig_v3); the debug APK built, installed with `-r`, pinned; then one 10-min LAN PS1-STREAM with `PRIVYHUB_AUDIO_CODEC=opus` on — the first live Opus session: holes, the wire rate, the user's listen. Flags removed at teardown. Nothing adopted; nothing committed
---

# CL-B4 — the APK's Opus decode, and the first Opus session

Read first: `G4_W2_OPUS_AUDIO_PATH_2026-10-18.md` §5.1 (the APK part, item by item: `audio_codecs` in setup; PHA1 v2 accepted in `NativeAudioReceiver`, de-dup by sequence; MediaCodec `audio/opus` with csd-0 OpusHead 2 ch / 48 kHz / pre-skip 120 and csd-1/csd-2; concealment; the 480→2×240 split for the queue; holes per 10 ms; the codec echoed in the health report) and its host-side contract (`companion/audio_codec.py`, the negotiation, fail-closed), `G3_S2_…` / `G3_S3_…` (the APK: the debug flavour is the CONFIRMED one, `adb install -r` keeps pairing, the pinned hashes, "if the client shows not paired, say so"), `G3_S1_…` (`session_identity.py`: what sig_v2 signs; sig_v3 adds `audio_codecs` — a guarded change, v2 clients still verify as today), `CL_B3_…` (the LAN smoke's shape; the host-CPU note), `D_BASE_P10_…` (holes per minute today: the number to compare).

## 1. Pre-registration (hashed before the build)

- **The client change** (the debug APK only, as CL-B1/B2/B3): the seven items of G4-W2 §5.1. **The host change:** sig_v3 in `session_identity.py` — the one file B may not touch, so it is A's: `audio_codecs` enters the signed fields when the client sends it; a client without it signs v2 and is verified as today (byte for byte on the v2 path: the handler comparison over the G3-S1 fixtures). Both behind nothing new on the client (the capability is declared always; the host uses it only with `PRIVYHUB_AUDIO_CODEC=opus`).
- **Build:** the debug APK; its sha256 pinned beside the CONFIRMED one; install with `adb install -r`; the client's "paired as …" line read back; if "not paired", stop and tell the user (the pairing hand step), then resume.
- **The smoke:** one E1-PS1-STREAM `--e2 --window 600` on the LAN with `e3_flag.conf` = `PRIVYHUB_AUDIO_CODEC=opus` (defaults: 128 kbit/s, 10 ms), read back (eight lines), removed at teardown, `flags_absent` true, `--check` ok, APK CONFIRMED on the new hash.
- **Gates (host):** RetroArch ≥ 59.9, capture 60 ± 0.1, dup+drop ≤ 0.2/min, `flags_absent` after. **Reported:** the audio stream on the LAN interface (packets/s and kbit/s: expected 200 and ~326 — the first live measurement of the saving), audio holes/min and audio underruns vs CL-B3 and D-BASE-P10, the +7.5 ms in the cushion's residence, the companion's and the encoder's CPU, the video figures as usual. **The user's listen, recorded as the user's report:** audio present, in sync, any artefact — nothing perceptual is a gate.
- **Validity:** PLAYING; the session set up with `audio_codecs: ["opus"]` in the audit (`token_issued` carries it) and `sig_v` 3; a session that fell back to PCM is void, said so, and the reason read from the companion's log.

## 2. Steps

1. Precondition: seven lines, `--check` ok, no `e3_flag.conf`, no game, one device paired, HEAD named (the tree carries B's uncommitted G4-W1/W2/G8-S4 work until the user commits — touch none of it beyond what this task names: the APK sources, `session_identity.py`'s sig_v3, the tests).
2. The pre-registration written and hashed; the client and host changes; unit tests (the APK's receiver tests if the project has them; the host's identity tests: v2 unchanged, v3 verified, a v3 claim without the field refused); the G1/G3 suites green.
3. The build, the pin, the install, the read-back. The user confirms the TV shows the app paired (one line in chat).
4. The drop-in, restart, the run, the teardown.
5. `evidence/CL_B4_APK_OPUS_DECODE_2026-10-18.md` + directory (the diffs, the test output, the APK hash, the suite's output, the audio reading, `redact_check.txt`, `manifest.sha256`, `validity.json`); `patches/CL-B4_…md`; ROADMAP §G4/§F lines; `KNOWN_ISSUES.md` if anything failed; `logs/cl_b4_git_status.txt`; `CURRENT.md` (state line: the new APK hash CONFIRMED if the smoke was valid; Next Action: the user's commit; the adoption question — `PRIVYHUB_AUDIO_CODEC=opus` as the eighth line is the user's call, with the picture and the listen in hand; then the off-site run at 4000 with it, predicted ~5.4 Mbit/s). Exit.

No sudo, no nft, the Opal read-only, adb only for the install and the state reads, no addresses or identifiers; nothing fetched (the build is offline, as G3-S2's was), nothing deleted; nothing adopted; nothing committed.
