# Active investigations

## BASELINE STREAM HEALTH — ACTIVE

`BASELINE_STREAM_HEALTH.md`. The active line of work as of 2026-09-20.
Decision: `../decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md`. Evidence:
`../evidence/BASELINE_STREAM_HEALTH_2026-09-20.md`.

The reference stream is not healthy and never has been: ~70% of every frame
misses the 16.7 ms budget in every session on record, the stream never reaches
60 fps, and stalls reach 7.3 s. None of the three identified faults is a
bandwidth fault.

**Link-drop recovery, launcher semantics — RUNTIME VALIDATED
(`D-BASE-R3c2`, 2026-09-23):** recovery never loads into a live core; it
resumes into a fresh core loaded while running (the user's option A)
(`../evidence/D_BASE_R3C2_RECOVERY_FLOW_2026-09-23.md`). `R3`+`R3a`
are **RUNTIME VALIDATED for real loss** (`R3d`: N05, N15b, E30 PASS;
`END_MS` validated).

**Everything under "C3 Linux actuator boundary" below is SUSPENDED**, not
failed. The Linux actuator is real, measured and correct; it is a mechanism
awaiting a reason. Phase C resumes when the baseline target is met.

## C3 Linux actuator boundary — SUSPENDED 2026-09-20

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

- **The Windows-era UDP burst/gap pathology** — awaiting representative
  Linux replay of the saved acceptance suite. See `DEFERRED.md` and
  `docs/KNOWN_ISSUES.md` Entry 1. **`D-BASE-B2` narrowed it without
  closing it**: with the Windows PC out of the path the burst fell from
  11.17 to 4.46 packets per gap and loss/min from 46.3 to 16.6, but both
  arms overlap and the loss stayed bursty. Moot for the current host,
  which no longer routes through that machine; **not disproved**.

  **The Linux-path loss is a separate matter and it is closed**
  (`KNOWN_ISSUES.md` Entry 2). `P4` excluded the air as far as the client
  can see it (rho −0.022 at n = 597) and `O1` as far as the router can;
  `P5` excluded the onn's receive path (0 socket drops of 4,349); `P3`
  showed sender pacing insufficient at its 8 ms budget rather than
  ineffective; `P6` then **established the cause by intervention** —
  the frame-size tail — and `P6a`/`S3` adopted and soaked the fix.
- Adaptive FEC — C4.
- Linux host resource telemetry gap — recorded in `docs/KNOWN_ISSUES.md`; not an
  active investigation.
- **Thermal thresholds** — `D-BASE-T1` measured both ends and `S3`
  confirmed the plateau over three hours. No threshold, no throttle
  response and no action on a thermal reading exists, and none is
  authorized. Reopen with a sustained-load complaint.

## Open, not blocking

- **`D-BASE-R3b` — nftables loss injection, PARTLY RUN 2026-09-22.** The
  user drove `../evidence/d_base_r3b_2026-09-21/r3b_run.sh`
  (`af602621…21d2`) by hand; the classifier still refuses every `nft` write.
  **N3, N15 and N150 all PASS.** N15 got the criterion no substitute fault
  could reach — an encoder restart that **succeeded 9.45 s before the rule
  was deleted**, while the fault was still dropping every packet.
  `GIVE_UP_MS` and the `.state.recovery` save are now exercised; give-up
  landed at **120.42 s** against 120,000 ms. **`R3d` later: N15b PASS,
  E30 PASS (`END_MS` validated), N05 PASS (2026-09-23)** — `R3` +
  `R3a` RUNTIME VALIDATED for real loss. Two post-run defects opened. Evidence:
  `../evidence/D_BASE_R3B_NFTABLES_LINK_DROP_2026-09-22.md`,
  `../evidence/R3B_POST_RUN_SESSION_REUSE_2026-09-22.md`.
- **A recovery restart hides the outage from `lost_packets`
  (`D-BASE-R3b`, 2026-09-22).** 3 s with no restart = **2 348** lost
  packets; 15 s and 150 s **with** a restart = **22** and **40**, because a
  new ffmpeg brings a new SSRC and the client books the return as
  `ssrc_change` with `jump_packets: 0`. The `D-BASE` loss column
  under-counts every outage that restarted; **`max_output_gap_ms` is the
  honest column** — it tracked all three faults to within 60 ms.
- **`R3b-D1` / `R3b-D2` — the two post-run defects.** A `native-stream-stop`
  leaves the game session live and paused by design, so the launcher tile
  resolved to `recovery-resume` ("Loaded", **no window**, and no
  `POST /plugins/games/launch` was ever issued); and after a recovery-state
  load the **source picture cycles through about four frames** (IDR-size
  spread **3 686 B** against 52 923-74 242 B for gameplay and 0 B for a
  frozen window). Cause of the loop unresolved — load-while-paused ordering
  or Beetle PSX HW's GL state restore; needs a run.
  `../evidence/R3B_POST_RUN_SESSION_REUSE_2026-09-22.md`.
- **`H1` — the SSH console on the host. DONE, verified 2026-09-22.**
  Key-only SSH from the PC on the Opal wifi, LightDM autologin bringing up an
  active X11 `seat0` session, and `DISPLAY=:0` as the only export the
  companion needs. `../evidence/H1_VERIFY_SSH_CONSOLE_2026-09-22.md`.
  **adb is the new blocker for `H2`** — the onn is unreachable and its
  wireless-debugging port rotates, so only the user can reconnect, from the
  TV.
- **`H2` — the headless cutover**, gated on the user's word that the
  DisplayPort dummy plug is installed.
  `../handoffs/D-BASE-H2_TASK.md` was rewritten on 2026-09-22 from the
  read-only inventory in
  `../evidence/H2_PREP_HOST_DISPLAY_INVENTORY_2026-09-22.md`, which also
  found **no autologin** (a reboot stops at the LightDM greeter — no X
  session, no capture) and **nothing starting the companion at boot**.
  Both are user-side root writes and both block `H2`'s check 5.
- **The cause of the 55-60 ms audio arrival hole** (`D-BASE-P7`,
  2026-09-22) — **narrowed by `P8`** the same night: not the heartbeat, not
  the adb socket sampler; the path's (the AP's per-station scheduling is
  the remaining candidate, unmeasured). Lever unchanged: the +45 ms audio
  cushion, the user's call.
