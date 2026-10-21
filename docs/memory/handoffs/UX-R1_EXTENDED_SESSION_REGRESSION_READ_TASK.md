---
memory_schema: 1
as_of: 2026-10-20
status: TASK HANDOFF — UX-R1 (session A, read-only, BEFORE any other run): the user's extended play session on the evening of 2026-10-19 (US Eastern; after CL-B7's end 17:48Z) was "horrible" — every issue, audio, visual and gameplay, every game, worse as time went on, especially SNES later; much worse than an extended session "earlier" (before October's adoptions). Copy that session's files into evidence before anything rotates them, read the state the hub and the onn are in NOW before anything restarts, build the per-minute timeline, list what changed since the earlier session, rank the hypotheses with the test for each. No change, no restart, no new run. Nothing committed
---

# UX-R1 — the extended session that went bad: the read

**The user's report, verbatim (2026-10-20):**
> "I just played for an extended play session and it was horrible. It is much worse than it was weeks ago when I last did one"
> 1. "All the above. Every issue from audio to visual to gameplay. Multiple games all played terrible, especially later on with SNES"
> 2. "Every game got worse as time went on"
> 3. "besides the first 5 minutes, it was not good to terrible"
> 4. (when the earlier good session was) "Earlier" — before the October adoptions.

**This report outranks every green 10-minute window this week.** Nothing perceptual is a gate, but the user's experience is what the gates exist for; a system that passes every window and fails a two-hour evening has a gap in its windows. This task's job is to see what the files say about *that* session, not to argue with the report.

## 0. Preserve first (before any read that could rotate or restart anything)

- `evidence/ux_r1_2026-10-20/session/`: copies of everything that covers 2026-10-19 17:48Z → now — the companion's journal for the span (`journalctl --user -u privyhub-companion`, ids masked as always), **every ladder log including the rotated ones in `stream_log_archive/`** (LOG_KEEP 3 — the night queue would push these out), the recovery log, `logs/games/decoder_sessions/*.json` for the span (the client's health reports — every one), `logs/games/native_frame_sizes.jsonl` and its archive, the encoder's log, the audit log rows for the span (as the redactor allows), the EPG grabber's / scheduler's log for the span, the companion's own telemetry / heartbeat records for the span, `logs/` anything else dated in the span. sha256 each in `manifest.sha256`. **Nothing is moved; copies only.**
- **State reads NOW, before anything else** (`state_now/`): host — `free -m`, swap, load, uptime, the companion's PID age / RSS / threads / open files, the encoder and RetroArch processes if any are still up, disk free, `systemctl --user status privyhub-companion` (no restart), the journal's error / warning counts for the span, any grab running; **the onn over adb** (state reads only; `adb connect` by hand if needed, the endpoint never printed) — `uptime`, `top` (process), `top -H` of PrivyHub (`tools/cl_b7_onn_threads.py state_now`), `dumpsys thermalservice` and the cpu-thermal temperature, `/proc/meminfo`, the PrivyHub process RES, `getprop debug.privyhub.opus_decode` (must be empty), `cl_b6_onn_read.py`. **Do not power-cycle the onn, do not restart the companion** — the state is evidence.
- `--check` read (ok on eight expected); the APK read (`93d29b4a…` CONFIRMED expected); `git status`; HEAD named.

## 1. The timeline of the session

From the copies, per client session (each game start — title, core, start / end UTC, duration) and **per minute inside each**:
- rendered fps, post-FEC loss/min, FEC recovered / unrecoverable, stale/min, resyncs, the rung and every transition with its reason, the client's pauses and every recovery row (`client_output_silence`, `encoder_restart`, `gave_up_saved`, desync), host control gaps > 1 s, audio underruns and net audio loss per minute, the decode queue depth / wait and the decoder spikes from each health report, max output gap; the `wan` class if telemetry was on (it is not adopted — say so).
- **The first 5 minutes of the evening against everything after**, as the user drew the line: the same figures as two columns.
- **SNES sessions marked** (snes9x, `SNES_CAPTURE_FIX=output_rate`), and the SNES figures against the PS1 figures of the same evening.
- The onn's uptime at the session's start (it was power-cycled ~16:54Z for CL-B7 — so ~1 h up at the start, several hours by the end) and, if any report carries it, its thermal / memory state over the evening.
- **Against the week's windows** (CL-B6, CL-B7, G4-S3 — all ≤ 12 min) and **against the last extended session on record** (`D_BASE_S2_THREE_HOUR_SESSION_2026-09-21.md`, `D_BASE_S1_OVERNIGHT_SOAK_…`, `C5_CLOSE_…` — whichever is the closest match to "a long evening of play before October"): the same figures per hour where they exist.

