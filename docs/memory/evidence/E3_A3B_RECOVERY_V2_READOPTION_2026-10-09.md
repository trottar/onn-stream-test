---
memory_schema: 1
as_of: 2026-10-09
baseline_commit: 75b2b6b
---

# E3-A3B — recovery v2, re-adopted under the right bar

**Classification: ADOPTION STANDS.** All four pre-registered clauses
hold in both windows. **Recovery v2 is now the companion's default**:
`PRIVYHUB_RECOVERY_TRIGGER=v2` through `recovery.conf`, which gives the
gap log, the 5-s two-check controller-silence trigger, and the
controller-return exit. The adopted state is **four lines**.

| clause | PS1-STREAM | CONC | holds |
| --- | --- | --- | --- |
| (i) no `gave_up_saved` | 0 | 0 | yes |
| (ii) no controller pause that fails to exit within 10 s | no controller pause | no controller pause | yes |
| (iii) host CPU ± 2 of 11.7 / 22.2; companion ± 2 of 24.3 / 26.5 | 11.1; 23.2 | 21.5; 24.8 | yes |
| (iv) gap log ≤ 0.5 point of a core | 0.0027 | 0.0031 | yes |

**Reported, not banded.** The link was still lossy:

- PS1 lost 381 packets/min at 58.7 fps; CONC lost 1,130/min at 56.8 fps.
- The client's own pauses were 1 and 4. All resumed by the client's
  path, in 0.25-9.1 s.
- Two uplink silences over 1 s (1,299 and 1,167 ms, in CONC) started
  while PLAYING. **The old 1-s rule would have paused on both.** v2
  passed them.

**Why a second verification.** E3-A3 adopted v2 and reverted it by
E3-A2's validity rule. That rule voided all six windows on the client's
own pauses (19), while v2 fired no controller pause and passed 27
silences over 1 s. This task's bar judges the trigger only on its own
trigger's events: client pauses are counted and reported, not voiding.
The task wrote that bar before any data, and the pre-registration
carries it.

**Context:**

- Task: `handoffs/E3-A3B_RECOVERY_V2_READOPTION_TASK.md`. The user's
  authorizations, quoted: "Adopt"; after E3-A3's revert, "Code
  application why not".
- **Baseline commit: `75b2b6b`.** E3-A3's work is in the tree,
  uncommitted.
- Files: `e3_a3b_2026-10-09/`.
- Timeline (UTC, 2026-10-09):

  | time | what |
  | --- | --- |
  | 04:50 | precondition ok (three lines, no `recovery.conf`, no `e3_flag.conf`) |
  | **04:50:43** | **`recovery.conf` written**, `daemon-reload`; E3-A3's state-check diff applied (the same bytes); restart; environ four lines; self-test OK, 33/33, `e3_state.py` ok |
  | **04:51:19** | **pre-registration hashed** (`4f110a62…6fde`) |
  | 04:51-05:40 | PS1-STREAM ×1, CONC ×1; both reached PLAYING; final state four lines |
  | 05:41 | analysis: **ADOPTION STANDS** |

## 1. The adoption (E3-A3 §2, repeated)

