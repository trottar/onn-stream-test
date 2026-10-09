---
memory_schema: 1
as_of: 2026-10-09
baseline_commit: 75b2b6b
---

# E3-A3 — adopting recovery v2; E3's close

**Classification: ADOPTION REVERTED by the pre-registered verification
bar, clause (ii): "broke the row".** Neither row had a valid run after
two replacements. Every one of the six 20-min windows was invalidated
by the **client's own** `client_output_silence` pauses (19 in all) on a
poor link (loss 201-2,938 per min).

**What v2 itself did** in those six windows (~2 h of streaming):

- **zero `controller_silence` pauses and zero `gave_up_saved`**, so clause
  (i) held;
- the gap log recorded **27 client→host silences over 1 s** (max
  2,208 ms). Under the old 1-s rule each would have been a pause with
  no exit (R1: pause, 120 s, save), and v2 passed all 27;
- host and companion CPU were inside the (iii)/(iv) bands in all six
  windows, and the gap log cost ~0.003 points of a core (reported; with
  no valid run these clauses were not judged).

**The user's nft check passed (§1).** The real-drop path is unchanged.
A 2-s controller drop no longer pauses. An 8-s one pauses at +5.35 s and
resumes itself 1.62 s after the clear.

**What failed is the validity rule, not the trigger.** E3-A2's rule
voids a run on any recovery pause. With the client's detector firing on
a bad link, no run could be valid tonight. The bar is not changed after
data.

- **State now:** the adopted state is back to three lines (live, the
  index, Snes9x). `recovery.conf` was removed at 03:02:24Z, the state
  checks were reversed (byte-identical to their predecessors), and the
  v2 code stays in the tree, dormant (as committed at `75b2b6b`).
- **Re-adopting is one line** (§5) and is the user's decision, as is
  whether to re-verify on a cleaner night or with a validity rule that
  separates the client's pauses.
- **E3 closes here as the task directs** (§6), with recovery v2 recorded
  as verified on the air but not adopted.

**Context:**

- Task: `handoffs/E3-A3_RECOVERY_V2_ADOPTION_TASK.md`. The user's
  authorization, quoted: "Adopt" (2026-10-09), after the nft check
  passed.
- **Baseline commit: `75b2b6b`**, the user's E3-R2/S7B commit.
- Files: `e3_a3_2026-10-09/`.
- Timeline (UTC, 2026-10-09):

  | time | what |
  | --- | --- |
  | 00:32 | the nft check recorded (§1); `SHA256SUMS.txt` appended |
  | 00:33:20 | precondition ok (three lines, no `e3_flag.conf`); **`recovery.conf` written**, `daemon-reload`, restart; environ four lines |
  | 00:33-00:34 | state checks extended; self-test OK, 33/33, `e3_state.py` ok |
  | **00:34:14** | **pre-registration hashed** (`333d5c6e…a454`) |
  | 00:34-01:22 | PS1-STREAM, CONC: both invalid (client pauses) |
  | 01:23-02:12 | first replacements: both invalid |
  | 02:13-03:01 | second replacements: both invalid → (ii) broke the row |
  | **03:02:24** | **ADOPTION REVERTED**: `recovery.conf` removed, `daemon-reload`, state checks reversed, restart; three lines, `e3_state.py` ok |

## 1. The user's nft check (2026-10-09 00:11-00:18Z), recorded

The runs are cited in place, not copied: `d_base_r3b_2026-09-21/V2-N3`,
`V2-N15`, `V2-C2`, `V2-C8` (each with `recovery_lines.jsonl`,
`timings.txt`, `nft_table_active.txt`, `state_during_fault.txt`, plus
the heartbeat lines, the decoder report and the status).

- `SHA256SUMS.txt` there gained 36 lines for those files. The 59
  existing lines are untouched, and all 36 new lines verify. Seven old
  `N05/` lines already fail to verify; that is pre-existing.
