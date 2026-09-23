---
memory_schema: 1
as_of: 2026-09-23
status: TASK HANDOFF — D-BASE close-out: re-score the baseline target table on the build as it now stands (cap 90 KB, cushion 12/17, redundancy 2/4, headless host, systemd companion), state the verdict against BASELINE_STREAM_HEALTH.md, and hand the roadmap back to Phase C; measurement + documentation, no code change; authorized by the user 2026-09-23
---

# D-BASE close-out — score the baseline as it stands

**Why.** `D-BASE` suspended Phase C until the target table in
`investigations/BASELINE_STREAM_HEALTH.md` was met or the attempt
formally abandoned (`decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md`).
Since 2026-09-20 the loss mechanism was found and capped (`P6`/`P6a`),
link-drop recovery was validated on real loss (`R3`-`R3d`), the recovery
flow fixed (`R3c2`), the audio cushion adopted (`P9a`/`T2`), the
warm-state audio loss located between the ends and covered by redundancy
(`T3`/`P10`), the host went headless with the companion under systemd
(`H2`/`H3`). Nothing has scored the table on the finished build in one
place. This task does, and writes the verdict.

Read first: `investigations/BASELINE_STREAM_HEALTH.md` (the table, each
row's definition and source counter), `CURRENT.md` §Verified State (the
table as last filled: corpus vs now), `decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md`
(the pre-registered client decision and the "not resolving" note),
`evidence/D_BASE_P10_AUDIO_REDUNDANCY_2026-09-23.md`, `evidence/D_BASE_T2_STREAMING_ACCUMULATION_2026-09-23.md`,
`docs/ROADMAP.md`, `docs/PROJECT_STATUS.md`, `TOOLS.md`.

**No code change. No profile change.** Everything measured is the
profile as adopted: `any_override: false`, cap 90,000, cushion 12/17,
redundancy 2/4, all `source: profile`, no `PRIVYHUB_*` set.

## The sessions — one cold, one warm, both scored

| # | session | condition |
| --- | --- | --- |
| 1 | C | 20 min, after ≥ 40 min with no stream (cold; the first 7 minutes are the cold plateau) |
| 2 | W | 20 min, started 1 min after C (warm throughout) |

PS1 reference title, zero input, `p9_run.sh`'s shape, `T2`'s thermal
sampler at 10 s, sampler off, heartbeat default, 0 foreign adb.

## Score, raw first

For each session and for the pair, every row of the target table with
its source counter, exactly as the investigation file defines it:
spikes ≥ 20 ms/min; rendered fps (`rendered_frames / duration`, not
`recent_fps`); received-AU fps; `max_output_gap_ms`; stale output drops
/min; **lost packets/min — video, post-FEC, as the table always read it,
and beside it audio after de-duplication**; audio underruns per session
(the total; `P2`) and `prolonged_starvation_events`/min; frames under
20 ms receive-to-output (%); client fps deficit. Put the corpus column
and the 2026-09-20 "now" column beside them from `CURRENT.md`.

Then the honest caveats in one paragraph each: `max output gap` is the
transport's and no D-BASE item moved it below ~100 ms (say the measured
range); the per-minute video loss is post-FEC; the warm-state loss is
covered, not cured (its cause is between the ends, `T3`); the synthetic
UDP pathology stays PAUSED (`M1`); the onn's thermal status never left 0.

## Verdict — pre-registered

- **BASELINE MET** if every row with a numeric target passes in **both**
  sessions except `max output gap`, and `max output gap` is ≤ 250 ms in
  both (the transport row is recorded as the one open row with its
  measured value, not as a failure of the client or encoder — `S1`/`S2`
  through `P10` all sit there). Then: `D-BASE` **CLOSED**; Phase C
  **RESUMES** at `C1` with the profile schema now carrying
  `max_frame_size_bytes`, `audio_queue_target/capacity_packets`,
  `audio_redundancy_copies/offset_packets` as the explicit fields; the
  next technical item is what `docs/ROADMAP.md` lists after C1
  (`C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA` is effectively done — say
  so if the fields are declared where C1 wanted them).
- **BASELINE NOT MET** if any other row fails in either session: name
  the row, its value and its target; `D-BASE` stays open with that row as
  the single next item; Phase C stays suspended.
- The pre-registered client decision (`D-BASE`: "if after Steps 1-3 a
  healthy decode path … cannot reach spike < 200 and fps ≥ 59.5, the onn
  is the ceiling") is re-read against these two sessions and recorded as
  **not triggered** or **triggered** with the numbers.

## Record and memory

`evidence/D_BASE_CLOSEOUT_<date>.md` (the scored table, the caveats,
the verdict) with reports, heartbeat logs, thermal jsonl and SHA-256s
under `evidence/d_base_closeout_<date>/`; `investigations/BASELINE_STREAM_HEALTH.md`
(the table's "now" column and a status line: MET / NOT MET, date);
`decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md` (status: closed or
open, with the verdict); `docs/ROADMAP.md` and `docs/PROJECT_STATUS.md`
(Phase C resumed or still suspended; the reference profile block with all
three adopted fields; the headless host and systemd companion; link-drop
recovery validated); `docs/KNOWN_ISSUES.md` (the open rows: max output
gap, warm-state loss between the ends, the PAUSED synthetic pathology,
`host_link`); `CURRENT.md` (fixed headings, `python3
tools/check_memory_health.py` healthy — **trim hard**: the D-BASE
narrative moves to `MEMORY.md`, Current Work Item becomes the C1 item or
the failing row); `MEMORY.md` (the D-BASE conclusions curated, one line
each, superseded lines marked); `handoffs/CURRENT_HANDOFF.md` rewritten
for Phase C; `investigations/ACTIVE.md`; `evidence/RUNTIME_VALIDATION.md`.
Teardown per `TOOLS.md`; companion under systemd. Never retry a failing
action more than twice. No addresses or device identifiers in any memory
or evidence file. Nothing committed.