- `slow_events_marked` emitted empty while `slow_event_retained_marked` reports
  30 of 64.
- `tools/probe_c3_fixed_*_characterization.py --finalize` matched the wrong
  decoder-session file once, when run back to back after another bitrate's
  finalize. Intermittent. Check `payload.decoder_session_log` and
  `session_duration_ms` before using any finalize result.
- The cause of a 385 ms output gap in a session with zero 250 ms codec spikes.
  No work item owns it.

Both defects are in `docs/KNOWN_ISSUES.md`.

- **The starvation counter is named — `D-BASE-P7`, CHARACTERIZED
  2026-09-22.** Record:
  `../evidence/D_BASE_P7_STARVATION_COUNTER_2026-09-22.md`; patch
  `../patches/D-BASE-P7_AUDIO_HEARTBEAT_COUNTERS.md`.

  **`prolonged_starvation_events` counts holes in the audio arrival
  stream.** The code latches it — one increment per contiguous run of
  three or more empty 5 ms queue polls, i.e. **one per arrival hole longer
  than ~15 ms**, and never twice for the same hole. **That excluded the
  "poll-quantized duty cycle" reading before any data was taken**, and the
  data agreed: deltas of 0-5 per 2 s tick with **34 % of ticks at zero**.

  **It is jitter, not loss.** Over 596 ticks, rho **+0.684** against the
  per-tick maximum audio inter-arrival gap, **+0.020** against audio loss,
  **+0.036** against the packet deficit — which averages **+0.54 of ~400
  expected**, so **no packets are missing, they are late**. (Its +0.747
  against `concealed_underruns` is near-tautological and is reported only
  for completeness: that counter increments on every empty poll and an
  episode *is* a run of them.)

  **The hole is periodic and it is not the sender's.** 93 % of ticks have
  their largest gap between **50 and 69 ms** (median 55, p90 60), and only
  **6 of 596** stay under the threshold — while the host's audio pacer was
  measured at baseline at **5.0 ms average, p95 5.04, max 5.08**. **The
  jitter appears between the host's socket and the onn's.**

  **The PC-versus-Opal halving is explained.** 75.9/min PC-path (`S2`),
  35.8-40.7 Opal uncapped (`O1`), 32.0-32.5 Opal capped (`S3`, `P7`). An
  arrival-gap counter should change when only the path changes, and it
  does. The frame cap barely moves it, which is also right: audio is
  low-rate, evenly paced and small — never the bursty stream.

  **Read it as a path-jitter rate, not a fault.** 32/min accompanied **4
  actual underruns in 20 minutes**. The only client-side lever is a deeper
  cushion: the queue target is **3 packets (15 ms)** against a p90 hole of
  **60 ms**, so absorbing it costs about **+45 ms of audio latency** and a
  capacity raise. **Sender-side pacing is closed by measurement.** Nothing
  was implemented and the counter was not renamed — the name is accurate.

  **What it could not determine** is what *causes* the 55-60 ms hole: the
  instrument records one maximum per 2 s tick, so it cannot locate the
  hole inside the tick or align it with anything. Candidates it cannot
  separate are queueing behind the video burst, the AP's scheduling, and a
  client-side stall; the PC-vs-Opal difference argues against a purely
  client-side cause and no more.

- **Three hours on the cap — `D-BASE-S3`, SOAK VALIDATED 2026-09-22.**
  Record: `../evidence/D_BASE_S3_CAP_SOAK_2026-09-22.md`. No code change.

  **The cap holds for hours and the loss keeps falling.** 977 losses over
  180 minutes = **5.4/min**, lower than any 20-minute capped session
  (15.4 / 20.3 / 12.4) and ~25x below uncapped. **0 resyncs, 0 SSRC
  changes, 0 onn socket drops**, fps **59.96**, max forward gap 27
  packets. Hourly 380 / 340 / 253 — a 1.50x spread, under the 2.0 drift
  flag, and trending **down**.

  **The pre-registered residual question is answered: the residual is a
  floor.** Every Spearman is under **0.08** across 1,080 ten-second and
  180 per-minute windows — frame size, frame count, receive rate, Opal
  channel utilization — and the bucketed loss table is **flat** (0.80 /
  1.05 / 0.85 per window) where uncapped it rose 14-fold into the `>= 80`
  bucket. **A tighter cap is not a live lever**, which is also why `P6`'s
  60 KB arm tied on loss: there is no frame-size signal left to remove.
  0.011 % of packets are lost with no per-window structure, and nothing in
  these instruments distinguishes the windows that lose from those that do
  not. **The loss column is closed at this level.**

  **The finding that outranks the rest, per the task.** Two frames in 180
  minutes exceeded 90,000 bytes — by **11 and 9 bytes**. The driver's
  `max_frame_size` is a **target, not a hard ceiling**; `P6`'s 60 KB arm
  had already shown 60,092. It does not touch the mechanism: those frames
  are **~76 packets** against a >= 80 threshold, the session maximum was
  **77 packets**, and **no minute had a frame at 80+**. The practical
  consequence is for future checks, which should allow a small tolerance
  rather than test `<= 90000` exactly.

  **Rotation, first multi-hour test of the `P6` log.** Both bounded logs
  rotated **twice**; the frame-size series has **0 discontinuities across
  10,801 seconds** and the heartbeat slice holds 5,382 lines at 2,001-2,031
  ms. **Neither rotation lost a row.**

  **Thermals plateau** (k10temp 53/54/55 °C by third, amdgpu edge
  43/43/44, encoder CPU 27 % flat), as `T1` found. **But `S2`'s memory
  result does not fully reproduce:** RetroArch grew **+140.2 MB** of which
  **+34.3 MB anonymous**, against `S2`'s +119.9 MB with only **+6.2 MB**
  anonymous, still rising at the end. Majority file-backed, so "warm-up,
  not a leak" survives in its main claim — **but it is not the clean
  result `S2` recorded and should not be cited as one.**

  **The Opal, sampled at 20 s through the soak** (543 rounds, read-only):
  channel utilization mean **6.82 %**, range 0.0-56.6. **The 56.6 %
  excursion did not move the loss** (rho +0.073) — other traffic came and
  went and the stream did not notice.

