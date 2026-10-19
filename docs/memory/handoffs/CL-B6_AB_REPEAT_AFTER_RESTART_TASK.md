---
memory_schema: 1
as_of: 2026-10-19
status: TASK HANDOFF — CL-B6 (session A, the user at the TV, sound ON): the paired A/B repeated after an onn power-cycle, to settle G-A2's single-run 78 underruns (CL-B5: 11/13). Opus is now adopted, so the Opus run is the plain run and the PCM run is the flagged one; the order is reversed from CL-B5. The onn's uptime and CPU read over adb this time. Measurement only; nothing adopted or un-adopted; nothing committed
---

# CL-B6 — the A/B repeated after a client restart

Read first: `G_A2_OPUS_ADOPTION_2026-10-19.md` §4 (78 underruns, 50 in the window; a burst of 22 at ~11 s during start-up; spikes ≥ 50 ms 138 vs 51/34; two > 1-s control gaps; "the onn had run five sessions since 22:00Z"; thermal 0; CPU not read), `CL_B5_…` (the paired table and its reading script — reuse it), `G4_W2_…` §1 (an unknown value for `PRIVYHUB_AUDIO_CODEC` is logged once and ignored → the PCM path; so the PCM arm is `e3_flag.conf` = `PRIVYHUB_AUDIO_CODEC=pcm`, which overrides the adopted drop-in by drop-in order — **verify by read-back and by the companion's log line, not by assumption**).

## 1. Pre-registration (hashed before the first run)

- **Hand step first (the user):** power-cycle the onn (unplug, 10 s, plug), wait for the home screen, open PrivyHub once. Code then reconnects adb and reads `uptime` — must be < 10 min — and the client's paired line.
- **Runs, both E1-PS1-STREAM `--e2 --window 600`, the same PS1 title, 5 min apart, the user playing with the sound on:**
  - **run 1 — Opus (adopted, no `e3_flag.conf`)**: the audit's `token_issued` with `sig_v` 3 and `audio_codecs` opus; the companion's log `opus`.
  - **run 2 — PCM (flagged):** `e3_flag.conf` = `PRIVYHUB_AUDIO_CODEC=pcm`; the environ read back shows that value; the companion's log says the value is ignored and the path is PCM; the heartbeats' `audio_codec=pcm`; removed at teardown, `flags_absent` true, the environ back to the eight adopted lines. If the override does not take (the log still says opus), stop and write it — do not improvise another way to turn Opus off.
- **Before each run and 150 s into each window, over adb (state reads):** `uptime`, `top -n 1` (the onn's total CPU and the PrivyHub process), `dumpsys thermalservice` or the app's thermal status, memory free. Recorded beside the run.
- **Gates (host):** the four as always. **Reported, paired against CL-B5 A/B/L and G-A2:** audio underruns (≤ 20 the number of interest), net audio loss, arrival holes, queue residence, the decode queue depth / wait maxima (Opus), decoder spikes ≥ 20 and ≥ 50 ms per min, max output gap, host control gaps > 1 s, video loss, rendered, the LAN interface's kbit/s and packets/s, host CPU, **the onn's CPU and uptime**.
- **The reading, written beforehand:** if run 1 (Opus, fresh onn) is back near 11–13 underruns, G-A2's 78 reads as the client's state after many sessions, not the codec — stated as consistent-with, not proved; if it repeats near 78, the codec path on the onn is the suspect and the adoption should be revisited (the user's call); if PCM is also high, it's the evening's link or the onn, not the codec. Whichever the files show.
- **The user's two lines, verbatim.** Nothing perceptual is a gate.

## 2. Steps

1. Precondition after the user's power-cycle: eight lines, `--check` ok (adb reconnected), no `e3_flag.conf`, no game, one device paired, APK `043891e1…` CONFIRMED, uptime < 10 min, HEAD named (tree clean).
2. Pre-registration hashed. Run 1 ("start the game, sound on"), the user's line. Gap. Run 2 with the override, its read-backs, the user's line. Teardown: override removed, restart, eight lines, `--check` ok.
3. `evidence/CL_B6_AB_REPEAT_AFTER_RESTART_2026-10-19.md` + directory (the suite's output for both, the adb readings, the paired table across CL-B5 A/B/L, G-A2 and these two, the user's lines, `redact_check.txt`, `manifest.sha256`, `validity.json`); `KNOWN_ISSUES.md` (the underrun/spikes item updated with what this shows); `logs/cl_b6_git_status.txt`; `CURRENT.md` Next Action (the user's commit; G4-S3 the 4000 hotspot run with Opus if the underruns are settled; else the user's call on the adoption). Exit.

No sudo, no nft, the Opal read-only, adb only for state reads (uptime, top, thermal, the paired line), no addresses or identifiers; nothing fetched, nothing deleted; the adopted state unchanged at the end; nothing committed.
