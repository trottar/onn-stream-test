# Active investigations

## C3 Linux actuator boundary

Record: `C3_LINUX_ACTUATOR_BOUNDARY.md`
Decision: `../decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`
Evidence: `../evidence/C3_L2A_E2_ACTUATOR_IDR_RESOLVED_2026-09-18.md`,
`../evidence/C3_L2C_LOW_LATENCY_DECODE_FALSIFIED_2026-09-19.md`,
`../evidence/C3_L3_LINUX_FIXED_BITRATE_CHARACTERIZATION_2026-09-19.md`

Question: can the existing Linux streaming architecture expose safe
backend-neutral quality controls without disturbing validated playback?

**State as of 2026-09-19.** The measurement side of this investigation is
finished. What remains is a judgment nobody has made.

| Sub-item | State |
| --- | --- |
| `C3.L0` source audit | COMPLETE |
| `C3.L1` / `C3.L1R1` encoder-only actuator | COMPLETE / RUNTIME VALIDATED |
| `C3.L2` classification | COMPLETE; reason 1's premise falsified, decision unchanged |
| `C3.L2a` first-IDR acceptance | **ANSWERED**; IDR wait falsified |
| `C3.L2b` decoder-report cycle retention | COMPLETE / RUNTIME VALIDATED |
| `C3.L2c` low-latency decode | **FALSIFIED / ROLLED BACK** |
| `C3.L3` fixed-bitrate port and characterization | COMPLETE / RUNTIME VALIDATED |
| `C3.L3a` gameplay acceptance probe | **REGISTERED / NEXT** |
| `C3.L4` automatic controller | **BLOCKED**; gate is `C3.L3a` |

Linux is `video_only_restart`: authorized for start-time profile selection,
manual and loopback-only diagnostic changes, fallback and recovery, and `C3.L3`
characterization; not authorized for automatic adaptation during play.
`live_bitrate_reconfigure` is not available under the current architecture.

### What the measurements settled

- **The actuator is not expensive.** `C3.L2a` E2: the cycle's first IDR was
  accepted 27 ms after the SSRC change, complete and unrepaired, and nothing
  registered at the cycle. The same session's ordinary resyncs cost 195 and
  210 ms. **287-318 ms was never actuator cost** and must not be cited as such.
- **Decode time is not the stall.** `C3.L2c` cut `max_codec_ms` to 107 ms —
  best of eight same-day sessions, zero 250 ms spikes — and `max_output_gap_ms`
  came out 385 ms, second worst of the eight. `max_codec_ms` is falsified as a
  proxy for the gap.
- **6000 kbps is the steadiest characterized level.** `C3.L3`, three valid
  samples per bitrate: 5000 kbps 242-367 ms (125 ms band), 5500 kbps 219-584 ms
  (365 ms), 6000 kbps 291-331 ms (**40 ms**).

### What is not settled, and why the controller stays blocked

Every figure above is transport and decoder timing. **No perceptual quantity
has been measured at any point in this investigation.** `C3.L2c` is the
standing proof that the two come apart: the instrumentation said the build was
clearly better and the user's verdict was "trash".

Two distinct unanswered questions:

1. **Are repeated, unannounced, under-pressure transitions perceptible?** The
   2026-09-18 manual observation covered a single announced transition, which
   `C3.L2` reason 3 already ruled insufficient.
2. **Do the candidate destinations look acceptable?** Nothing has judged the
   picture at 5000 or 5500 kbps. A fast-down controller whose destination is
   visually poor fails even with invisible transitions.

## C3.L3a — gameplay acceptance probe. PART 1 RUNTIME VALIDATED / PART 2 INSTALLED.

The `C3.L4` gate, made performable. Diagnostic-only. **It authorizes nothing**
and adds no controller logic. Full design in
`../architecture/ADAPTIVE_BITRATE.md`, section "C3.L3a design".

**Part 1 — `C3-L3A-P1`, installed 2026-09-19, DEVELOPMENT ONLY.** Ported the
D-069 validated-ladder seam to Linux. `_run_c3_linux_bitrate_cycle` now holds
one body with two preconditions, mirroring the Windows split;
`run_c3_linux_fixed_bitrate_cycle` keeps the `C3.L3` behaviour unchanged, and
`run_c3_linux_validated_bitrate_transition` allows chained transitions in
either direction between `(5000, 5500, 6000, 7000)`.

No new companion method and no new route were built —
`diagnostic_c3_validated_bitrate_transition` and its loopback route already
existed and dispatched to the Windows implementation unconditionally. The
only route change was adding 5000 to the allowlist. This supersedes both the
earlier "reuses `run_c3_linux_fixed_bitrate_cycle` as-is" description and the
later `ladder_transition`/new-route design; see the correction in
`../architecture/ADAPTIVE_BITRATE.md`.

**Part 2 INSTALLED 2026-09-19, development only — not yet run.**
`tools/probe_c3_l3a_gameplay_acceptance.py` plus the shared
`tools/manual_checkout.py`. Tools only; no companion source changed and no
existing probe touched. Record:
`../patches/C3-L3A-P2_GAMEPLAY_ACCEPTANCE_PROBE.md`.

