---
memory_schema: 1
as_of: 2026-10-19
status: TASK HANDOFF — G-A2 (session A): the user's adoption of `PRIVYHUB_AUDIO_CODEC=opus` as the EIGHTH adopted line (the user's decision 2026-10-19 after CL-B5's paired A/B and listen). The pattern of G-A1 / E4-S5D: a drop-in per flag, the adopted-state tools updated to eight lines, every preflight that counts lines updated, one LAN confirmation run with no `e3_flag.conf`, the records and docs. Nothing else changes; nothing committed
---

# G-A2 — adopting the Opus audio path

Read first: `G_A1_OVERLAY_AND_IDENTITY_ADOPTION_2026-10-16.md` and `E4_S5D_…` (the adoption pattern: the drop-in file, `tools/e3_state.py`'s `ADOPTED` list, the suite's preflight, the read-back, the confirmation run, the docs touched), `CL_B5_…` (the numbers the decision rests on; the new APK `043891e1…` CONFIRMED), `G4_W2_…` (the flag's defaults: 128 kbit/s, 10 ms; fail-closed for a client without `audio_codecs`), `docs/KNOWN_ISSUES.md` (the open Opus items: decoder spikes 144 vs 100/min, not located).

## 1. The decision, recorded

The user adopts `PRIVYHUB_AUDIO_CODEC=opus` (defaults) on 2026-10-19, on CL-B5: underruns 11/13 vs 19 (bar ≤ 20), −2,910 kbit/s paired, net audio loss comparable, the user's listen "No visual or audio problems". The open item (decoder spikes, under the 200 bar, not located) is carried in KNOWN_ISSUES, not a blocker — the user's call.

## 2. Steps

1. Precondition: the seven lines, `--check` ok (adb to the onn), no `e3_flag.conf`, no game, one device paired, APK `043891e1…` CONFIRMED, the tree clean, HEAD named.
2. **The drop-in:** `~/.config/systemd/user/privyhub-companion.service.d/audio-codec.conf` with `Environment=PRIVYHUB_AUDIO_CODEC=opus` (the file named like the others); `daemon-reload`, restart; the environ read back: **eight lines**, the seven plus this one; the companion's log line `opus 128 kbit/s, 10-ms frames`.
3. **The tools:** `tools/e3_state.py` `ADOPTED` → eight lines and the eighth drop-in in its checks; `tools/e1_suite.py`'s preflight (the home row refuses any environ other than the adopted one — now eight); `tools/e1_remote.py`'s preflight (the two overlay flags plus the adopted set); the detached drivers' scaffolding strings ("adopted7 ok" → the count read from the tool, not a literal, if that is a one-line change; else noted); the `flags_absent` readers that count seven. Each a small patch, listed. `--check` ok on eight lines.
4. **The confirmation run:** one E1-PS1-STREAM `--e2 --window 600` on the LAN with **no `e3_flag.conf`** — Opus must be on by the drop-in alone: the audit's `token_issued` with `sig_v` 3 and `audio_codecs` opus, the companion's log `opus`, the heartbeats' `audio_codec=opus`; host gates; reported: underruns, net audio loss, the LAN interface's kbit/s and packets/s (expected ~9,000 and ~1,180 at 7000, as CL-B5 B), decoder spikes/min, the user's one-line listen if they are present (else "no listen").
5. **The PCM fallback stays reachable:** state what happens with the drop-in present and an old client (refused at start, with the reason — G4-W2) and how the user turns Opus off (remove the drop-in, restart) — in the record and in `docs/REMOTE_TRUST.md` or wherever the adopted lines are listed for the user.
6. **Records and docs:** `evidence/G_A2_OPUS_ADOPTION_2026-10-19.md` + directory (the drop-in's content, the read-backs, the patches, the run's output, `redact_check.txt`, `manifest.sha256`, `validity.json`); `docs/ROADMAP.md` §G4/§F (adopted); `docs/CAPABILITY_MODEL.md` if it lists the audio path's cost; `docs/KNOWN_ISSUES.md` (the spikes item kept open); `logs/g_a2_git_status.txt`; `CURRENT.md`: **the adopted state is now EIGHT lines** (list them), the APK, Next Action: the user's commit; the off-site run at 4000 with Opus (G4-S3: predicted ~5.4 Mbit/s, ~2.4 GB/h); the spikes item. Exit.

No sudo (systemd --user is not sudo), no nft, the Opal read-only, adb only for state reads, no addresses or identifiers; nothing fetched, nothing deleted; nothing committed. This task adopts exactly one line; every other flag stays absent at the end (`e3_flag.conf` absent, the eight lines only).
