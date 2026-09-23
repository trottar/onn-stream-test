---
memory_schema: 1
as_of: 2026-09-22
status: TASK HANDOFF — D-BASE-R3d, classify the user-run N05, N15b and E30 fault-injection runs from their artifacts and close (or not) R3+R3a and END_MS; documentation only, no nft, no code
---

# D-BASE-R3d — close R3+R3a and END_MS from the hand runs

**Gate.** The user has run, by hand with
`evidence/d_base_r3b_2026-09-21/r3b_run.sh`, the three runs `R3b` left
owed, and says so. Artifacts land beside the earlier ones in
`evidence/d_base_r3b_2026-09-21/<LABEL>/`. If any of `N05/`, `N15b/`,
`E30/` is missing, classify that run NOT RUN and go on with the rest.

Read first: `evidence/D_BASE_R3B_NFTABLES_LINK_DROP_2026-09-22.md`
(criteria, the N3/N15/N150 readings and the restart-hides-loss caveat),
`handoffs/D-BASE-R3B_TASK.md` (the per-run criteria table),
`investigations/LINK_DROP_RECOVERY_DESIGN.md` (`END_MS`, the constants),
`evidence/D_BASE_R3C_RECOVERY_SEMANTICS_<date>.md` (the launcher semantics
now in force: prompt only when no live session and a recovery file exists),
`evidence/d_base_r3b_2026-09-21/r3b_run.sh`, `TOOLS.md`.

**Nothing on the host changes.** No `nft`, no code, no reboot. If a
`privyhub_fault` table is still present (`sudo -n nft list tables`), record
it and tell the user to delete it — do not delete it yourself.

## Per run, raw numbers first

For each of N05, N15b, E30, from `<LABEL>/timings.txt`,
`state_during_fault.txt`, `state_after_clear.txt`, `recovery_lines.jsonl`,
`heartbeat_lines.jsonl`, `status_end.json` and the copied decoder report:

- measured fault duration (`t_off - t_on`; for E30 `t_off` is empty —
  say so and take the rule's removal time from the user's word or the
  script's exit);
- every recovery-log event with its offset from `t_on` / `t_off`;
- `max_output_gap_ms`, `lost_packets`, `lost_packets_in_resyncs`,
  `sequence_resyncs`, `ssrc_changes`, `restarts`, the discontinuity list;
- the heartbeat's `rx_packets` and `last_output_age_ms` across the fault.

**N05 (0.5 s)** — PASS if no `desync_pause` fires, the receiver resyncs on
its own, `max_output_gap_ms` < 1,000, and the report records a sequence
resync or loss for the hole. A pause that fires and clears is a FAIL of
the criterion as written; report it with the DESYNC constant beside it.

**N15b (15 s repeat)** — PASS on the N15 criterion: pause; any restart is
`method: restart` and **succeeds while the fault is active**; resume
within 5 s of the rule being deleted. Put the N15 and N15b numbers side by
side.

**E30 (150 s fault, rule kept for the whole post-wait)** — the run is
`./r3b_run.sh E30 output 48100,48101 150 1900 25 1`: `KEEP_RULE=1` keeps
the table until the script's exit trap, so the 1,900 s post-wait is what
carries the fault across `END_MS`; the script deletes the table itself at
exit. An earlier attempt on 2026-09-22 at 23:38 UTC was aborted (it
overlapped `P8`'s first arm B; its two files were moved aside as
`E30_aborted_2338Z/`) and is not evidence. PASS if, after `gave_up_saved`,
`ENDED` fires **30 min ± 5 s after entering `PAUSED_SAVED`** (from the
recovery log timestamps, not the poll), the session ends gracefully
(RetroArch exit in the game log with `SAVE_FILES OK` and returncode 0, no
orphan pid, no listener on 48100-48102/48110), the recovery file is
present and its SHA-256 recorded, and — after the script exited and the
user launched the same title from the launcher — **the recovery prompt
appeared before the launch** (the companion access log showing the prompt's
request before any `launch`, or the uiautomator dump the user saved).
**The user chooses Discard at that prompt** (`R3c` showed a mid-FMV
recovery save loops when loaded through today's path, so "resume from
recovery" is not exercised here); record that the file and its `.png` are
gone from the states directory afterwards and the game launched plain.

Read the loss column with the `R3b` caveat: a restart makes an outage
invisible to `lost_packets`; `max_output_gap_ms` is the honest column.

**One incident to explain, from logs only.** Between the end of N05 and
the first N15b attempt the companion was **not listening on 8765** (the
first N15b attempt failed to open the stream; `logs/n15b_fail_probe.txt`
holds the status curl — empty — the top activity `MainActivity`, and a
uiautomator dump showing "Companion unreachable"). The user restarted it
by hand (`DISPLAY=:0 nohup … > logs/companion_manual_2026-09-22.log`) and
the second N15b attempt is the one that counts. Find out why it died:
the newest companion stdout/stderr log before the restart (the P8 harness
last restarted it — see `evidence/d_base_p8_2026-09-22/p8_all.sh` for
where its output went), the companion's own log files under `logs/`, the
N05 report POST (the 414 / `send_error` `AttributeError` path `P8`
recorded is a candidate — say whether a traceback is there), and whether
the process that P8 started was a child of the Claude Code session that
ended at 01:58 UTC. Record the cause or "not determined" with what was
looked at; one line in `KNOWN_ISSUES.md` either way. Do not change code.

## Classify

- N05, N15b both PASS (with N3, N15, N150 already PASS) → **`R3` + `R3a`
  RUNTIME VALIDATED** — say so in one line, with the five runs listed.
- E30 PASS → **`END_MS` RUNTIME VALIDATED** (its own line).
- Any FAIL → name the run and the criterion it missed, with the numbers;
  classification stays as it was for the pair.
- Any NOT RUN → say which and why the pair stays open.

## Record and memory

`evidence/D_BASE_R3D_HAND_RUNS_<date>.md` (raw numbers first, one section
per run, then the classification). Regenerate the SHA-256 manifest in
`evidence/d_base_r3b_2026-09-21/` to cover the new run directories;
`sha256sum -c` clean. `evidence/RUNTIME_VALIDATION.md` (the R3, R3a and
END_MS lines). `CURRENT.md` (fixed headings, `python3
tools/check_memory_health.py` healthy — trim; Next Action becomes
companion autostart `H3`, then thermal thresholds, then whatever `P8`
left open). `MEMORY.md` (the closure, one line each). `handoffs/
CURRENT_HANDOFF.md`, `investigations/ACTIVE.md`, `KNOWN_ISSUES.md` (close
the R3b owed-runs item), the dated memory file. Teardown per `TOOLS.md`.
Never retry a failing action more than twice. No addresses, ADB
endpoints, serials or device identifiers in any memory or evidence file.
Nothing committed to git.