- **The cap is adopted — `D-BASE-P6a`, RUNTIME VALIDATED 2026-09-22.**
  Record: `../evidence/D_BASE_P6A_CAP_ADOPTED_2026-09-22.md`; patch
  `../patches/D-BASE-P6A_FRAME_CAP_PROFILE_DEFAULT.md`; decision
  `../decisions/D-BASE-P6A_FRAME_CAP_ADOPTED.md`.

  **The user checked the picture and decided.** Playing the capped arm for
  about a minute on 2026-09-22 they reported no stutters and that they
  "could barely tell it was over the LAN" — **a user-stated perceptual
  result, recorded in their words and not upgraded.** With it they adopted
  the setting.

  **`max_frame_size_bytes = 90,000` is now a declared profile field**, not
  an environment override, honoured by the Linux `h264_vaapi` builder. All
  ten pre-registered gates passed on the first session with nothing set in
  the environment: **zero ≥ 80-packet frames**, max frame **89,874 B**,
  loss **249** (bound 600), bitrate **6,929.6 kbps**, fps **59.90**, zero
  resyncs, zero onn socket drops, zero relay send errors, encoder CPU
  **26.6 %**. The `≥ 80` bucket is absent from the conditional-loss table.

  **`PRIVYHUB_ENC_MAX_FRAME_SIZE=0` still runs uncapped** — proven, not
  asserted: a 60 s check produced a **90,438-byte** frame with the flag
  absent from the argv. That keeps the `P6` baseline reproducible without
  editing source, which is what makes adopting a measured setting safe.
  `any_override` changed meaning deliberately: it is **false when only the
  profile decides**.

  **A result worth carrying forward:** V1's per-minute loss correlates with
  nothing — not with the other capped sessions, not with the uncapped ones.
  `O1`'s content-lock (Pearson 0.964) **was a property of the tail**; with
  the tail gone the residual 249 packets are not content-driven and there
  is nothing left to lock onto. `D-BASE-S3` is the three-hour soak that
  asks what the residual *is*.