To run it:

    python3 tools/probe_c3_l3a_gameplay_acceptance.py --plan
    python3 tools/probe_c3_l3a_gameplay_acceptance.py --traversals 8
    python3 tools/probe_c3_l3a_gameplay_acceptance.py --finalize
    python3 tools/probe_c3_l3a_gameplay_acceptance.py --aggregate

The probe requires the stream active and at 7000 and fails preflight
otherwise. It always returns the stream to 7000 — on success, on error and on
Ctrl-C.

**Part 1 gate PASSED 2026-09-19.** The round trip
`7000 -> 6000 -> 5500 -> 5000 -> 5500 -> 6000 -> 7000` ran clean on both
sides. Host: every transition `ok`, `from_bitrate_kbps` chaining exactly,
zero FEC/audio/controller deltas, spawn spread 0.45 ms across five restarts,
ending at reference. Client: `ssrc_changes` 6, all six discontinuities typed
`ssrc_change` with `jump_packets` 0, first IDRs at 18/24/24/29/30/65 ms, all
complete and unrepaired. A redundant same-target request was correctly
rejected with `bitrate_transition_noop`. Record:
`../evidence/C3_L3A_P1_LADDER_TRANSITION_RUNTIME_2026-09-19.md`.

Part 1 needs no further work, and **it advances the `C3.L4` gate not at
all** — nothing perceptual was measured.

Requirements, from `../decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`,
section "The `C3.L4` gate, stated so it can be satisfied":

1. several transitions within one play session, not one;
2. fired at intervals the player does not know in advance;
3. at least one interval in which nothing fires, as a control;
4. the player's marks compared against `stream_discontinuities` `elapsed_ms`
   after the session, not during it;
5. part of the session parked at 5000/5500/6000 kbps so the picture itself
   can be judged.

**Part 2 session design, settled with the user 2026-09-19.** Ladder state
machine alternating top (7000) and bottom (5000); each traversal randomly
assigned **jump** (one cycle, 2000 kbps delta) or **ramp** (three cycles, one
rung each, 4 s apart). Jump and ramp data are recorded separately and never
pooled — a ramp's three smaller discontinuities and a jump's one larger one
answer different questions, and per the architecture's fast-down/slow-up rule
the ramp is what routine `C3.L4` adaptation would actually do while the jump
exercises the separately-authorized fallback/recovery case.

Decoys cost no session time: each dwell carries one decoy timestamp at a
random offset where nothing fires, giving a 1:1 decoy ratio and a
false-alarm baseline without it, a mark rate on ramps means nothing.

Marks are captured non-blocking — the player presses Enter on the companion
terminal the instant they notice something, timestamped against the same
clock as the cycle log and `stream_discontinuities`. A blocking prompt would
itself telegraph that a transition fired. The association window is
**asymmetric**, `[event, event + 2.5 s]`, because a mark always lags the
event by reaction time; decoys are scored through the identical window.
Primary metric is binary per sequence — was this sequence marked at all;
mark count is secondary, since a three-rung ramp in 8 s may reasonably draw
one press.

Runs pool: per-run files aggregate across sessions of the same configuration,
so several shorter sessions beat one long one. Attention drifts over a long
marking session, and drift correlated with shape order would fake a result —
shape order is randomized within each run.

Expectation, stated plainly: ~20 of each shape estimates a detection rate to
roughly +/-11%. That resolves a large difference and will not resolve a
subtle one. Pooling is what moves it.

Writes a fresh per-run result file with cycle times, and always returns the
stream to 7000 on completion, on error and on interrupt — nothing today does
that, so a session currently stays parked wherever the last cycle left it.
Changes no production path. No acceptance threshold is encoded in the probe —
the probe records, the user judges.

Outcome disposition: marks not aligned with cycle times and the picture judged
acceptable → the gate is met and `C3.L4` may be proposed. Marks aligned →
`C3.L4` is answered in the negative and closed cheaply. Either is a result.

## Deferred, not active

- UDP burst/gap pathology — awaiting representative Linux replay. See
  `DEFERRED.md` and `docs/KNOWN_ISSUES.md`.
- Adaptive FEC — C4.
- Linux host resource telemetry gap — recorded in `docs/KNOWN_ISSUES.md`; not an
  active investigation.

## Open, not blocking

- `slow_events_marked` emitted empty while `slow_event_retained_marked` reports
  30 of 64.
- `tools/probe_c3_fixed_*_characterization.py --finalize` matched the wrong
  decoder-session file once, when run back to back after another bitrate's
  finalize. Intermittent. Check `payload.decoder_session_log` and
  `session_duration_ms` before using any finalize result.
- The cause of a 385 ms output gap in a session with zero 250 ms codec spikes.
  No work item owns it.

Both defects are in `docs/KNOWN_ISSUES.md`.

## Superseded — the 2026-09-18 open state (history)

Before `C3.L2a` E2, this file recorded `C3.L2a` as open with the question
unanswered, `C3.L2b` as code-installed with no runtime evidence, `C3.L2c` as
registered but unauthorized, and `C3.L4`'s gate as `C3.L2a`. All four have
since resolved. The `C3.L2b` "next diagnostic" instructions — build, install,
run one cycle, re-read the report — were carried out and produced the E2
evidence. Kept as chronology; act on the current state above.