- The 15 gap lines for 00:11-00:18Z are excerpted in
  `nft_gap_lines.jsonl`.
- `e3_a3_nft_table.py` → `nft_table.md/.json`.

| run | fault | window (UTC; s) | recovery events (offset from t_on / t_off) | gap > 1 s (start from t_on; ms; burst) |
| --- | --- | --- | --- | --- |
| V2-N3 | host→client 48100,48101 | 00:12:00.248 → 00:12:03.317; 3.07 | `desync_pause client_output_silence` (+1.34 / −1.73); `resumed` (+5.40 / +2.33) | none |
| V2-N15 | host→client 48100,48101 | 00:13:27.868 → 00:13:42.933; 15.07 | `desync_pause client_output_silence` (+1.36 / −13.71); `encoder_restart` (+5.54); `resumed` (+18.78 / +3.71) | none |
| **V2-C2** | client→host 48102 | 00:15:20.487 → 00:15:22.569; 2.08 | **none** | −0.03 s; **2,064.3**; 227 |
| **V2-C8** | client→host 48102 | 00:16:46.914 → 00:16:54.973; 8.06 | `desync_pause controller_silence` (**+5.35** / −2.71); **`resumed` via `controller_return`** (+9.68 / **+1.62**); no `gave_up_saved` | −0.00 s; **8,038.1**; 227 |

- V2-C8 also had an unrelated client-side pause at 00:16:29Z, 8 s into
  its session (17.5 s before the fault). It resumed in 3 s. That is the
  client's detector, unchanged.
- **Redactor** over the four dirs (`redact_check_nft.txt`): the hits are
  the encoder's loopback RTP target and RetroArch's Beetle PSX HW version
  string. No private address. It is the same pattern as R3b's original
  `N3/status_end.json`.

## 2. The adoption (then reverted)

- **Precondition** (`precondition.json`): environ exactly live, index,
  snes9x; three drop-ins; `e3_flag.conf` absent (the user's paste had
  removed it); `e3_state.py` ok.
- **`recovery.conf`** (copy here): `[Service]` /
  `Environment=PRIVYHUB_RECOVERY_TRIGGER=v2`. Written 00:33:20Z, then
  `daemon-reload` and restart.
  - The environ was **exactly four** `PRIVYHUB_*` lines
    (`environ_after.txt`); the manager had none.
  - `systemctl --user cat` listed four drop-ins (`unit_cat_files.txt`).
  - The gap log wrote on the first session (bounded: 512 KB + one
    rotated copy).
- **State checks** (`e3_a3_state_checks.diff`; patch
  `patches/E3-A3_RECOVERY_V2_ADOPTION.md`):
  - `tools/e1_suite.py`: `RECOVERY` in `ADOPTED`, and the preflight
    checks the drop-in;
  - `d7_regression.py` and `c3_l4_nft_night.py`: the name in
    `ADOPTED_E3`;
  - `e3_state.py`: its docstring;
  - the test refuses the gap log alone.
  - Results: self-test OK, `test_c3_l4_nft_night` 33/33, `e3_state.py`
    ok on four lines.
- **Revert** (03:02:24Z, the pre-registered action):
  - `recovery.conf` removed, `daemon-reload`, the diff reversed
    (`git apply -R`), restart;
  - environ three lines (`environ_after_revert.txt`), three drop-ins;
  - the five tools byte-identical to their predecessors
    (`state_checks_predecessor_sha256.txt`, `sha256sum -c` OK);
  - self-test OK, 33/33, `e3_state.py` ok (`state_after_revert.json`).

## 3. The verification and its bar

From `e3_a3_preregistration.txt` (hashed 00:34:14Z, before any run):

- No flag set; E1-PS1-STREAM ×1 and E1-CONC ×1 with E2's windows and
  gaps.
- E3-A2's validity rule, except that a `controller_silence` pause that
  resumed via `controller_return` within 10 s still counts.
- An invalid run is replaced at most twice.