- **Control the frame-size tail — `D-BASE-P6`, CHARACTERIZED
  2026-09-21.** Record:
  `../evidence/D_BASE_P6_FRAME_TAIL_CONTROL_2026-09-21.md`; seven arms in
  `../evidence/d_base_p6_2026-09-21/`; patch
  `../patches/D-BASE-P6_FRAME_BYTE_COUNTERS_AND_ENCODER_KNOBS.md`.
  **`P5` correlated; `P6` intervened, and the loss followed.**

  **The transfer function is now demonstrated end to end: frame-size tail
  → large-frame incidence → wireless loss → forward gaps.** Capping the
  encoder's largest frame at **90,000 bytes** took the ≥ 80-packet
  population **718 → 0** and the loss **2,696 → 311**; on a second,
  adjacent pair **2,896 → 408**. That is **8.7x and 7.1x** against a
  pre-registered bar of 2x, with forward gaps 306 → 105 and the maximum
  forward gap 61 → 13-27 packets.

  **The bucket-specific pattern is what makes it causal.** Windows
  assigned to the bucket of their largest frame: in both baselines the
  **≥ 80-packet bucket carries 93-95 % of all loss** at **~14x the loss
  per window** of any bucket below it, and capping deletes that bucket
  **while the `< 40` bucket is not raised** (3.33 → 1.63, 4.62 → 2.88).
  The knee was measured first, not assumed: it is a **step at 100 KB** —
  46.3 loss/window above, 1.2-4.2 below — and the caps were chosen from it
  (A1 just under, A2 a third lower).

  **At no measurable cost.** Achieved bitrate **6,928.9-6,931.3 kbps
  across all seven arms** (0.03 %), encoder CPU **26.6-26.9 %**, GPU power
  overlapping. A cap does not starve the stream; it redistributes inside
  it. fps rose 59.58 → 59.88 and spikes fell 61.6 → 33-35/min.

  **Two bounds on the recommendation.** The benefit **saturates**: a
  60,000-byte cap, a third tighter, ties on loss (299 vs 311), so **the
  looser cap is the better setting** — same benefit, less constraint, less
  of the quality cost this run cannot see. And **conventional VBV is not
  the same lever**: `-bufsize` at the one-frame budget flattens hardest
  (every frame 14-16 packets, max 17,144 bytes, per-0.5 s bitrate range
  6,661-7,168 against the default's 64-15,792) yet loses **938** against
  the cap's 311, and it is **the only arm that raised loss in small-frame
  windows** (7.79/window against 3.33). It trades the tail for a higher
  floor and does not satisfy the pre-registered pattern.

  **Drift was flagged and the result survived it.** The three baselines
  came out **2,696 / 2,189 / 2,896** — a ±15 % spread, wider than the
  ~10 % the task allowed — but their **frame distributions are
  near-identical** (≥ 80: 718/717/734, max byte 242/245/247 KB), so the
  environment moved and the content did not, and each pair clears the bar
  against its own nearer bookend. **Bookend every future arm.**

  **What this run does not measure is the quality cost**, and the record
  says so plainly. `h264_vaapi` exposes **no achieved QP** here
  (`q=-0.0`); **`slices` and intra-refresh do not exist** in this encoder;
  the RC mode is **CBR**, read directly. The stand-in is the unchanged
  bitrate, and the cap binds on ~1 % of frames. **The perceptual check of
  the best arm is the user's own step before anything is adopted.**

  **Nothing was adopted.** Both knobs (`PRIVYHUB_ENC_MAX_FRAME_SIZE`,
  `PRIVYHUB_ENC_BUFSIZE_K`) default off; the run ended on the default,
  verified by an argv diff against A0 and a final `status` read showing
  `any_override: false`.

- **Which queue drops the burst — `D-BASE-P5`, CHARACTERIZED
  2026-09-21.** Record: `../evidence/D_BASE_P5_WHICH_QUEUE_2026-09-21.md`;
  instruments, series and analyses in `../evidence/d_base_p5_2026-09-21/`;
  patch `../patches/D-BASE-P5_RELAY_FRAME_SIZE_COUNTERS.md`. Three
  instruments on one clock — frame size from the relay, the onn's
  `/proc/net/udp6` receive-queue `drops` over adb, and the `R5` heartbeat
  loss counters — across two 20-minute attract-mode sessions.

  **The onn's receive path is not the queue.** Its UDP socket discarded
  **0 datagrams in 40 minutes**: 0 of 4,349 lost packets, **0 of 240**
  ten-second windows, on the video and the audio socket both. `rx_queue`
  peaked at **480 KB of a 2 MiB buffer** — a quarter used at its worst.
  Below the socket, `wlan0` `rx_errors`, `rx_missed_errors`,
  `rx_over_errors` and `rx_fifo_errors` are **all +0** and device-wide UDP
  `RcvbufErrors` **+1** in twenty minutes. **A larger client receive
  buffer is not a fix**, and that is now ruled out rather than assumed.

  **One counter looks like the answer and is not.** `wlan0 rx_dropped`
  advances **+36,988** over a session — **16.6x** the loss — but does not
  track it: per minute Spearman **0.040**, Pearson **−0.123**, ranging
  203-8,154 against a loss range of 0-293, with every hardware error
  counter beside it at zero. It is the Android broadcast/multicast filter.
  **Never read it as stream loss.**

  **The loss tracks the frame-size tail.** Max packets per frame rho
  **0.583** over 240 ten-second windows and **0.780** over 40 minutes;
  `frames >= 80 packets` **0.569** / **0.779**; forward-gap events the
  same. **Frame rate and mean frame do not move at all** — 599-601 frames
  per 10 s, mean 12.96-14.20 — so nothing about the *volume* of traffic
  changes. Only the tail does, and the loss goes with it. `frames >= 80`
  is the better statistic than the maximum: a per-window maximum is an
  extreme value and saturates, a count does not.

  **The control held, with one honest miss.** Frame size reproduces across
  sessions **more tightly than the loss does** — `frames_ge_80` Pearson
  **0.996**, `frames_ge_40` 0.991, mean 0.939, against loss **0.890**.
  That is the right way round for the account to survive. But the task
  pre-registered loss agreement at Pearson **> 0.9** and this pair came in
  at **0.890**, just under (`O1`'s pair was 0.964). Recorded as a miss.

  **The distribution a fix has to flatten**, ~72,600 frames a session at
  CBR 7000 kbps: **p50 11, p90 29, p99 82/78, max 207/208** packets, with
  **4.0 %** of frames >= 40 packets and **1.0 %** >= 80. **The shape is
  the problem, not the rate**: a nineteen-fold spread between the median
  and the p99, emitted back to back at line rate.

  **By elimination the queue is the wireless hop** — the AP's per-station
  queue or the air during the burst. **Not observed directly, and it
  cannot be on this AP**: `O1` established that its `tx failed` is a copy
  of `tx retries`, so retry exhaustion — the air's own way of discarding a
  frame — is unreadable. The case is that everything else on the path now
  reports zero and the one thing that moves with the loss is how big the
  burst is. It also explains **`P3`'s bounded null** (its 8 ms budget
  clamps above 53 packets a frame, exactly this tail) and **`O1`'s
  audio/video split** (0.024 % against 0.214 % on one radio).

  **Levers, all upstream, all the user's, each with a cost:** encoder VBV
  (`-maxrate` with `-bufsize`) — the direct lever, costs quality on scene
  changes; a smaller IDR spike or periodic **intra-refresh** — costs
  compression efficiency and needs the resync path re-tested; a **pacing
  budget that actually spreads a 60-80-packet frame** — costs latency
  directly, +41 % spikes at 8 ms.

  **Two instrument traps, both caught in smoke runs before the real
  sessions, both of which would have produced a confident wrong answer:**
  the client's Java `DatagramSocket` binds the IPv6 wildcard, so
  `/proc/net/udp` alone shows the stream's ports in **none** of 76 rounds
  — read **`udp6`**; and a row in either file has **thirteen** fields, not
  the fourteen the header names, because `tx_queue:rx_queue` and
  `tr:tm->when` are each one colon-joined token, so read `drops` as the
  **last** field.

- **The Opal's view of the air — `O1`, CHARACTERIZED 2026-09-21.** The
  user installed the key, `ssh opal` authenticates, and the Opal was read
  **read-only** beside two 20-minute attract-mode sessions (40 minutes, 269
  sampling rounds at 10 s, 1,196 heartbeats). Record:
  `../evidence/O1_OPAL_AIR_VIEW_2026-09-21.md`; sampler, raw rounds and
  four analyses in `../evidence/o1_2026-09-21/`. **No patch — no code
  changed.**

  **The first thing checked, per the task, and it is closed:**
  `iw dev sta0 link` and `iw dev sta1 link` both return **`Not
  connected`**. Neither managed-mode interface carries an uplink, so **the
  5 GHz radio is not time-shared** and the possibility that outranked
  everything else here is gone.

  **Neither the air nor the Opal is implicated** — the pre-registration's
  third branch. Client loss swung **0-331/min** while every Opal reading
  stayed flat: channel utilization rho **−0.434** per minute (and on the
  *wrong sign* — a busier channel goes with less loss), **−0.008** at the
  sampler's own 10 s cadence, `tx retries` **+0.219**, `rx drop misc` and
  **every** `dropped`/`errors` counter on `wlan1`, `br-lan`, `eth0` and
  `eth0.1` **constant 0** for 40 minutes. The 24 worst 10 s windows read
  **6.78 %** utilization against **6.94 %** in the 141 that lost nothing.
  In absolute terms **the channel is ~93 % idle while streaming** (2.9-3.3
  % idle → 6.9 % under load), so sustained contention is not merely
  uncorrelated, it is **not present**. Retries run **10.2-11.3 %** of tx
  packets at −70 dBm and do not track loss.

  **And the run found something larger than its own question. The loss is
  reproducible.** The per-minute series of the two sessions, started three
  minutes apart, agree at **Pearson 0.964** (0.951 at 30 s, 0.886 at 10 s;
  forward gaps 0.783) while their totals differ (2,230 vs 2,040). Each
  session relaunches the title, so the attract loop replays and **the loss
  follows the replay**. `D-BASE-R5`'s "episodic" meant
  bursty-within-a-session — it is **not random**, and **no wall-clock
  account can produce a shape that repeats on restart**. Do not run another
  environmental hypothesis at it.

  **Where it points.** Video loses **0.225 %/0.206 %** while audio, over
  the same radio, AP and station in the same second, loses **0.077
  %/0.028 %** — the bursty stream selected over the paced one, which is
  what a burst-meets-a-queue account predicts and a degraded-air account
  does not. The encoder is **CBR** (6,901-6,957 kbps, Pearson −0.19/−0.31
  against loss) so average rate is not the driver; its sub-second
  burstiness is itself content-locked (**0.911** across sessions) and
  tracks loss at only **0.40** — 0.5 s is far too coarse to see the
  per-frame burst, so this is consistent with `D-BASE-P3`'s bounded null,
  **not a demonstration of it**.

  **What it could not settle, and why.** Three counter traps on this AP,
  all in `../TOOLS.md`: `survey dump` does **not** accumulate (a fixed
  29-30 ms window, never to be differenced); `channel utilization` is that
  window rounded, quantised in 3.33 % steps at a **0.3 % duty cycle**, so
  sub-second contention is invisible; and **`tx failed` is not independent
  of `tx retries`** (their difference held at 6,790 → 6,792 across four
  hours and 240,000 retries). **Retry exhaustion — the air's own way of
  dropping a frame — is therefore unreadable here**, and that is precisely
  the instrument that would separate the AP's per-station queue from the
  onn's receive path. Both remain live suspects. **The next measurement is
  client-side and costs no hardware:** sample the onn's `/proc/net/udp`
  `drops` for the stream socket per minute beside the heartbeat series.

  **Levers, all the user's, none of them code.** The air levers have lost
  most of their motivation at ~7 % occupancy; the one with a rationale left
  is **40 MHz width** against the 10-11 % retry rate at −70 dBm, then
  placement. Nothing here indicts this access point. **Sender-side pacing
  with a larger frame budget** (`P3`) is now the best-supported lever and
  costs latency.

  **Privacy: two redaction defects were found and fixed mid-run**, both
  after leaking to a terminal once — an IPv6 pattern that ate bare
  `HH:MM:SS` clocks, and SSID/secret patterns that missed `uci show`'s
  `…ssid='…'` and `.key='…'`, so one `uci show wireless` printed both SSIDs
  and both WPA passphrases in clear. Closed in `o1_redact.py`; **nothing
  was written**, and no address, MAC, BSSID, SSID, key or device identifier
  appears in any stored artifact.

- **Heartbeat loss counters — `D-BASE-R5`, RUNTIME VALIDATED 2026-09-21.**
  The receiver's cumulative loss counters now ride the existing 2 s
  heartbeat, so **the project has a per-minute loss series for the first
  time.** Client heartbeat payload only, plus companion passthrough;
  nothing new is sampled, counted or threaded, and the counters are the
  same ones the end-of-session report reads. Evidence:
  `../evidence/D_BASE_R5_HEARTBEAT_LOSS_COUNTERS_2026-09-21.md`; patch:
  `../patches/D-BASE-R5_HEARTBEAT_LOSS_COUNTERS.md`.

  **Every check passed on one 20-minute session.** 597 heartbeats, all
  carrying all seven fields under schema
  `privyhub_native_stream_heartbeat_v2`; **all seven loss counters at the
  last heartbeat match the report exactly**; and the series accounts for
  the report to the packet — 2,212 + 6 head + 0 tail = **2,218 = the
  report's 2,218**. `rx_packets` is the only field that differs (1,310),
  and it should: 1,641 ms of stream followed the last heartbeat.

  **What it immediately showed.** Per-minute loss inside one session ran
  **0 to 303 packets**, median 87, with burst minutes 4, 6, 12, 17 and 18 —
  while RSSI spanned **−65 to −67** and `txLinkSpeed` read **260 in twenty
  of twenty-one minutes**. **Minute 6 lost 303 packets and minute 15 lost
  none, at the same RSSI and the same link speed.** That reproduces
  `D-BASE-P4`'s conclusion at sixty times the resolution with a direct
  measurement instead of an inferred one, and confirms the loss is
  **episodic within a session**, not only between sessions.

  **Live watching works too:** `native-stream-status` carries
  `loss_per_min_recent`, sampled six times mid-session at 158, 205, 76,
  125, 24 and 87 per minute, each on a 60.2-60.3 s window of 31
  heartbeats. It returns **None, never 0**, when unmeasurable.

  **Cost: none that shows.** The heartbeat line grew 276 → **465 bytes**
  and `spike_20_ms`/min came out **51.5**, inside `D-BASE-P4`'s 40.6-62.4
  range, with fps 59.70 and no discontinuities.

  **Two side findings.** The bigger line took heartbeat-log growth from
  ~453 to **~819 KB/h**, which **rotated the log 17.9 minutes into the
  session — the first time rotation has run against real traffic.** It
  lost nothing (sequence step 1, elapsed step 2,007 ms), which closes a
  standing `KNOWN_ISSUES` item; but it also **broke the harness's
  offset-based log slice**, because rotation makes the file shorter than
  the offset. Read the archive and the live log together and filter on a
  rising `elapsed_ms` run (`../TOOLS.md`). Separately, `TOOLS.md`'s
  Android build line was wrong — **the Gradle wrapper is in `PrivyHub/`,
  not the repository root** — which cost this task a build; corrected.

- **Air telemetry — `D-BASE-P4`, CHARACTERIZED 2026-09-21: not the air.**
  The first measurement of the radio rather than of symptom counts at the
  decoder. Host-side sampling over adb, **no code change anywhere**; the
  sampler is a script under `../evidence/d_base_p4_2026-09-21/`, not a
  companion feature.

  **The gate passed — the onn is on 5 GHz**, 5180 MHz, **channel 36, 80 MHz
  wide**, 802.11ac, an 866 Mbps ceiling, supplicant `COMPLETED` and **never
  re-associated** across seven sessions. Had it been on 2.4 GHz that alone
  would have been the finding; it was not.

  **Seven sessions (six 120 s, one 20-minute), none rejected.** Loss/min
  swung **1.4 → 105 (74x)** while the radio sat still: RSSI spanned **5 dB**
  over 639 three-second samples with a median of **−66 in every session**,
  and **not one scan of any kind** fell inside any session window. Inside
  the 20-minute session, at **n = 597** heartbeat ticks, the client's
  receive rate against RSSI gives **rho = −0.022**, against Tx link speed
  **−0.001**, against Rx link speed **−0.001**; the 5 % of ticks more than
  10 % below median rate **all sit at ordinary RSSI**. Those are not
  small-sample nulls.

  **Half the pre-registered test could not be run, and that bounds it.**
  This device exposes **no retry, failure, airtime or channel-occupancy
  counter**: `tx_retry`, `tx_bad` and `bcnCnt` are identically 0 across
  3,600 score-report rows, `total_tx_retries`/`total_tx_bad` likewise, the
  `/proc/net/wireless` discard columns and missed-beacon count are 0,
  `noise` is −256, `channel_utilization_ratio` is a **constant 15**, and
  `iw`/`wpa_cli` are absent. **So signal strength, association stability,
  link-rate selection and background scanning are excluded as the cause —
  interference and airtime contention are not excluded, they are invisible
  from here** and need the Opal side or a client that reports retries.

  **The 20-minute session is the substantive find.** It lost **105/min at
  14.89 packets per gap**, against 3.0-7.0 in the two-minute ones — **bigger
  bursts over a longer observation.** The loss is **episodic, and short
  sessions sample it badly**, which accounts for `D-BASE-P3`'s 1.8-35.2
  control-arm swing as sampling variance better than anything about the
  radio does. **Two-minute sessions are the wrong instrument for the loss
  column**, and that changes how future runs should be sized.

  **No per-minute loss series is available and none is presented.** Built
  from `relay_rtp − client_rx` deltas its noise sd is **86 packets per 10 s
  window against a 3.0-packet signal**, and windows come out negative,
  because the `native-stream-status` heartbeat snapshot lags up to 2 s.
  Loss stays a per-session figure from the report unless the client gains a
  per-tick loss counter — which this task forbade adding.

  **Levers, none of them code and all the user's:** band and background
  scanning are already where you would put them; **channel 36 and the
  80 MHz width are the untested ones**, each a single Opal setting;
  placement would buy rate headroom (the link runs 195-260 Mbps against an
  866 ceiling at −66 dBm) but the data does not say it would buy less loss.
  Evidence: `../evidence/D_BASE_P4_AIR_TELEMETRY_2026-09-21.md`; how to read
  the onn's radio at all is now in `../TOOLS.md`. No patch — nothing changed.

- **Sender pacing — `D-BASE-P3`, INDETERMINATE 2026-09-21, not adopted.**
  Tests whether the ordinary loss is the host's own per-frame micro-burst
  overflowing the wireless queue: the encoder emits a frame's packets back
  to back, so spreading them should cut loss and burst size if that account
  is right. **The knob is `PRIVYHUB_FEC_PACING_US`** — environment, read at
  relay `start()`, **default off** — queueing a frame's packets by RTP
  timestamp and sending one every N µs, parity after its group, clamped to
  `8000 µs / packets-in-frame` so a frame is out within 8 ms of its first
  packet arriving. Off is the old path byte-for-byte, asserted by an
  offline check. Fifteen 120 s sessions, **strictly alternating with the
  companion restarted for each**, 0 rejected, 0 discontinuities.

  **Not implicated on the pre-registration:** loss/min fell in **3 of 5**
  pairs against a bar of 4, medians **1.72x** (loss) and **1.70x** (packets
  per gap) against a bar of 2x, and **`spike_20_ms`/min rose in 5 of 5**,
  which the criterion forbids. **Not ruled out:** packets per gap fell in
  **4 of 5** and the median max forward gap **halved, 16 → 8**. **Mixed.**
  **The one reproducible result is a cost** — spikes **42.7 → 60.1
  (+41 %)** — though `max_rx_to_decode_ms` *fell* 137 → 112 and fps held.
  **It does not scale**: at 400 µs the achieved spacing is only 187.5 µs,
  30 % of frames clamped, loss fell in 0 of 2 pairs.

  **Two bounds on that null, and they matter more than the null.** The
  clamp bites above 53 packets/frame at 150 µs and the mean frame is 15.85,
  so **the large frames a queue-overflow account blames are exactly the
  ones the 8 ms budget refuses to spread** — a stronger test needs a larger
  budget, which costs latency and is the user's call. And the off arm swung
  **1.8-35.2 loss/min inside one hour**, so five pairs cannot resolve 1.7x.
  **Adoption is a product decision, with the cost measured and the benefit
  not established; the knob ends at 0.** Evidence:
  `../evidence/D_BASE_P3_SENDER_PACING_2026-09-21.md`; patch:
  `../patches/D-BASE-P3_FEC_RELAY_SENDER_PACING.md`.

  Also recorded: **`time.sleep` cannot pace this stack** (~55 µs overshoot
  floor), and **the onn asks for a 2 MiB receive buffer and never reads
  back what it got** (`RtpH264Receiver.kt:573`); its `rmem_max` is 8 MiB,
  so nothing clamps the request. The client was not changed.

- **Host on the Opal — `D-BASE-B2`, INDETERMINATE 2026-09-21.** The
  production topology is measured at last. Gate checked on the host first:
  default route on its one wired interface, the gateway answering as the
  Opal (vendor OUI, Dropbear / nginx / local-DNS banners), host and onn on
  one subnet, adb reaching the onn, the host's internet through the same
  gateway — **host wired -> Opal -> onn wireless, one hop**, the Windows
  PC out of the path. Six attract-mode sessions, 120 s, zero input, no
  code change. **Loss/min median 16.6 against the PC path's 46.3** (2.8x,
  not the order of magnitude the pre-registration required), **packets per
  gap 4.46 against 11.17** (lower, but still four times uniform loss),
  forward-gap events 7 against 11. **The arms overlap** — the PC arm spans
  0.0-206.7 loss/min and contains the Opal range 7.0-24.1, with A60/B60/C60
  quieter than all six — so **no verdict is claimed on the Windows PC**,
  against a Group A day-to-day swing of 12.6x. Every transport column did
  move together (max gap 2.84x, max output gap 1.75x, spikes 1.82x) and the
  Opal arm is far tighter. Four of six target rows pass; **`max output gap`
  (139-231 ms) and loss/min still fail, both transport.** The deferred UDP
  burst/gap pathology is **not** resolved: the burst shrank, it did not go
  away. Evidence: `../evidence/B2_HOST_ON_OPAL_2026-09-21.md`; reports and
  harness in `../evidence/b2_2026-09-21/`. No patch — nothing changed.

  **It also falsified `C5a`'s durable fact.** A single 3 s `SIGSTOP`
  produced a **690-packet `sequence_resync` with `restarts` 0 and
  `ssrc_changes` 0** — no restart, no new SSRC — which the claim "cannot
  produce a sequence resync at any pulse length short of tripping a
  restart" forbids. The heartbeat gives the mechanism: `rx_packets` ticks
  of 393 and 1,161 against ~1,650 steady, then a **resume burst of 2,587**.
  **The packets were minted and then dropped on the burst, so the boundary
  is the burst's size, not a restart.** The 0.3 s case survives.

