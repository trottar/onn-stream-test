---
memory_schema: 1
as_of: 2026-10-09
status: TASK HANDOFF — E3-A3B (the user's authorizations in chat, 2026-10-09: "Adopt", then after E3-A3's revert "Code application why not"): re-adopt recovery v2 exactly as E3-A3 did, with a verification bar that judges a trigger change on its own trigger's events only — the client's output-stall pauses are reported, not voiding. PS1-STREAM ×1, CONC ×1. E3's close updated. Nothing else adopted; nothing committed
---

# E3-A3B — recovery v2, re-adopted under the right bar

**Why this task exists.** E3-A3 adopted v2, verified nothing wrong
with it (six windows: 0 `controller_silence` pauses, 0 `gave_up_saved`,
27 uplink silences > 1 s passed that the old rule would have turned
into pause-and-save), and then reverted it because the verification
rule voided every run on the **client's own** `client_output_silence`
pauses (19 of them on the worst link night of E3: loss up to 2,938/min,
rendered 52.6 on plain PS1). That rule was written for performance
bars (E3-A2) and is wrong for a trigger change that does not touch the
client's detector. The user's word stands: "Adopt", and again after
the revert. **This task re-adopts with the bar corrected before any
data.** Nothing else changes.

Read first: `evidence/E3_A3_RECOVERY_V2_ADOPTION_2026-10-09.md` and
`e3_a3_2026-10-09/` (`recovery.conf`, `e3_a3_state_checks.diff`,
`e3_a3_analysis.py`, `e3_a3_preregistration.txt`); the R2 record;
`TOOLS.md`.

## 1. The adoption (E3-A3 §2, repeated)

- Precondition: the three-line adopted state; no `e3_flag.conf`, no
  `recovery.conf`; `e3_state.py` ok.
- `recovery.conf` (`[Service]` / `Environment=PRIVYHUB_RECOVERY_TRIGGER=v2`)
  in the drop-in dir; `daemon-reload`; restart; the environ exactly
  **four** `PRIVYHUB_*` lines; the manager none; four drop-ins listed.
- The state checks: `git apply` E3-A3's `e3_a3_state_checks.diff` (the
  same patch; if it no longer applies cleanly, the same change by hand
  and a new diff); self-test, `test_c3_l4_nft_night` 33/33,
  `e3_state.py` ok on four lines.
- Kill switch in `TOOLS.md` as E3-A3 §5 (already there; confirm).

## 2. Verification (pre-registered, hashed before the runs)

No flag set; the adopted defaults run. E1-PS1-STREAM ×1, E1-CONC ×1
(E2's windows and gaps).

- **Validity for this task, written here:** a run is judged on
  **controller-trigger events only**. A `client_output_silence` pause
  (the client's detector, unchanged by v2) does **not** void the run; it
  is counted and reported with its resume time. A run that never
  reaches PLAYING is still an invalid attempt (replaced at most twice).
- **Bar, the adoption stands if all hold:**
  - (i) no `gave_up_saved` in either window;
  - (ii) no `controller_silence` pause that fails to exit within 10 s
    (one that fires and exits via `controller_return` is reported and
    counts);
  - (iii) host CPU within ± 2 of its reference (PS1-STREAM 11.7; CONC
    22.2) and the companion's CPU within ± 2 points of a core of its
    reference (24.3; 26.5);
  - (iv) the gap log ≤ 0.5 point of a core.
- **Reported, not banded:** rendered fps, loss/min, resyncs, underruns,
  the client pauses and their resume times, the gap count / > 1 s / max,
  and how many of the > 1 s gaps the old rule would have paused on.
- If (i)-(iv) fail, the pre-registered action is the revert, as E3-A3
  did it; the record then says which clause and why.

## 3. The record and the close

`evidence/E3_A3B_RECOVERY_V2_READOPTION_<date>.md` + `e3_a3b_<date>/`
(the pre-registration + `.sha256`, environ before/after, the applied
diff, the runs with `manifest.sha256` and `--check`, `validity.json`,
`gaps/`, table, verdict, `redact_check.txt`); `patches/` +
`PATCH_INDEX.md`; `docs/KNOWN_ISSUES.md` (the false pause: fixed and
adopted; the client's 1-3 s stalls remain the client's, open — and
note last night's link as the worst recorded, a LINK item);
`TOOLS.md`; `docs/ROADMAP.md`'s E3 table: R1→R2→A3→A3B **ADOPTED**,
three adoptions standing (the index, Snes9x, recovery v2);
`CURRENT_HANDOFF.md`; the redactor over everything written;
**`CURRENT.md` last** — Verified State: the four-line environ and four
drop-ins; Active Objective E4; Next Action 1: the user's commit; 2:
E4-S1 as Cowork hands it (CPUQuota/MemoryMax steps on the companion's
unit; cpuset not delegated). `logs/e3_a3b_git_status.txt`. **The final
state is the four-line adopted state**; no other flag; no game; PS1
files identical; APK CONFIRMED. No `nft`, no real `sudo`, the Opal
untouched; nothing fetched; nothing deleted.