The analysis is `e3_a3_analysis.py` (adapted from E3-R2's, copied here),
writing `validity.json`, `e3_a3_verdict.json` and `gaps/`. The table
over all six windows is `e3_a3_table_all_windows.md`, made by
`tools/e3_table.py`. `--check` is OK for `runs/`, `runs_retry1/` and
`runs_retry2/`.

| window | valid | client pauses | controller pauses | gave_up | host CPU % | companion CPU % | rendered fps | loss/min | resyncs; underruns | gaps > 250 ms; > 1 s (max ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PS1 run1 | no | 6 | **0** | **0** | 11.4 | 23.6 | 52.6 | 2,938 | 189; 123 | 121; 6 (1,420) |
| PS1 retry1 | no | 3 | **0** | **0** | 11.8 | 25.5 | 58.5 | 530 | 28; 39 | 47; 3 (1,210) |
| PS1 retry2 | no | 1 | **0** | **0** | 10.9 | 25.6 | 59.4 | 201 | 4; 16 | 16; 2 (1,285) |
| CONC run1 | no | 4 | **0** | **0** | 21.7 | 26.6 | 56.9 | 1,436 | 80; 89 | 79; 8 (2,000) |
| CONC retry1 | no | 3 | **0** | **0** | 21.7 | 25.8 | 56.1 | 1,952 | 122; 98 | 69; 3 (1,365) |
| CONC retry2 | no | 2 | **0** | **0** | 20.6 | 24.8 | 57.8 | 932 | 67; 60 | 32; 5 (2,209) |
| *E3-R2 PS1 r1 / CONC r2 (same code, 10-08)* | yes | 0 | 0 | 0 | 11.1 / 23.4 | 25.0 / 27.1 | 59.8 / 59.4 | 58.6 / 284 | 0; 13 / 9; 5 | 7; 1 / 1; 0 |

- Each client pause resumed by the client's own path; several first had
  encoder restarts, meaning the output really stalled.
- The PS1 row's last replacement had a single client pause (02:20:47Z,
  resumed in 3.6 s). That one pause decided the row.

| clause | needed | got | holds |
| --- | --- | --- | --- |
| (i) no `gave_up_saved`; no unexited controller pause | none | none in six windows | **yes** |
| (ii) a valid run per row (≤ 2 replacements) | 1 + 1 | **0 + 0** (client pauses) | **no — broke the row** |
| (iii) host CPU in band (PS1 9.69-13.69; CONC 18.9-25.4) | | not judged; every window inside | not evaluable |
| (iv) companion CPU in band (PS1 23.0-27.2; CONC 24.0-29.1) | | not judged; every window inside | not evaluable |
| (v) gap log ≤ 0.5 point | | not judged; 0.0028-0.0030 in every window | not evaluable |

**Verdict: ADOPTION REVERTED (ii).**

`e3_a3_verdict_before_replacements.json` is the analysis's first output,
written before the replacements ran. It marked (iii)-(v) as failed
instead of "not evaluable"; the final verdict corrects that label. It is
kept as written.

## 4. Read beside the bar

- **The fix did its work again**, on the worst link of E3. 27 silences
  over 1 s, up to 2.2 s, all passed. R1 counted five false pauses on
  four nights under the old rule; tonight alone would have produced
  several, most ending in pause-and-save.
- **The rule that broke the row voids a run on any recovery event.** It
  was written (E3-A2) to keep false pauses out of performance numbers.
  Here it applied to the trigger whose change removes those pauses. The
  client-side stalls are real output stalls (encoder restarts follow
  some), and v2 does not touch them.
- **For the user:**
  - re-adopt anyway: one line, §5. The nft check and ~3 h of v2 on
    suite windows (R2's four, tonight's six) show no controller pause and
    no save;
  - re-verify on a cleaner night;
  - or re-verify with a validity rule that judges a trigger change only
    on its own trigger's events. That is a bar change for a new
    pre-registration.

## 5. The kill switch / the one-line re-adoption (`TOOLS.md`)

```bash
printf '[Service]\nEnvironment=PRIVYHUB_RECOVERY_TRIGGER=v2\n' > ~/.config/systemd/user/privyhub-companion.service.d/recovery.conf && systemctl --user daemon-reload && systemctl --user restart privyhub-companion   # adopt v2
rm ~/.config/systemd/user/privyhub-companion.service.d/recovery.conf && systemctl --user daemon-reload && systemctl --user restart privyhub-companion       # back to today's 1-s rule, no gap log
```

A re-adoption also needs the state checks: `git apply
docs/memory/evidence/e3_a3_2026-10-09/e3_a3_state_checks.diff`. The gap
log alone stays available as `PRIVYHUB_RECOVERY_GAP_LOG=1` (a probe hook).

## 6. E3's close, and what E4's method can use (measured, not acted on)

**E3 is CLOSED** (`docs/ROADMAP.md`, the table of every item). Two
adoptions stand: the guide index and Snes9x. Recovery v2 was verified on
the air and reverted by its verification bar; re-adopting it is the
user's call.

**cgroups** (`cgroup_delegation.txt`, `cgroup_membership.txt`; read-only):

- The user manager (`user@1000.service`) has `Delegate=yes`,
  `DelegateControllers=cpu memory pids`.
  - **cpu: yes. memory: yes. cpuset: NO.** The root has cpuset, but it is
    not delegated.
- The companion's cgroup currently has `memory pids` enabled. `app.slice`
  enables `cpu` only when a unit asks for it (the controller is
  delegated down to the user manager).
- **RetroArch (and its AppRun wrapper) and the encoder (ffmpeg) live in
  the companion's cgroup**, `app.slice/privyhub-companion.service`: one
  cgroup, 7 processes, measured during a PS1 session.
- **So for E4:**
  - `CPUQuota=` and `MemoryMax=` in a `systemd --user` drop-in on the
    companion's unit can constrain the whole stack (companion + core +
    encoder) without sudo;
  - `AllowedCPUs=` cannot, because cpuset is not delegated. Pinning would
    need root, or another method such as `taskset` on the processes.