- **Thermal telemetry, both ends — `D-BASE-T1`, RUNTIME VALIDATED
  2026-09-21.** Diagnostic only; nothing acts on a temperature. **The onn
  reports thermal *status* only**: `getCurrentThermalStatus()` works and
  read **0 (NONE) for the whole of both 10-minute sessions**, while
  `getThermalHeadroom(10)` returns **NaN** on SDK 34 and
  `/sys/class/thermal` is **permission-denied** even to the adb shell, so
  `zones_readable` is 0. Recorded as absent, never faked. The host warms
  the way `D-BASE-S1` saw — hottest sensor **54 → 60 °C** over ten minutes,
  `k10temp` always the hottest — so **the host warms and the onn does not
  report warming, and status alone cannot tell "cool" from "silent"**.
  New and durable: `tools/host_resource_sampler.py`, started and stopped by
  the companion with every native stream session, so future sessions carry
  a host series with no harness; `host_thermal_c` on
  `native-stream-status` and in each decoder session log. A thermal pause
  on the recovery state machine is **deferred with a reopen condition**
  (`DEFERRED.md`). Evidence:
  `../evidence/D_BASE_T1_THERMAL_TELEMETRY_2026-09-21.md`; patch:
  `../patches/D-BASE-T1_THERMAL_TELEMETRY.md`.

