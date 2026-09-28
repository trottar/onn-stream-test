---
memory_schema: 1
as_of: 2026-09-24
status: TASK HANDOFF — C3.L3a rerun session 2 of 4 (run 20260924_130016, 26 marks, pooled): record it; the client posted NO decoder session for it (BACK was pressed, nothing is running) — find out from the companion journal whether the client attempted the post, record the session with the marks-only detection table and the decoder check as NOT POSSIBLE, open a KNOWN_ISSUES item if the client silently failed to post; tools + documentation only, no companion / client / profile change, no session; authorized by the user 2026-09-24
---

# C3-L3A-R2 — rerun session 2, recorded without a decoder session

**What happened.** The user played rerun session 2: run **`20260924_130016`**,
seed 118334293, Phase A 788.366 s, 20 transitions, 10 decoys, **26 marks**,
not aborted, restore 5000 → 7000 at 926.698 s; state copy at
`logs/streaming/c3_l3a_runs/states/20260924_130016_state.json`; session log
`logs/streaming/c3_l3a_session_20260924_130016.log`; finalize logs
`c3_l3a_finalize_20260924_131657.log` and `c3_l3a_finalize_s2b_20260924_131953.log`
(the second with `--state`); `--aggregate` pools it (2 runs). The user
pressed BACK on the TV after the debrief; nothing is running now. **The
client posted no decoder session**: the newest in
`logs/games/decoder_sessions/` is `native_decoder_20260924_161558_087.json`
(session 1's second half). Both finalizes report "no candidate (0
rejected); split: 0 session(s) posted after the run's start sum to 0
ssrc_changes, expected 24". Phase B answers defaulted again (all three
`False` / `None`: Enter through the prompts). The user has **not stated**
the title or a picture judgement for this session — record "not stated";
do not infer the title from `/plugins/games/status` (at 13:00 local it
showed Crash Bandicoot active; report that fact as a fact, not as the
user's statement).

Read first: `evidence/C3_L3A_R1_SESSION1_2026-09-24.md`,
`evidence/D_BASE_R4_REPORT_VISIBILITY_2026-09-20.md` (how the client's
end-of-session post works and what its failure looks like),
`docs/KNOWN_ISSUES.md`.

**Scope.** Documentation plus one read of the journal. No probe, companion,
client, profile or route change; nothing in the environment; no session;
companion not restarted. Never modify the state file or any run file.

## Do

1. **Why no report.** `journalctl --user -u privyhub-companion` from 16:55Z
   to 17:25Z (redact with `h2_prep_redact.py`, `--check` 0 residual): find
   the session's `native-stream-start` / `-ready` / `-stop`, the heartbeat
   sequence's last entry, and whether a decoder-session POST arrived,
   failed (HTTP error, malformed body, size) or never came. Also the
   companion's own log for a client report rejected or dropped
   (`companion/diagnostics/retention.py` / the decoder-session writer —
   read the source for what it logs). State one of: **client never
   posted**, **client posted and the companion rejected/dropped it (with
   the line)**, or **cannot tell from the logs**. If the client never
   posted or the companion dropped it, open a `docs/KNOWN_ISSUES.md` item
   ("end-of-session decoder report not received after BACK, 2026-09-24
   session 2") with the facts; a real play session lost its decoder-side
   evidence, which the gate's requirement 4 depends on. Do not fix
   anything here.
2. **Record** `evidence/C3_L3A_R2_SESSION2_2026-09-24.md`: the detection
   table from `c3_l3a_runs/20260924_130016.txt` at all three windows (at
   W 5.0: jump 1/5 marked, 1 mark, 30.8 s; ramp 5/5, 10 marks, 83.0 s;
   decoy jump-matched 2/10, 2, 50.0 s; decoy ramp-matched 4/10, 4,
   165.8 s; 15 marks in no sequence window; chance rate 0.0330/s;
   chance-expected 1.02 / 2.74 / 1.65 / 5.47), the mark-lag table and
   histogram (11 marks 1.6-2.6 s after a fire; from decoys: 0.26 s, 4.68,
   7.35, 9.24 s), decoy placement, settling (10 of 10, 1.0-5.0 s: list),
   lifecycle 0/0/0, controller `lost_packets` **1 → 60** over the run
   (~3.5 / min against session 1's ~225 / min and `S1`'s 213-438 — record
   the contrast as a fact under the `KNOWN_ISSUES.md` controller item; no
   cause), Phase B "defaulted (accidental Enter); user's judgement not
   stated", the **decoder-axis check NOT POSSIBLE** and why (from step 1),
   with the consequence stated: this session's marks cannot be checked
   against `stream_discontinuities` (`C3-L2` requirement 4), so in the
   pooled reading it carries marks-only weight. Pooled so far (from
   `c3_l3a_aggregate.txt`, 2 runs, W 5.0): quote the table as printed.
3. **Reading, pre-registered and unchanged:** session 2 of ≥ 4, no
   verdict. What it shows: every ramp marked (5/5, two rungs each on
   average) at 1.6-2.6 s lags; jumps 1/5 (≈ chance 1.02); decoys at their
   chance expectation; 15 unattributed marks (more than session 1's 8),
   unverifiable here. **`C3.L4` stays BLOCKED.**
4. Evidence under `evidence/c3_l3a_r2_2026-09-24/`: byte copies of the
   state copy, the session log, both finalize logs, the run files, the
   aggregate outputs, the journal extract (redacted), `sha256sum`
   manifest. `investigations/ACTIVE.md` §C3.L3a one paragraph; `CURRENT.md`
   (sessions 3-4 awaiting the user; the lost-report item; `python3
   tools/check_memory_health.py` healthy); `2026-09-24.md`;
   `handoffs/CURRENT_HANDOFF.md` one line. No addresses or device
   identifiers in any file. Nothing committed.
