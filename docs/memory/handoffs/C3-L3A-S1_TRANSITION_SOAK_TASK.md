---
memory_schema: 1
as_of: 2026-09-24
status: TASK HANDOFF — C3.L3a-S1, the transition soak: unattended attract-mode sessions on the adopted build, three with 20 scheduled transitions each interleaved with three plain holds, to put the C3.L4 readiness numbers at n >> 1 (per-transition cost, settling, lifecycle) and to measure what 20 restarts per session do to the close-out rows against the night's own no-transition band; diagnostic only, authorizes nothing, no companion / client / profile change; authorized by the user 2026-09-24
---

# C3-L3A-S1 — the transition soak

**Why.** The gate itself (`C3.L3a` Part 2) is the user's eyes and cannot be
automated. What can be: the numbers a `C3.L4` controller design needs,
which the smoke gave at n = 8 on one evening
(`evidence/C3_L3A_P2R2_SMOKE_SESSION_2026-09-24.md`): the cost of a
`video_only_restart` at the decoder (125-211 ms, codec 7-11 ms), telemetry
settling (one to two client reports), lifecycle deltas, and the close-out
rows of a session carrying restarts. This task takes them at n = 60
transitions, 30 settling measurements, cold and warm, beside plain holds
from the same night. Every transition is a scheduled loopback diagnostic
call — `C3.L2`'s authorized use ("explicit manual or loopback-only
diagnostic bitrate changes", "`C3.L3` characterization cycles"); nothing
here adapts to a condition, and the probe stays not-a-controller.

Read first: `evidence/C3_L3A_P2R2_SMOKE_SESSION_2026-09-24.md`,
`evidence/C3_L3A_P2R3_POOLING_RULE_2026-09-24.md`,
`evidence/D_BASE_CLOSEOUT_2026-09-23.md` (the rows and their source
counters; `d_base_closeout_2026-09-23/closeout_score.py`),
`evidence/d_base_p9_2026-09-23/p9_run.sh` (the harness to derive from),
`evidence/D_BASE_T2_STREAMING_ACCUMULATION_2026-09-23.md` (the warm state;
`t2_sample.py`), `TOOLS.md` (host-shell sessions, the systemd companion,
teardown), `decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md` §Authorized
use.

**No companion, client, profile, route or environment change.** The
adopted profile as the close-out scored it: `any_override: false`, cap
90,000, cushion 12/17, redundancy 2/4, no `PRIVYHUB_*` set — confirm in the
companion's environ and `native-stream-status` before every session. The
probe (`tools/probe_c3_l3a_gameplay_acceptance.py`) is used as installed;
prefer no change to it (see "Headless" below).

## The sessions — six, interleaved, one night

PS1 reference title, attract mode, zero input, RESUME PLAYING, BACK to end,
the harness shape of `p9_run.sh` (companion restarted through its unit
before each session, MainPID owns 8765, 0 foreign adb during the hold),
`T2`'s thermal sampler at 10 s for the whole night, heartbeat default.

| # | arm | what | length |
| --- | --- | --- | --- |
| 0 | T0 | probe smoke, `--traversals 2 --dwell-min 40 --dwell-max 50 --no-park`: proves the headless path and the attract-mode preflight before the night is spent | ~3 min |
| 1 | T1 | **cold** — starts ≥ 40 min after the last `session_ended` (wait for it; T0 counts as a session, so T1 waits 40 min after T0); probe `--traversals 10 --no-park` (defaults: dwell 55-90, W 5.0, seed fresh) | ~14 min |
| 2 | H1 | plain hold, duration = T1's Phase A length | same |
| 3 | T2 | probe `--traversals 10 --no-park` | ~14 min |
| 4 | H2 | plain hold, = T2's length | same |
| 5 | T3 | probe `--traversals 10 --no-park` | ~14 min |
| 6 | H3 | plain hold, = T3's length | same |

Only T1 is cold; H1-H3 and T2-T3 are warm (`T2`: the path drops single
packets from ~7 min after a cold start until ~30 min idle). That is the
design: the transition cost is wanted in both states, and the no-transition
band is wanted warm, which is where the rerun sessions will be. One
session's failure is recorded and the queue moves on; never retry a failing
action more than twice.

**Headless.** The probe waits on `input()` to start and reads marks from
stdin. Run it as `printf '\n' | python3 tools/probe_c3_l3a_gameplay_acceptance.py …`:
the one newline starts Phase A, then stdin is at EOF and the mark reader
exits — marks are 0 by construction and the record says so. If T0 shows
this does not work (the probe blocks, or a spurious mark is recorded), add
a `--headless` flag that skips the start prompt and does not start the mark
capture, `py_compile`, re-run `--plan`, and record the change; that is the
only probe change permitted. After each T session copy
`logs/streaming/c3_l3a_gameplay_acceptance_state.json` into the evidence
directory at once (the next run overwrites it), then `--finalize --state
<that copy> --decoder <that session's report>`; the run files land in
`c3_l3a_runs/` where `--aggregate` will **skip** them (no-park is not the
pre-registration) — move them into the evidence directory anyway so the
user's rerun pool stays clean. The probe restores 7000 on every exit; the
harness confirms `bitrate_kbps` 7000 before BACK regardless.

## What is measured, and the pre-registered reading