- **Three-hour session — `D-BASE-S2`, CHARACTERIZED 2026-09-21.** One
  uninterrupted 3 h session on the PC path, completed cleanly, and it
  settled three open items. **RetroArch memory is not a leak**: the
  +108 MB/30 min S1 saw is the first block only (+110.2 of +119.9 MB total)
  and is **file-backed** — `RssFile` +113.6 MB against `RssAnon` **+6.2 MB
  in three hours** (~2.1 MB/h), `VmSwap` 0, `MemAvailable` *higher* at the
  end. The companion plateaus too (+6.8 MB, ~0.18 MB/30 min after
  startup); the encoder is flat. **Nothing drifted for 150 minutes** (fps
  by 30-min block 59.53 / 59.71 / 59.62 / 59.71, encoder CPU Spearman
  -0.012); the last 30 min fell only because the link broke.
  `prolonged_starvation_events` **75.9/min**, unchanged across a 90x range
  of session lengths, and `avg_queue_residence_ms` 27.86, unmoved.

  **The degraded tail did what no injection could.** Seven natural
  `desync_pause` events, **four on the host-side `controller_silence`
  trigger** — which `MEMORY.md` recorded as untestable without stopping the
  client — all seven resumed, and one **`method: "restart"` encoder restart
  succeeded during a live 78-second outage** (the `D-BASE-R3b` N15
  criterion, obtained naturally). `GIVE_UP_MS`, `END_MS`, the recovery save
  and its prompt remain unexercised. **And the `C5` hypothesis is
  FALSIFIED** — see below. Evidence:
  `../evidence/D_BASE_S2_THREE_HOUR_SESSION_2026-09-21.md`.

