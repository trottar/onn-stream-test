---
memory_schema: 1
as_of: 2026-09-24
status: TASK HANDOFF — C3.L3a rerun session 1 of 4 (run 20260924_115810, Crash Bandicoot, 19 marks): teach --finalize to score a run whose client stream restarted mid-run (two decoder sessions), keep every run's state file, record session 1 with the per-mark decoder check and the user's words, read the companion journal for the mid-run client restart; tools + documentation only, no companion / client / profile change, no session run; authorized by the user 2026-09-24
---

# C3-L3A-R1 — rerun session 1, recorded; finalize across a split client session

**Why.** The user played the first pre-registered rerun session
(`--traversals 10`, dwell 55-90, W 5.0, Phase B included): run
**`20260924_115810`**, seed 1368802297, Crash Bandicoot (USA), Phase A
815.974 s, 20 transitions, 10 decoys, **19 marks**, not aborted, restore
5000 → 7000 at 954.8 s. `--finalize` (12:17 local) scored the marks but
found **"no candidate (2 rejected)"** for the decoder session: the client
posted **two** reports during the run — `native_decoder_20260924_160232_200.json`
(received 16:02:32Z, 270.7 s, 9 SSRC changes) and
`native_decoder_20260924_161558_087.json` (16:15:58Z, 804.5 s, 15 SSRC
changes) — because the client's stream **restarted on its own ~3.4 minutes
into Phase A**. 9 + 15 = 24 = 20 Phase A + 3 parks + 1 restore. Neither
alone reaches the expected count, so the finalize skipped alignment and
the decoder-axis check. Cowork did the check by hand (below); the probe
must learn to do it. `--aggregate` already pooled the run (config is the
pre-registration). The state file in `logs/streaming/` is this run's and
will be overwritten by the next; copy it now.

Read first: `evidence/C3_L3A_P2R2_SMOKE_SESSION_2026-09-24.md`,
`evidence/C3_L3A_S1_TRANSITION_SOAK_2026-09-24.md` (the ~190 ms restart
gap at n = 60), `evidence/C3_L3A_P2R3_POOLING_RULE_2026-09-24.md`,
`decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md` §"The `C3.L4` gate",
`investigations/LINK_DROP_RECOVERY_DESIGN.md` and
`evidence/D_BASE_R3A_RESTART_FALLBACK_2026-09-20.md` (what a client-side
restart looks like in the journal), `TOOLS.md`.

**Scope.** Change only `tools/probe_c3_l3a_gameplay_acceptance.py`. No
companion, client, profile or route change; nothing in the environment; no
stream or session; companion not restarted. Never modify the state file, a
decoder session or a run file — copy, regenerate.

## Probe changes

1. **Split-session finalize.** When no single decoder session reaches the
   expected SSRC count, take **every** decoder session received after the
   run's start (`generated` minus Phase A minus Phase B, i.e. the run id's
   time) and before the finalize, in order, and use them together if their
   `ssrc_changes` **sum** to the expected count: align each session
   separately (its own offset from the fires that fall in it; spread ≤ 1 s
   each), score the per-transition table across them, and report the
   **client restart(s)** as events: probe time of the first session's end
   and the next session's start (this run: ~202.3 s and ~204.2 s), with the
   first session's close-out rows beside the second's. Each mark's decoder
   check uses the session that covers it. If the sum does not match either,
   say which count and stop the decoder-axis analysis as now.
