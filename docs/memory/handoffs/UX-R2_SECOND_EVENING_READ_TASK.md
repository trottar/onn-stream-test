---
memory_schema: 1
as_of: 2026-10-21
status: TASK HANDOFF — UX-R2 (session A, read-only, before any other run): the user "ran a few games last night" (the evening of 2026-10-20, US Eastern; after UX-R1's read at ~18:31Z 10-20). The same read as UX-R1, with its scripts, on that span: preserve first, the state now, the per-minute timeline, and this time PAIRED AGAINST UX-R1 by play-minute. Plus UX-R1's H5 check (is the Load-State stream restart new since October). No change, no restart, no run. Nothing committed
---

# UX-R2 — the second evening: the read

Read first: `UX_R1_EXTENDED_SESSION_REGRESSION_2026-10-20.md` (the whole record; the scripts `ux_r1_2026-10-20/ux_r1_preserve.py` and `ux_r1_timeline.py` — reuse them, parameterised by the span; the per-minute table's columns; the first-5-minutes line; the three bursts; H1-H5), `docs/KNOWN_ISSUES.md`'s top item.

**The user's words (2026-10-21):** "Ran a few games last night." Their one-line report of how it felt, if they give one, goes in verbatim; if none is given by the time the record is written, "no report yet".

## 0. Preserve first, then the state now (as UX-R1 §0, exactly)

- `evidence/ux_r2_2026-10-21/session/`: copies of everything covering 2026-10-20 18:31Z → now (the companion journal, every ladder log including `stream_log_archive/`, the frame-size log and archive, the heartbeat / recovery / control-gap / host-sampler / audio-encoder logs, every decoder health report in the span, the audio-timing records, the game logs, the encoder log's blocks, the audit and HTTP rows), `manifest.sha256`; copies only.
- **State now, no restart, no power-cycle:** host (`free`, swap, load, uptime, the companion's PID age / RSS / threads, disk, service status, journal warning counts, any grab); the onn over adb (state reads; `adb connect` by hand if needed, the endpoint never printed): `uptime`, **the boot reason and boot history** (did the user power-cycle it before or after last night?), `top`, `cl_b7_onn_threads.py state_now`, thermal, meminfo, `/proc/net/udp6` (the `drops` column, P5's instrument — read it now even though it is post hoc), `getprop debug.privyhub.opus_decode` (empty expected), `cl_b6_onn_read.py`. `--check` (eight, the APK `93d29b4a…`), `git status`, HEAD.

## 1. The timeline, and the pairing with UX-R1

- The games (start, system / core, title, client sessions, minutes), the per-minute table, the recovery rows, the rung path, the grabs (ran or not), per report the decode queue and spikes — UX-R1 §1's shape.
- **The first 5 minutes against the rest**, the same columns as UX-R1's table, **with UX-R1's two columns beside them**.
- **By play-minute, paired with UX-R1:** post-FEC loss, FEC-recovered, concealed underruns, underruns, rendered fps, in 5-minute blocks from the first frame of each evening — one table, two evenings. Where does the step come in each (UX-R1: 37 min, at 04:56Z)? Does it come at a similar play-minute, a similar wall-clock time of day, a similar onn uptime, or not at all?
- **The onn's uptime at the first frame** (from the boot history read in §0 and the previous cold boot at ~14:22Z 10-20) — stated, since UX-R1 could not.
- **SNES against PS1** if both were played; the order they were played in (UX-R1's H3 confound: SNES was last).
- The Load-State count and the per-load stream restart, if any loads happened.
- The same Spearman set (loss vs the tail, loss vs minute, concealed vs loss).

## 2. UX-R1's H5, read (a read of old files, no run)

Is the Load-State stream end-and-restart new? Find one game log + recovery log + companion journal span from September (D-BASE-S2's 2026-09-21 soak had no input; look for a user-played PS1 session in `logs/games/` or the evidence copies of September — C3-L3A R1-R4 sessions, D-BASE-R3D hand runs) that contains "Loading state", and read whether the client session ended and restarted on it then. State the answer, or that no September load is on file.

## 3. The reading (written in the record, from the two evenings)

- If the second evening steps the same way at a similar play-minute regardless of the onn's uptime or the clock: time-in-session on the receive path, H1/H2 as UX-R1 ranks them; the instrumented evening stays the test.
- If it steps at the same wall-clock hour: something on the home network at that hour (the Opal's view, the link watch resumed, read-only) moves up.
- If the second evening is clean throughout: the first evening is one event, not a trend yet — the instrumented evening still runs, and the user's two reports side by side are the record.
- Whichever the files show. The user's report outranks nothing here and is dismissed by nothing: it is beside the numbers.

## 4. Record

`evidence/UX_R2_SECOND_EVENING_2026-10-21.md` + `ux_r2_2026-10-21/` (copies, state-now, the timeline script copy and outputs, `redact_check.txt`, `manifest.sha256`); `docs/KNOWN_ISSUES.md`'s top item updated with the second evening's line and H5's answer; `logs/ux_r2_git_status.txt`; `CURRENT.md` Next Action (the user's commit; the instrumented evening as the next task for the user's say-so, with what §3 adds to it; the night queue still held). Exit.

No sudo, no nft, the Opal read-only, adb only for state reads, no addresses or identifiers anywhere; nothing fetched, deleted or moved; no restart, no power-cycle, no run, no change outside `docs/`, `logs/` and the evidence directory; nothing adopted; nothing committed.