- **Overnight soak — `D-BASE-S1`, CHARACTERIZED 2026-09-21.** Four 30 min
  sessions, two hours of streaming on the **PC path** (host -> Windows PC ->
  Opal -> onn), all four completed. **No stream metric degrades with
  elapsed time**: per-minute fps Spearman -0.298 / -0.127 / -0.119 / +0.246,
  **not one output gap over 1 s in two hours**, encoder CPU flat at 26-27 %,
  loss 114.8-128.5/min with no within-session trend. **Memory does grow**:
  RetroArch **+108 MB per 30 min** (Spearman 0.89-0.98, reproducible 4/4,
  resets on restart), companion +4.5-6.4 MB, encoder +0.5-3 MB. Thermals
  ramp to a plateau (CPU 42 → 58 °C). `prolonged_starvation_events` is
  **linear at ~75/min from the first tick, with the queue full** — same
  rate as 2-minute sessions, still unexplained. Three natural resyncs, all
  jumping exactly 128 packets, all 168-222 ms, all `rejected_idr_aus` 0 →
  `C5a` stays INDETERMINATE (five natural resyncs now, one over 250 ms,
  none rejecting an IDR). **Zero `desync_pause`**; neither log rotated
  (archive empty), so `D-BASE-R4` rotation is still only synthetically
  tested. Reference for the morning's `B2`. Evidence:
  `../evidence/D_BASE_S1_OVERNIGHT_SOAK_2026-09-21.md`.

- **Audio startup hold — `D-BASE-P2a`, RUNTIME VALIDATED 2026-09-21.**
  The P2 fix works and is now fully accepted: `audio.underruns` median
  **6** against 207, 0-3 in the first three seconds, `first_write` moved
  7 ms. Its two open checks were closed by **`D-BASE-P2b`** — ten sessions,
  five matched pairs, strictly alternating against a build with the hold
  compiled out. That build measures `prolonged_starvation_events`
  **125-157, median 151**, the same band the fix was blamed for; pooled
  Spearman against run index **-0.036** (not drift either); sign test 3 of
  5; `avg_queue_residence_ms` 27.70 off against 27.62 on, so the proposed
  shifted-queue mechanism is absent. Both arms clear the fps bar on a quiet
  link (59.53 off, 59.56 on) and the underrun result replicated (276 off,
  19 on). Evidence:
  `../evidence/D_BASE_P2A_AUDIO_STARTUP_HOLD_2026-09-21.md` and
  `../evidence/D_BASE_P2B_STARVATION_SEPARATION_2026-09-21.md`; patch:
  `../patches/D-BASE-P2A_AUDIO_STARTUP_HOLD.md`.

  **Still open: `prolonged_starvation_events` itself.** A second
  phenomenon (`D-BASE-P2`), insensitive to the startup hold, no run-order
  trend, 125-157 per 120 s on a quiet link, not following video loss. No
  work item owns it and nobody has related it to anything audible.