2. **Keep the state.** At the end of every run, also write the state to
   `logs/streaming/c3_l3a_runs/states/<run_id>_state.json` (a
   subdirectory, so `--aggregate`'s glob does not see it). `--finalize`
   without `--state` prefers the run's own copy there when the shared
   state file's `run_id` differs.
3. Nothing else. Prompt text, scoring, windows, pooling rule unchanged.

## The record — `evidence/C3_L3A_R1_SESSION1_2026-09-24.md`

Re-run `--finalize --state <copy of this run's state> --decoder <both
files>` after the fix and record, from its output and the raw files:

- **Detection**, all three windows as the report prints them. At W 5.0:
  jump 3/5 (3 marks, 31.5 s exposure), ramp 4/5 (8 marks, 83.1 s), decoy
  jump-matched 1/10 (1 mark, 50.0 s), decoy ramp-matched 2/10 (2 marks,
  165.7 s), 8 marks in no sequence window; chance rate 0.0233/s; chance-
  expected marks jump 0.73 / ramp 1.94 / decoy-j 1.16 / decoy-r 3.86.
- **Every mark on the decoder axis** (Cowork's hand check, to confirm or
  correct): session 1 offset ≈ 68.47 s, session 2 ≈ 204.1 s (probe = decoder
  + 204.1). **Eleven marks — 7.582, 12.234, 78.021, 84.117, 88.868, 271.859,
  418.047, 502.367, 507.556, 591.830, 668.781 — each sit 1.4-2.9 s after a
  restart's output gap of 144-217 ms with `codec_ms` 6-13**, i.e. after a
  transition (lags from the fire 1.5-3.2 s). **Eight marks — 69.805, 114.364,
  251.466, 282.778, 386.488, 448.587, 455.663, 544.422 — have no slow event
  ≥ 50 ms in the 5 s before them** in either session: nothing the video
  path recorded. Say so; do not attribute them. (114.364 is 3.9 s after
  decoy 1; 386.488 is 13.6 s after decoy 4, inside its ramp-matched window
  only.) Lag histogram from the report.
- **The client restart at probe ~202-204 s — explained by the user
  (2026-09-24, their words): they pressed BACK by accident and resumed.**
  Record it as that, not as a fault; no `KNOWN_ISSUES.md` item. Confirm
  from the companion journal (`journalctl --user -u privyhub-companion`
  over 15:57-16:17Z, redacted) only that it reads as a client-ended session
  followed by a Resume of the same game (no encoder restart: SSRC changes
  24 = 24 expected, none extra; the host game stayed active and paused
  across the gap), and note how long the picture was gone. The user's
  earlier failed handoff (11:29-11:58 local: the game launched and sat
  paused for handoff until Resume) is a separate, also-explained event
  from the same afternoon. No mark fell within 5 s after the restart.
- **The two client sessions' close-out rows** (session 1 / session 2):
  spikes 121.9 / 42.0 per min, rendered fps 59.40 / 59.77, stale drops
  9.31 / 1.27 per min, video loss post-FEC 1.11 / 1.94 per min, max gap
  216 / 217, audio underruns 18 / 13, starvation 3 / 3. The first session's
  decode path was rough by every row; the second is the adopted build's
  usual. Beside the close-out C / W.
- **Phase B, as the state holds it and as the user said it.** The state:
  6000 acceptable `False` rating `None`; 5500 `False` / `None`; 5000
  `False` / 7 — the user pressed Enter through the y/N prompts while
  focused on the game (empty input = No / no rating), then typed 7 at the
  last. **The user's words, 2026-09-24, verbatim as stated, not a gate:**
  their ratings would be 6-7; they can't really tell which level was
  running; the roughest play was in the middle. The state file is not
  edited; the record carries both, and the pooled Phase B table must show
  this session's answers as "defaulted (accidental Enter); user's stated
  6-7, level not distinguished".
- **Lifecycle** 0 / 0 / 0 over 20; settling 10 of 10 (1.0-4.5 s, 5 at two
  reports, 5 at three); controller `lost_packets` 15 → 3,868 over the run
  (~230 / min, inside the zero-input band of `S1`).
- **Reading, pre-registered and unchanged:** this is session 1 of ≥ 4;
  the pooled table at ≥ 20 per shape is where the gate is read, by the
  user. State plainly what this session shows without a verdict:
  transitions marked 7 of 10 with a consistent ~2.3 s reaction lag behind
  measured ~190 ms restart gaps, decoys 1 of 10 jump-matched; 11 marks in
  transition windows against ~2.7 expected by chance; against it, the
  smoke's 0 of 4 on a shorter session and a different title. **`C3.L4`
  stays BLOCKED.**

## Evidence and memory

`evidence/c3_l3a_r1_2026-09-24/`: byte copies of the state file, both
decoder sessions, the session log (`c3_l3a_session_20260924_115810.log`),
the two refused-preflight logs (`…112950.log`, `…115753.log` — the
failed-handoff attempts), the finalize log, the as-finalized run files
(before the fix) and the regenerated ones (after), the journal extract
(redacted, `h2_prep_redact.py --check`), `sha256sum` manifest.
`patches/C3-L3A-R1_*.md` with per-file SHA-256s; regenerate
`patches/PATCH_INDEX.md`. `investigations/ACTIVE.md` §C3.L3a (session 1 of
4, one paragraph), `CURRENT.md` (Current Work Item: sessions 2-4 awaiting
the user; `python3 tools/check_memory_health.py` healthy), `2026-09-24.md`,
`handoffs/CURRENT_HANDOFF.md` one line, `TOOLS.md` (the state copies, the
split-session finalize, and one line: an accidental BACK mid-run splits
the client session; the run stays valid and `--finalize` now scores it).
No addresses or device identifiers in any file. Nothing committed.