## 2. What changed since the earlier session (a list, dated, from CURRENT / ROADMAP / the records; no judgement)

The adoptions and installs since 2026-10-01, each with its kill switch: `ADAPTIVE_BITRATE_MODE=live` (C3-L4-D1, 10-01), `EPG_GUIDE_INDEX=cached` (E3-S6A, 10-07), `SNES_CORE=snes9x` (E3-A2, 10-07), `RECOVERY_TRIGGER=v2` (E3-A3/A3B, 10-09), `SNES_CAPTURE_FIX=output_rate` (E4-S5D, 10-15), `OVERLAY_PROVIDER=tailscale` and `SESSION_IDENTITY=v2` (G-A1, 10-16), `AUDIO_CODEC=opus` (G-A2, 10-19); the APKs CL-B2/B3 (identity), CL-B4/B5 (Opus decode, the decode thread), CL-B7 (`93d29b4a…`, the lean flag absent); the memory floor / swapoff state from E4-S3B if it was applied; the link watch stopped (E4-S4C); the deferral flag NOT adopted (grabs still run during a stream — E4-S4: "the stream degrades under the grabs"); the Opal's settings (the user's hand changes, listed if the record names them). Plus the onn's own state: hours of uptime, the number of sessions that evening (CL-B6: underruns rose with the onn's session count).

## 3. Hypotheses, ranked by what §1 shows, each with its test (nothing run here)

Write only the ones the timeline supports, in the order the files rank them; for each: what in the timeline points at it, what argues against it, and the one test that would settle it — e.g.:
- **time on the onn** (uptime / sessions / thermal / the decode queue growing): the test is the same evening's games after an onn power-cycle, a 2-hour soak with `cl_b6_onn_read.py` + `cl_b7_onn_threads.py` every 5 min;
- **time on the host** (companion RSS, the encoder, log growth, swap): the state-now numbers; the test a 2-hour soak with the E1 resource sampler;
- **the grabs** (if the grabber ran during the span — the journal / scheduler log says): the test is the deferral flag on for one evening;
- **a link that got worse over the evening** (loss/min rising, resyncs): the Opal's view (read-only), the link watch resumed for one evening;
- **one of the adoptions** (if the degradation is per-feature — SNES-specific, audio-specific): the kill switches, one per evening, the user playing — a bisect plan written here, not run;
- **the ladder** (if the rung path shows it stepping down and staying down — `live` mode, recovery v2): the rung path says.
If the files show the evening's figures as clean as the week's windows, say so plainly: then the gap is between what the files measure and what the user sees, and the next task is instrumentation beside the user (a session with the user narrating by the minute against the host's clock), not a change.

## 4. Record

`evidence/UX_R1_EXTENDED_SESSION_REGRESSION_2026-10-20.md` + `ux_r1_2026-10-20/` (the copies, the state-now reads, the timeline script and its output, `redact_check.txt`, `manifest.sha256`); **`docs/KNOWN_ISSUES.md`: a new item at the top, OPEN, with the user's report verbatim and the ranked hypotheses**; `logs/ux_r1_git_status.txt`; `CURRENT.md` Next Action (the user's commit; **the night queue `QUEUE_2026-10-19N.md` held until the user says**; the one test the files rank first, written as the next task for the user's say-so). Exit.

No sudo, no nft, the Opal read-only, adb only for state reads, no addresses or identifiers anywhere; nothing fetched, nothing deleted, nothing moved; no restart, no power-cycle, no run, no change to any file outside `docs/`, `logs/` and the evidence directory; nothing adopted; nothing committed.