- **Audio underrun burst — `D-BASE-P2`, CHARACTERIZED 2026-09-20.** A
  median 98.7 % of a session's underruns fall in the first 3 s, ending when
  the audio queue first fills; the burst is over before the stabilization
  gate releases. "113/min" was a fixed burst divided by a short session.
  `prolonged_starvation_events` is a separate, unexplained phenomenon.
  Hypothesis (the AudioTrack starts ~1.7 s before the stream flows) and a
  candidate fix are stated, **neither implemented**. Evidence:
  `../evidence/D_BASE_P2_AUDIO_UNDERRUN_BURST_2026-09-20.md`; probe fields:
  `../patches/D-BASE-P2_AUDIO_TICK_SERIES_PROBE.md`.

- **IDR-rejection counters — `C5a`. The question is now ANSWERED and the
  `C5` hypothesis is FALSIFIED (2026-09-21, `D-BASE-S2`).** 94 natural
  sequence resyncs fired the counters for the first time
  (`idr_aus_rejected_waiting_for_idr` 10). **Six of the seven retained
  resyncs over 250 ms rejected zero IDRs**, longest 1,340 ms, and one at
  **240 ms rejected one** — impossible if a rejection costs a further GOP.
  The long tail tracks `dropped_non_idr_aus` (40-67 on the longest rows):
  waiting for an IDR to *arrive* on a lossy link, not discarding damaged
  ones. p50 resync-to-IDR **71 ms**. **`C5` §5's bounded fallback is
  retired.** Across `P2b`, `S1` and `S2`, 69 natural resyncs, 66 rejecting
  zero IDRs. The `C5`
  §4 probe is built, installed and **proven wired** (a control session
  using the C3.L1 encoder-only restart drove four resyncs at 18-24 ms, each
  row carrying `rejected_idr_aus` / `dropped_non_idr_aus`). The verdict is
  indeterminate because no injection available without root produced a
  sequence resync **at the 0.3 s pulse length used**: a short SIGSTOP is a
  gap in *time*, not in *sequence*. Three 150 s sessions, largest forward
  gap 47 packets against a 128 threshold, zero resyncs. **`D-BASE-B2`
  falsified the general form of that claim at 3 s** (690-packet jump, 0
  restarts, 0 ssrc changes) — the boundary is the resume burst's size. Four discontinuities against a
  pre-registered floor of six, none over 250 ms. **Counters stay in to
  accumulate against natural resyncs; the bounded fallback is NOT
  implemented.** Evidence:
  `../evidence/C5A_IDR_REJECTION_COUNT_2026-09-21.md`; patch:
  `../patches/D-BASE-C5A_IDR_REJECTION_COUNTERS.md`.

- **Receiver resync and IDR acceptance — battery `C5`, COMPLETE 2026-09-20,
  analysis only.** The 195-332 ms is one GOP of unavoidable wait plus, in
  ~31 % of resyncs, one or more further GOPs because the completeness gate
  discards an IDR that lost a packet. Corpus: 104 sequence resyncs, p50
  204.5 ms, p90 484.2, max 2,555, 32 beyond one GOP; 47 actuator IDRs at
  p50 27 ms, none beyond 76. Read:
  `C5_RESYNC_IDR_ACCEPTANCE_READ_2026-09-20.md`. The rejection counter
  proposed there is now built (`C5a`, above); the bounded fallback remains
  **unauthorized**.

- **Stale-drop threshold — `D-BASE-P1`, CHARACTERIZED 2026-09-20, no change
  made.** The 60 ms policy discards 0.1-0.3 % of frames on the current
  build, so raising it cannot recover more than ~0.18 fps and measurably
  recovers none; p90 of rendered-frame latency does not move. Group A's
  "3.5 fps deficit from the stale policy" was a pre-`C3.L2c` measurement.
  Evidence: `../evidence/D_BASE_P1_STALE_THRESHOLD_2026-09-20.md`; the
  probe knob (product default 60, stays in the tree):
  `../patches/D-BASE-P1_STALE_THRESHOLD_PROBE_KNOB.md`.

- **Session-report visibility — `D-BASE-R4`, CLOSED 2026-09-20, RUNTIME
  VALIDATED.** A gap that never ends is now recorded
  (`terminal_slow_event`, `output_age_at_end_ms`); two top-16 lists keep a
  long session's worst events; the `slow_events_marked` defect turned out
  to be already gone; both native-stream logs rotate and are covered by
  `tools/diagnostic_retention.py`. Evidence:
  `../evidence/D_BASE_R4_REPORT_VISIBILITY_2026-09-20.md`; patch:
  `../patches/D-BASE-R4_SESSION_REPORT_VISIBILITY.md`.

- **Link-drop self-recovery — `D-BASE-R3`, IMPLEMENTED 2026-09-20,
  classification DEVELOPMENT.** Authorized and built: the host pauses on
  desync, restarts the encoder with backoff, resumes only after the client
  passes the stabilization gate again, and after `GIVE_UP_MS` saves to
  `<stem>.state.recovery` (never a slot) with a launcher prompt on return.
  Design and constants: `LINK_DROP_RECOVERY_DESIGN.md`. Evidence:
  `../evidence/D_BASE_R3_LINK_DROP_RECOVERY_2026-09-20.md`. Patch:
  `../patches/D-BASE-R3_LINK_DROP_SELF_RECOVERY.md`.

  **Both `D-BASE-R3` defects are fixed by `D-BASE-R3a`** (2026-09-20):
  a failed encoder restart now falls back to the full start path
  (`method: "full_start"`), and the restart trigger needs two rising,
  fresh heartbeats (`age_pair_ms`). Evidence:
  `../evidence/D_BASE_R3A_RESTART_FALLBACK_2026-09-20.md`; patch:
  `../patches/D-BASE-R3A_RESTART_FALLBACK_AND_TRIGGER_FRESHNESS.md`.

  **Runtime validated for the SUBSTITUTE fault only — the nftables runs are
  owed.** Every run so far stopped the encoder instead of dropping packets
  on the wire, because this host has no non-interactive root, so loss,
  sequence jumps and FEC during an outage are untested. Also open: the
  host-side controller-silence trigger and `END_MS`, both unexercised.


## Superseded — the 2026-09-18 open state (history)

Before `C3.L2a` E2, this file recorded `C3.L2a` as open with the question
unanswered, `C3.L2b` as code-installed with no runtime evidence, `C3.L2c` as
registered but unauthorized, and `C3.L4`'s gate as `C3.L2a`. All four have
since resolved. The `C3.L2b` "next diagnostic" instructions — build, install,
run one cycle, re-read the report — were carried out and produced the E2
evidence. Kept as chronology; act on the current state above.