**The drop-in.** `recovery.conf` (copy here; byte-identical to
E3-A3's): `[Service]` / `Environment=PRIVYHUB_RECOVERY_TRIGGER=v2`.

- The environ is **exactly four** `PRIVYHUB_*` lines
  (`environ_after.txt`): live, the index, Snes9x, recovery.
- The manager has none.
- Four drop-ins are listed (`unit_cat_files.txt`).

**The state checks.** E3-A3's `e3_a3_state_checks.diff` applied cleanly
(`e3_a3b_state_checks_applied.diff`, the same bytes, `d7790c74…9e`).
It changes:

- `tools/e1_suite.py`: `RECOVERY` in `ADOPTED`, and the preflight checks
  `recovery.conf`;
- `d7_regression.py` and `c3_l4_nft_night.py`: the name in `ADOPTED_E3`;
- `e3_state.py`: its docstring;
- the test: the gap log alone is refused.

Checks: self-test OK; `test_c3_l4_nft_night` 33/33; `e3_state.py` ok on
four lines. The predecessor hashes are in
`state_checks_predecessor_sha256.txt`.

**The code** is E3-R2's, unchanged: `games.py` `d72e5f8e…`,
`native_session_io.py` `b7e99279…`, `link_drop_recovery.py` `822fe173…`.

**The kill switch** is in `TOOLS.md` ("Recovery v2", rewritten for the
adopted state): delete `recovery.conf`, `daemon-reload`, restart, and
`git apply -R` the state-check diff. That gives today's 1-s rule with no
gap log.

## 2. The verification

`e3_a3b_analysis.py` → `validity.json`, `gaps/`, `e3_a3b_table.md/.json`,
`e3_a3b_verdict.json`. `runs/` has `manifest.sha256` and `--check` OK.
Both runs reached PLAYING, so both are valid under this task's rule.

| | PS1-STREAM (v2 adopted) | CONC (v2 adopted) | E2 PS1-STREAM | E3-S6A CONC |
| --- | --- | --- | --- | --- |
| window (UTC) | 04:55:16-05:15:16 | 05:19:35-05:39:35 | — | — |
| host CPU % | 11.1 | 21.5 | 11.7 | 22.2 |
| companion CPU % / PSS MB | 23.2 / 38.6 | 24.8 / 47.9 | 24.3 / 38.1 | 26.5 / 45.8 |
| rendered fps | 58.7 | 56.8 | 59.8 | 57.6 |
| video loss/min | 381 | 1,130 | 32.3 | 1,312 |
| resyncs; underruns | 21; 24 | 58; 67 | 0; 11 | 52; 11 |
| `gave_up_saved` | 0 | 0 | — | — |
| `controller_silence` pauses | **0** | **0** | — | — |
| client pauses (resume s) | 1 (6.5) | 4 (3.7, 5.8, 0.25, 9.1) | — | — |
| gaps > 250 ms; > 1 s; max ms | 48; 0; 984 | 83; 2; 1,299 | — | — |
| > 1-s gaps the old rule would have paused on | 0 | **2** (05:21:16Z 1,299 ms; 05:22:43Z 1,167 ms) | — | — |
| gap log, points of a core | 0.0027 | 0.0031 | — | — |

**Verdict: ADOPTION STANDS.**

**Read beside it:**

- **Across the trigger's whole history** (E3-R2's 4 windows, E3-A3's 6,
  these 2: ~4 h on suite windows, plus the user's nft night), v2 has
  fired one `controller_silence` pause: V2-C8's real 8-s drop. That one
  exited 1.6 s after the clear.
- Over the same windows it passed 30 silences over the old rule's 1-s
  threshold. This task checked its 2 against the pause state; E3-A3's 27
  were not checked.
- **No `gave_up_saved` anywhere.**
- The client's 1-3-s output stalls continue. They are the client's
  detector, they resume by themselves, and they remain open.
  - Last night (E3-A3) was the worst link recorded in E3: PS1 loss up to
    2,938/min at 52.6 fps.
  - Tonight it is still lossy: 381 / 1,130 per min.
  - That is a LINK item (`docs/KNOWN_ISSUES.md`), not this change's.

## 3. State at the end; files

- **Final state** (`runs/final_state.json`, 05:40:03Z; `e3_state.py`
  after):
  - environ exactly four lines (live, index, Snes9x, recovery v2); four
    drop-ins;
  - no `e3_flag.conf`, no other flag; no game, RetroArch or encoder;
  - the PS1 files identical; **APK CONFIRMED**.
- No `nft`, no real `sudo`, the Opal untouched; nothing fetched, nothing
  deleted. No other task's script was run (E3-A3's diff applied; its
  analysis not run).
- Files (`e3_a3b_2026-10-09/`):
  - `precondition.json`;
  - the adoption: `environ_before.txt`, `environ_after.txt`,
    `unit_cat_files.txt`, `recovery.conf`, `adopted_at.txt`;
  - the state checks: `state_checks_predecessor_sha256.txt`,
    `e3_a3b_state_checks_applied.diff`, `state_after_adoption.json`;
  - the pre-registration and its `.sha256`;
  - the runs: `runs/`, `runs_console.log`;
  - the analysis: `e3_a3b_analysis.py`, `analysis_console.txt`,
    `validity.json`, `gaps/`, `e3_a3b_table.*`, `e3_a3b_verdict.json`;
  - `redact_check.txt`.
- Git status: `logs/e3_a3b_git_status.txt`.
