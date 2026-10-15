---
memory_schema: 1
as_of: 2026-10-10
status: TASK HANDOFF — E4-S4B, queue item 3: grab deferral (`PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1`, E4-S4's change, unchanged) re-run on a clean link. E4-S4 was REJECTED only on clauses (a) and (d) — loss and rendered fps — on a night where even the no-flag control lost 148/min; (b), (c), (e) held and CONC at `CPUQuota=150%` ran with 0 s throttled. Same runs, same bar verbatim, plus a clean-link gate on the control that is read before any flagged run and retried over the night. Nothing adopted; nothing committed
---

# E4-S4B — grab deferral, on a clean link

**What E4-S4 established.** With the flag: 0 grabber processes during
every CONC window, the queue grew to 6, drained 6/6 with 0 failures in
~33 s, the guide served, the cap never fired; host CPU 11.7-12.4 % (the
control 11.8 %); at `CPUQuota=150%` 0 s throttled, host CPU 10.8 %. The
change does what it says and makes CONC a plain stream. The bar failed
on loss/min (364-817 vs the control's 148, the cap 100) and rendered fps
(58.1-58.9 vs ≥ 59.5): link metrics on a bad-link night. The bar is not
changed after the data — it is run again under the condition it assumed.

Read first: `evidence/E4_S4_GRAB_DEFERRAL_2026-10-10.md`,
`e4_s4_2026-10-10/e4_s4_preregistration.txt`, `e4_s4_passrule.py`,
`e4_s4_table.md`, `apply_e4_s4.py` (the flag's apply/remove), E3-A3B's
validity reading.

## 1. Pre-registration (hashed before any run)

- **The clean-link gate (new; the only addition):** the control
  (E1-PS1-STREAM, no flag, 20 min) runs first. It is **clean** if its
  video loss/min < 10 (D-BASE's row) **and** rendered ≥ 59.5 **and**
  resyncs ≤ 10. If not clean: idle 30 min, run the control again — up to
  **4 controls over the night** (~3.5 h). The first clean control is
  *the* control; the flagged runs start after it. If none of the four is
  clean: **INCONCLUSIVE (link)**, no flagged run, the four controls'
  figures in the record, and the task ends there.
- **Runs after a clean control**, E2's windows and gaps, exactly E4-S4's:
  E1-CONC ×2 with the flag (unconstrained), E1-CONC ×1 with the flag at
  `CPUQuota=150%` (the drop-in as E4-S2, removed at teardown). Each CONC
  teardown waits for the deferred queue to drain and records it.
- **Comparability (else INCONCLUSIVE):** the control within E1's bands of
  E4-S1's PS1-STREAM (host CPU 10.9 ± 2; rendered 59.53 ± 0.5).
- **Bar = E4-S4's, verbatim** (clauses (a)-(e); ACCEPTED only if all
  hold): (a) each flagged CONC: loss/min ≤ 3 × the control's and ≤ 100,
  rendered ≥ 59.5, resyncs ≤ 10, host CPU within ± 2 of the control; (b)
  0 grabber processes in the window, the queue grew, drained with failed
  0, within 2 × the cycle's normal time; (c) the guide serves after the
  drain (6 channels; programmes ± 5 % of the pre-run read); (d) CONC at
  150 % passes E4-S2's pass rule, throttled time reported; (e) the
  companion's stream cost within ± 2 points of a core of the control's.
- **Reported:** the cap, drain times, the client's pauses, the gap log,
  and — if a flagged run's link goes bad mid-night (loss > 3 × the clean
  control's) — that it did, with the host-side clauses stated on their
  own so the record says which clause the link took.

## 2. The record

`evidence/E4_S4B_GRAB_DEFERRAL_CLEAN_LINK_<date>.md` + `e4_s4b_<date>/`
(the pre-registration + `.sha256`, every control attempt, the 3 flagged
runs, `manifest.sha256`, `--check`, `validity.json`, table, verdict,
`redact_check.txt`); **what the alpha spec becomes if adopted** (E4-S2
§5's table with the deferral line: the stack's CPU-time floor 150 %, 4
cores); the one-line adoption (a drop-in `epg-defer.conf`,
`Environment=PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1`) and its revert,
written, not applied; `logs/e4_s4b_git_status.txt`. Flag absent; no
`e4_constraint.conf`; the adopted state restored; then the queue's close
(ROADMAP, `CURRENT_HANDOFF.md`, the redactor, `CURRENT.md` last).
