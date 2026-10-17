---
memory_schema: 1
as_of: 2026-10-17
status: TASK HANDOFF — G8-S1 final record (session A): the envelope's record over all 22 cells from the driver's files, superseding the PARTIAL record of 2026-10-16; the code-version change from cell 6 on (session B's G5-S3 edits) disclosed and bounded by B's flag-absent proof; the four cap cells that never reached PLAYING read from the suite's and the shim's files. Measurement only; nothing adopted; nothing committed; the driver is not relaunched
---

# G8-S1 — the final record

Read first: `G8_S1_ADVERSE_NETWORK_ENVELOPE_2026-10-16.md` (the PARTIAL record: its tables, field definitions, the resync columns, the `none` vs CL-B3 comparison — keep its form), `G8_S1_RESUME_2026-10-17.md` §5 (the B edits during cell 6: files, times, hashes), `G5_S3_REMOTE_LADDER_2026-10-17.md` (B's flag-absent proof: actuator 200/200, games plugin 3/3, G5-S2's replay identical), `g8_s1_preregistration.txt` (hash `b2e02fa0…dcf73`, unchanged), `cells.jsonl` (22 rows), `g8_s1_state.json` (`closed_by: all 22 cells done`, 04:30:30Z), `runs/<cell>/`, `~/privyhub_g8_s1/` (final `status.txt`, `history.csv`, `driver.log` — copy them in as `final_status_resume.txt`, `history.csv`, `driver.log`, replacing the stop-time copies).

## 1. Precondition

The unit `privyhub-g8-s1` collected (not found); `status.txt` says `EXITED (all 22 cells done)` or the driver's equivalent; `tools/e3_state.py --check` ok on the seven lines, no `e3_flag.conf`, no game, one device paired (adb: reconnect as the resume did if needed). The tree may carry the user's uncommitted B work (G5-S3, G5-S4, G4-P2) — touch nothing; no stash, reset, checkout or clean. Baseline HEAD named.

## 2. The record — `evidence/G8_S1_ADVERSE_NETWORK_ENVELOPE_2026-10-17.md` (supersedes the 10-16 PARTIAL record; say so in both)

**Classification:** MEASURED — n of 22 cells valid; the four cap cells (17–20) `no_play`; the code-version note (§3). All five tables of the PARTIAL record extended to 22 rows (host side with gates; link side with both resync columns; ladder / rules / classifier / shim; recovery events; the shim's cost), from `cells.jsonl` and the run files, by the same `g8_s1_analysis.py` extended — its reading saved beside (`g8_s1_cells_read_final.json`, `g8_s1_table_final.md`, `validity.json` replaced).

**The pre-registered comparisons, now complete:**

- (i) `none` vs CL-B3 as in the PARTIAL record.
- (ii) off vs on per profile, all eleven: what the rules suggested (count by rule id, from `decisions.jsonl` rows with `source: wan_rules`) and what the ladder then did (rung path), and whether rendered / stale / loss moved — stated, not judged. Cells 6 (loss-5 on: 297 suggestions, 7000→5000) and 12 (delay-150 on: 133, →6000) are the two where the rules acted; cell 7 (burst off) is where the plain ladder acted by itself (`capacity_mild`?) — say which trigger from the decisions log.
- (iii) the classifier check for all eleven profiles: class assigned vs the profile's intent, off and on — the pre-registered questions answered from the files: did `cap-4500` read `capacity-limited` (the cells read capacity-limited / starved while not playing — say what the classifier saw: setup traffic only), did `delay-150` read `latency-limited` (rows 11/12 read lossy / path-changed), did `loss-5` read `lossy` (yes), and `jitter-30 on` read `latency-limited`.

**The four cap cells (17–20), read, not explained away:** for each, the suite's launch attempts and their outcomes (the run's `suite.log`: how many launches, what the client reported, whether PLAYING was ever reached and lost or never reached), the shim's counters over the attempt (`impairment_run<n>.jsonl`: `dropped_queue`, `queue_max`, in / out, the cap's token rate as applied), the client's last heartbeat state, the companion's log lines at the attempts, `flags_absent_after`. Then the candidate readings, listed, none chosen: (a) the stream's start exceeds the cap and the bounded queue drops the setup burst (the ladder starts at 7000 > 6000 > 4500); (b) the shim's cap stage stalls or mis-paces at post-FEC; (c) the client's start-up timeout. What each would predict in the files, and what the files show. **G8-P1's in-process cap proof was against a synthetic source at a steady rate — say so.** This is the one finding that needs a follow-up task (listed in §5, not designed here).

**The link's own loss across the night:** the `none` cells and the two 10-17 control-like cells (none ran on 10-17; say so) — the LAN was lossy on 10-16 evening (cells 1–5) and the resumed cells ran 00:21–04:30Z; report cells 9/10 (delay-50) and 15/16 (reorder-5) as the lowest-loss cells of the night, as a bound on the link's own contribution, not as a control.

## 3. The code version, disclosed (the resume record §5)

- Cells 1–5 and cell 6's attempt 1 ran the pre-registered modules (`tools_at_preregistration_sha256.txt`). From cell 6's attempt 2 (00:2x Z) to cell 22, every companion restart loaded session B's edited `companion/wan_adaptation.py` (sha256 now `9a9fe444…`, pre-registered `e28f6b44…`), `companion/adaptive_bitrate_live.py`, `companion/plugins/games.py`, and the new `companion/remote_ladder.py` — B's G5-S3 work, behind `PRIVYHUB_REMOTE_LADDER=1`, which was absent all night.
- **What bounds it:** B's flag-absent proof in `G5_S3_…` — the actuator 200/200 identical, the games plugin's stream start 3/3 identical, and G5-S2's replay of the rules' recorded decisions re-run identical with B's code present and B's flag absent. State that proof's scope exactly (what it compared, on what inputs) and what it does not cover (live behaviour under the shim's profiles was not replayed; the proof is in process). The on-arm cells' `wan_suggestion` rows therefore come from `wan_adaptation.py` as edited, equivalent to G5-S2's by that replay.
- The hashes of the four files at the record's close, beside the pre-registered ones (`tools_at_record_close_sha256.txt`). No claim that the night is unaffected beyond what the proof shows; no re-run proposed by this record (the user's call — listed as an option in §5).
- The Cowork-side lesson, one line: a measurement that enables a flag must not run while that flag's module is being edited.

## 4. State, files

`--check` ok; `manifest.sha256` over the whole directory (the night's `runs/` included), `manifest_check.txt`, `validity.json`, the redactor over the whole directory (the benign rule as before; the `.pyc` files excluded as before), `redact_check.txt` replaced; `logs/g8_s1_final_git_status.txt`.

## 5. The rest

- `docs/ROADMAP.md` §G8: "envelope measured: 18/22 cells valid; the rate-cap profiles did not reach PLAYING (open); see the record".
- `docs/KNOWN_ISSUES.md`: the cap cells; delay-150 not read as latency-limited by the classifier (reported).
- `CURRENT.md`: the state line; Next Action: the user's commit (B's three tasks, the resume, this record); **options for the user, not decided here:** (a) a cap follow-up (G8-S2: the cap cells with a start below the cap, or the shim's cap stage re-proved against a bursty source); (b) a re-run of the on-arm cells on committed code if the user wants the arm on one code version; (c) G5-S3's LAN smoke, then G4-S2 off-site with G5-S3 + G5-S2 + the cap (the user judging 4000's picture).
- Nothing adopted; nothing committed. Exit.
