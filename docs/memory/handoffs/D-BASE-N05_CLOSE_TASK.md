---
memory_schema: 1
as_of: 2026-09-22
status: TASK HANDOFF — classify the user's N05 hand run (the one R3b run still owed) and close, or not, R3 + R3a for real loss; documentation only, no nft, no code
---

# N05 close — the last owed link-drop run

**Gate.** The user has run `./r3b_run.sh N05 output 48100,48101 0.5 20 25`
by hand with the companion listening. If `evidence/d_base_r3b_2026-09-21/N05/`
is still empty, classify NOT RUN again, say so, and stop.

Read first: `evidence/D_BASE_R3D_HAND_RUNS_2026-09-22.md` (the shape of a
run write-up and the N05 criterion), `evidence/D_BASE_R3B_NFTABLES_LINK_DROP_2026-09-22.md`,
`handoffs/D-BASE-R3B_TASK.md` (criteria table).

**Criterion (N05, 0.5 s).** PASS if **no `desync_pause`** fires (the
recovery log between `session_started` and `session_ended` holds no pause
event), the receiver resyncs on its own, `max_output_gap_ms` < 1,000, and
the report records a sequence resync or loss for the hole. A pause that
fires and clears is a FAIL of the criterion as written — record it with
the DESYNC constant (1 s) beside the measured fault duration and the
`age_ms` that tripped it.

Raw numbers first: measured fault (`t_off - t_on`), every recovery event
with its offset, `max_output_gap_ms`, `lost_packets`, `sequence_resyncs`,
`forward_gap_events`, `fec_recovered_packets`, the discontinuity list, and
the heartbeat's `rx_packets` / `last_output_age_ms` across the hole.

**Classify.** N05 PASS → **`R3` + `R3a` RUNTIME VALIDATED for real loss**
(N05, N3, N15, N15b, N150 all PASS; `END_MS` already validated by `R3d`).
N05 FAIL → name the criterion and the numbers; the pair stays open; state
in one line whether the failure is the constant (DESYNC 1 s against a
0.5 s hole plus restart latency) or the mechanism, from the numbers only.

**Record.** Append an "N05 — result" section to
`evidence/D_BASE_R3D_HAND_RUNS_2026-09-22.md` and update its front-matter
status; regenerate `d_base_r3b_2026-09-21/SHA256SUMS.txt` (`sha256sum -c`
clean); `evidence/RUNTIME_VALIDATION.md` (R3, R3a, R3b lines); `CURRENT.md`
(fixed headings, `python3 tools/check_memory_health.py` healthy — trim);
`MEMORY.md` (one line); `handoffs/CURRENT_HANDOFF.md`; `KNOWN_ISSUES.md`
(close or narrow the "N05 owed" item); `investigations/ACTIVE.md`; the
dated memory file. Teardown per `TOOLS.md`; confirm `sudo -n nft list
tables` shows no `privyhub_fault`. No addresses, endpoints or identifiers.
Nothing committed.