- A cgroup-v1 `net_cls` hierarchy from a VPN package is also mounted.
  It does not affect the controllers above.

## 7. State at the end; files

- **Final state** (`state_after_revert.json`, 03:02Z; the last suite's
  `final_state` 03:01:43Z):
  - the three-line environ, three drop-ins;
  - no `e3_flag.conf`, no `recovery.conf`;
  - no game; the PS1 files identical; **APK CONFIRMED**.
- No `nft`, no real `sudo`, the Opal untouched; nothing fetched.
- Nothing deleted except `recovery.conf`, the pre-registered revert; a
  copy is kept here.
- No other task's script was run in its directory: R3b's runs and R2's
  analysis were read or copied.
- Files (`e3_a3_2026-10-09/`):
  - `precondition*.json`;
  - the nft record: `e3_a3_nft_table.py`, `nft_table.*`,
    `nft_gap_lines.jsonl`, `redact_check_nft.txt`;
  - the adoption: `recovery.conf`, `environ_*.txt`, `unit_cat_files.txt`,
    `adopted_at.txt`, `reverted_at.txt`;
  - the state checks: `e3_a3_state_checks.diff`,
    `state_checks_predecessor_sha256.txt`, `state_after_*.json`;
  - the pre-registration and its `.sha256`;
  - the runs: `runs/`, `runs_retry1/`, `runs_retry2/` (each with
    `manifest.sha256` and `check.txt`) and their consoles;
  - the analysis: `e3_a3_analysis.py`, `validity.json`, `gaps/`,
    `e3_a3_table*.md/.json`, `e3_a3_verdict*.json`;
  - `cgroup_delegation.txt`, `cgroup_membership.txt`;
  - `redact_check.txt`.
- Git status: `logs/e3_a3_git_status.txt`.
