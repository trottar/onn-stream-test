---
memory_schema: 1
as_of: 2026-10-18
status: TASK HANDOFF — CL-B5 (session A, the user at the TV, sound ON): the APK's Opus decode moved off the receive thread (CL-B4 §4.1's likely cause of 40 underruns), the sig_v3 overlay-host capture fixed in `audio_codec.py` (CL-B4 §4.3, one line), the debug APK rebuilt and installed; then a paired A/B on one evening — PCM then Opus, 10 min each, same game, the user listening to both — and CL-B4 §5 completed with the user's report. Nothing adopted; nothing committed
---

# CL-B5 — the decode thread, and the paired A/B

Read first: `CL_B4_APK_OPUS_DECODE_2026-10-18.md` §4 (underruns 40 vs 9: MediaCodec synchronous on the receive thread, 3.3 ms avg / 84 ms max per frame, 4 drain timeouts; spikes 178/min vs 87, cause not located; `note_setup` records the overlay host for `sig_v` 2 only) and §5 (the listen: not given — the TV was muted; record that as the user's report for CL-B4), `D_BASE_P10_…` (the ≤ 20 underruns bar), `G4_W2_…` §5.1 (the decode design), `android/…/NativeAudioReceiver.kt` as CL-B4 left it.

## 1. Pre-registration (hashed before the build)

- **Client change:** the Opus decode runs off the receive thread — a dedicated decode thread fed by a bounded queue (or MediaCodec's async callback), the release order kept, the socket read never waiting on the codec; the health report gains the decode queue's depth max and the decode thread's wait max. Nothing else in the receiver changes (the PCM path byte for byte: the receiver's PCM unit tests unchanged and green).
- **Host change (one line, disclosed, B's file):** `audio_codec.py` `note_setup` records the overlay host for `sig_v` in (2, 3). A unit test for v3 over the overlay.
- **The A/B, paired:** two E1-PS1-STREAM `--e2 --window 600` runs on the LAN, the same PS1 title, 5 min apart: **run A** flags absent (PCM 2/4, today), **run B** `PRIVYHUB_AUDIO_CODEC=opus`; the drop-in written and removed around run B only, `flags_absent` true at the end. The user plays both with the sound on and reports each in one line.
- **Gates (host, both runs):** the four as always. **Reported, paired:** audio underruns (B's bar of interest: ≤ 20, D-BASE-P10's), net audio loss, arrival holes, queue residence avg/max, the decode thread's wait max and queue depth max (B), decoder spikes/min, max output gap, video loss, rendered, the LAN interface's kbit/s and packets/s (A vs B: the saving, paired this time), companion/encoder CPU, the onn's CPU if adb reads it. **Validity:** both PLAYING; B's audit `token_issued` with `sig_v` 3 and `audio_codecs` opus; A's with `sig_v` 3 and no Opus on the wire (the companion's log: pcm).
- **The user's report, verbatim, per run:** sound present, in sync, clicks/gaps/robotic patches, any difference A vs B. Nothing perceptual is a gate.

## 2. Steps

1. Precondition: seven lines, `--check` ok (adb to the onn), no `e3_flag.conf`, no game, one device paired, APK `8e10497e…` CONFIRMED, HEAD named (tree clean after the user's commit).
2. Pre-registration hashed; the client and host changes; tests (receiver: PCM unchanged, Opus decode-thread tests; host: `audio_codec` v3 overlay test; the G1/G3 suites green); the debug APK built offline, pinned, `adb install -r`, the paired line read back (if "not paired", stop and tell the user).
3. Run A (tell the user "start the game, sound on"); its report line. Gap. Drop-in, restart, run B; its report line. Teardown: drop-in removed, restart, `flags_absent` true, `--check` ok on the new hash.
4. `evidence/CL_B5_OPUS_DECODE_THREAD_AB_2026-10-18.md` + directory (diffs, tests, APK hash, both runs' suite output, the paired table, the user's two lines verbatim, `redact_check.txt`, `manifest.sha256`, `validity.json`); **append CL-B4's §5** with "no listen: the TV was muted (the user, 2026-10-18)"; `patches/CL-B5_…md`; ROADMAP §G4/§F; `KNOWN_ISSUES.md` (close the sig_v3 overlay item if fixed; underruns if still over the bar); `logs/cl_b5_git_status.txt`; `CURRENT.md` (state line: the new APK hash CONFIRMED if both runs valid; Next Action: the user's commit; **the adoption question** — `PRIVYHUB_AUDIO_CODEC=opus` as the eighth line, with the paired numbers and the user's two lines in hand; then the off-site run at 4000 with Opus). Exit.

No sudo, no nft, the Opal read-only, adb only for the install and state reads, no addresses or identifiers; nothing fetched, nothing deleted; nothing adopted; nothing committed.