**A. Transition cost, n = 60** (T1-T3, 20 each: 5 jumps + 5 ramps × 3
rungs). Align every session's 20 fires to its `ssrc_change`s as the
probe does (spread ≤ 1 s or the session's decoder-axis rows are
INDETERMINATE). Report the largest `output_gap_ms` in `[ssrc, ssrc + 1 s]`
and its `codec_ms`, first-IDR ms, `jump_packets`, spawn / first RTP resume /
host verified ms — as distributions (n, min, median, p95, max) split by
**shape** (jump vs ramp rung), **direction** (down vs up), **state** (T1's
first 7 minutes = cold; everything else warm), and per session. State the
slow-event coverage per session (`retained` vs capacity; a 14-minute
session with 20 restarts may saturate the 64-entry marked segment — if it
does, say which transitions are covered and score only those).
Classification: **COST CHARACTERIZED** if ≥ 54 of 60 transitions align and
are covered; otherwise **PARTIAL** with the count. No threshold on the size
— the size is the fact. Beside it, the smoke's 125-211 / 7-11.

**B. Settling, n = 30.** Distribution of `settled_s`, distinct-snapshot
counts, `sample_interval_ms`, never-settled count. Expected from the smoke:
every value is the rule's floor (one to two client reports); say whether
any sequence took a third report or more, and if so which and what the
samples showed.

**C. Lifecycle, 60 transitions.** FEC send errors, audio send errors,
controller bad packets — deltas per transition and totals; the client's
`ssrc_changes` = 20 per T session (+ the restore if the last traversal left
the stream at 5000: the probe's `expected_transitions()` counts it).
**CLEAN** only if every delta is 0 and every session's SSRC count matches.

**D. The close-out rows with 20 restarts, against the night's own band.**
For each of the six sessions: spikes ≥ 20 ms/min, rendered fps, stale
drops/min, video loss/min post-FEC, audio underruns per session, max
output gap, `prolonged_starvation_events`/min, `fec_recovered`/min — from
the same counters as `closeout_score.py`. The **band** for a row is the
five no-transition values: H1, H2, H3 and the close-out's C and W. The
rule is written against that band, on the direction that matters (worse):
a row is **ELEVATED BY TRANSITIONS** only if **all three** T values are
worse than the band's worst value **and** the T median is beyond the band's
worst by more than the band's own width (max − min of the five); anything
less is **WITHIN THE NIGHT'S NOISE**. Max output gap is excluded from this
rule — in a T session it is a transition by construction; report it as
part of A. Say plainly, per row, which side of the rule it fell on and by
how much. Then the one question that matters for the rerun: **does the
baseline stay met in the T sessions** (every numeric-target row inside its
target)? Yes / no, with the failing row and value if no.

**E. Warm-state context.** `t2_sample.py` at 10 s across the night: onn
cpu-thermal at each session's start and end, thermal status (expect 0),
the audio-loss-per-minute series from the heartbeat for every session, so a
T session's loss can be read against the H session beside it in the same
thermal state. Expect the warm-state loss in both arms; the question is
whether the T arm's is different, judged by the same band rule.

**F. Controller transport `lost_packets` with zero input** (the
`KNOWN_ISSUES.md` 2026-09-24 item). `conditions_before` / `after` in each T
state file, and `native-stream-status` at start and end of each H session:
the counter's rate per minute under attract mode, six sessions. Recorded as
the zero-input baseline for that item; not investigated further here.

**What this does not establish, to be said in the record:** nothing about
perception (no marks were possible), nothing about the gate, nothing about
behaviour under real network pressure (every transition fired from a
schedule), nothing about input (zero of it).

## Record and memory

`evidence/C3_L3A_S1_TRANSITION_SOAK_<date>.md` — the six sessions with
times and thermal state, A-F with their classifications, the band table,
the "baseline stays met in T" answer, the caveats. Evidence under
`evidence/c3_l3a_s1_<date>/`: the harness script (derived from `p9_run.sh`,
named `c3_l3a_s1_run.sh`, copied in), per session: the decoder report,
heartbeat jsonl, frame-size jsonl, companion journal (redacted — private
addresses as `<IP_REDACTED>`, `h2_prep_redact.py --check` on every text
file), `native-stream-status` at start and end; per T session: the state
copy and its finalize outputs; the thermal jsonl for the night; the
scoring script (verdict rules in its docstring, written before the data);
`sha256sum` manifest of every file. `patches/` entry only if the probe was
changed. Update `investigations/ACTIVE.md` §C3.L3a (S1's numbers, one
paragraph), `CURRENT.md` (Verified State: the transition cost and settling
at n = 60 / 30 in one line; **strike the stale line "`.claude/` and
`_prel2b/` are untracked and unignored" — both are in `.gitignore` since
2026-09-23**; Next Action unchanged: the user's rerun sessions, then
`C3.L4`; fixed headings; `python3 tools/check_memory_health.py` healthy),
`2026-09-24.md` or the next day's file, `handoffs/CURRENT_HANDOFF.md` one
line, `evidence/RUNTIME_VALIDATION.md`, `docs/KNOWN_ISSUES.md` (the
zero-input controller figure under its item). **`C3.L4` stays BLOCKED on
the gate**; this task authorizes nothing. Teardown per `TOOLS.md`;
companion left running under systemd; stream at 7000; game inactive;
banner cleared; sampler stopped. No addresses or device identifiers in any
file. Nothing committed.
