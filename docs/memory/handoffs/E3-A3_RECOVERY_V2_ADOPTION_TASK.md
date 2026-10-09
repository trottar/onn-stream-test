---
memory_schema: 1
as_of: 2026-10-09
status: TASK HANDOFF — E3-A3 (the user's authorization in chat, 2026-10-09: "Adopt", after the nft check of 2026-10-09 00:11-00:18Z passed): adopt E3-R2's recovery trigger v2 (the gap log, the 5-s two-check controller-silence threshold, the controller-return exit) as the companion's default through its own drop-in; record the nft check from its raw files; extend the state checks; verify on the suite (PS1-STREAM ×1, CONC ×1); CURRENT.md. E3 closes with this. Nothing else adopted; nothing committed
---

# E3-A3 — adopting recovery v2; E3's close

**What is adopted.** `PRIVYHUB_RECOVERY_TRIGGER=v2`
(`evidence/E3_R2_RECOVERY_PAUSE_EXIT_2026-10-08.md`): the controller
receive loop's gap log; the host's `controller_silence` trigger at
5,000 ms confirmed on two checks ≥ 250 ms apart; a `controller_silence`
pause resumes by itself when the packets are back (age < 500 ms on two
checks) and the next heartbeat shows the client's output age ≤ 300 ms.
The client-side trigger, the give-up timer, the restart path and R3c2's
flow are unchanged.

**Why, in the user's words and the evidence.** The user: "Adopt"
(2026-10-09), after the cost-benefit in chat. The evidence: R1 located
the false pause (a 1-s threshold on 1-3 s uplink stalls with no exit;
five suite sessions on four nights); R2's repaired replay reproduced
every recorded event, fired on all eight real drops and on none of the
controller false pauses, and the exit would have resumed each within
~3 s; four suite windows with the flag had no pause of any kind and the
gap log caught a 1,253-ms stall that today's rule would have turned
into a pause-and-save. R2 was REJECTED on two bar clauses the record
reads as defects of the bar (a two-sided fps band against a lossier
night; a write-coincidence rule with no tolerance) — said plainly here.
**The user's nft check (00:11-00:18Z, 2026-10-09, `r3b_run.sh`)**:
V2-N3 and V2-N15 paused on `client_output_silence` at +1.3 s and
resumed as R3b; **V2-C2 (2-s controller drop): no pause** (gap log
2,064 ms); **V2-C8 (8-s drop): `controller_silence` at +5.35 s,
`resumed via controller_return` 1.6 s after the clear, no
`gave_up_saved`** (gap log 8,038 ms).

Read first: the R1 and R2 records and dirs; `d_base_r3b_2026-09-21/V2-*/`
(the user's four runs — **record them**: §1); `E3_A2_…` and `E3_S6A_…`
(the adoption pattern and the state-check patches); `TOOLS.md`.

## 1. The nft check, recorded first

Copy nothing; **cite** `d_base_r3b_2026-09-21/V2-N3`, `V2-N15`, `V2-C2`,
`V2-C8` (their `recovery_lines.jsonl`, `timings.txt`,
`nft_table_active.txt`, `state_during_fault.txt`) and the gap lines in
`logs/games/native_stream_ctrl_gaps.log` for 00:11-00:18Z; add the
four dirs' files to `d_base_r3b_2026-09-21/SHA256SUMS.txt` (append; do
not rewrite the existing lines). Table in the record: per run, the
fault window, every recovery event with its offset from `t_on` /
`t_off`, the gap line. Note V2-C8's unrelated client-side pause at
+8 s into its session (00:16:29Z, resumed in 3 s): the client's
detector, unchanged. **The redactor over every file cited.**

## 2. Precondition and the adoption

- The adopted state (environ exactly live, index, snes9x; three
  drop-ins; no e3 drop-in — the user's paste removed it; if
  `e3_flag.conf` is somehow present, remove it and say so); `e3_state.py`
  ok.
- A separate drop-in `recovery.conf` in
  `~/.config/systemd/user/privyhub-companion.service.d/` with exactly
  `[Service]` and `Environment=PRIVYHUB_RECOVERY_TRIGGER=v2`;
  `daemon-reload`; restart.
- Verify: the environ carries **exactly four** `PRIVYHUB_*` lines (live,
  index, snes core, recovery); the manager none; `systemctl --user cat`
  lists four drop-ins; the gap log file is created on the first session
  (bounded: 512 KB + one rotated copy).
- **State checks**: `ADOPTED` / `ADOPTED_E3` in `tools/e1_suite.py`,
  `e3_state.py`, `d7_regression.py`, `c3_l4_nft_night.py` gain the
  name; the preflight checks the drop-in; `test_c3_l4_nft_night.py`
  still passes. Recorded as a patch.
- **Kill switch** in `TOOLS.md`: delete `recovery.conf`, `daemon-reload`,
  restart — today's 1-s rule, no gap log, byte for byte. The gap log
  alone stays available as `PRIVYHUB_RECOVERY_GAP_LOG=1`.

## 3. Verification on the adopted state (pre-registered, hashed before the runs)

No flag set; the adopted defaults run.

- **Runs**: E1-PS1-STREAM ×1, E1-CONC ×1 (E2's windows and gaps).
- **Bar, the adoption stands if all hold** (else the drop-in is removed,
  the state checks reverted, and the record says ADOPTION REVERTED with
  the clause): no `gave_up_saved` and no unexited `controller_silence`
  pause in either window; each run valid by E3-A2's rule or, if a
  controller pause fires and exits within 10 s, that is reported and
  the run still counts; host CPU within ± 2 of its reference
  (PS1-STREAM 11.7; CONC: E3-R2's 20.9-23.4, same code); the
  companion's stream cost ± 2 points of a core; the gap log ≤ 0.5 point
  of a core. Rendered fps, loss, underruns, resyncs, the gap count and
  max **reported, not banded** (R2's lesson: cross-night fps bands do
  not belong in a trigger's bar).

## 4. The record, and E3's close

`evidence/E3_A3_RECOVERY_V2_ADOPTION_<date>.md` + `e3_a3_<date>/` (the
nft table and citations, the drop-in's text, environ before/after, the
pre-registration + `.sha256`, 2 runs, `manifest.sha256`, `--check`,
`validity.json`, the gap logs, table, verdict, `redact_check.txt`);
`patches/E3-A3_…md` + `PATCH_INDEX.md`; `docs/KNOWN_ISSUES.md` (the
false pause: fixed and adopted; the client-side 1-3 s stalls remain the
client's, open); `TOOLS.md`; `investigations/ACTIVE.md`;
`logs/e3_a3_git_status.txt`.

**Then E3's close** (the user: "So e3 is done then?" — yes, on this
adoption): `docs/ROADMAP.md` E3 **CLOSED** with a table of every E3
item — S1 INCONCLUSIVE, S2 REJECTED, S3 REJECTED, S4 ACCEPTED→ADOPTED,
S5/S5B/S5C and A2's frame_spin REJECTED/REVERTED (not adopted), S6
MEMORY ACCEPTED→ADOPTED / STREAM REJECTED, S7/S7B REJECTED (pacing not
adopted, the user's decision), R1 INCONCLUSIVE→R2→A3 ADOPTED — and the
adopted state's four lines; `CURRENT_HANDOFF.md`; the redactor over
everything written; **`CURRENT.md` last** — Active Objective: **E4**
(the resource envelope on the adopted state); Verified State: the
four-line environ and four drop-ins; Next Action 1: the user's commit;
2: E4-S1 as Cowork hands it (the reference re-measured on the adopted
state, then the floor by constraining the host, no `sudo`: a
`systemd --user` drop-in with `CPUQuota=` / `AllowedCPUs=` /
`MemoryMax=` on the companion's unit — say in the record whether the
user manager delegates the `cpu`, `cpuset` and `memory` controllers
and whether RetroArch and the encoder live in the companion's cgroup,
since that decides whether the method works; measure, do not act).
