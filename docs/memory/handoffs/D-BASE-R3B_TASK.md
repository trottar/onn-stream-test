---
memory_schema: 1
as_of: 2026-09-20
status: TASK HANDOFF — D-BASE-R3b, the owed nftables fault-injection runs for link-drop self-recovery plus the two unexercised paths; runs only once passwordless `sudo nft` exists; superseded once its evidence record exists
---

# D-BASE-R3b task handoff

Validation only — **no production code changes in this task.** Run the link-drop recovery against real on-the-wire packet loss in /home/privyhub/Projects/onn-stream-test. Read first: docs/memory/CURRENT.md, docs/memory/investigations/LINK_DROP_RECOVERY_DESIGN.md (the validation plan and expected column), docs/memory/evidence/D_BASE_R3_LINK_DROP_RECOVERY_2026-09-20.md and D_BASE_R3A_RESTART_FALLBACK_2026-09-20.md (what the substitute fault could and could not show), docs/memory/TOOLS.md, companion/games/link_drop_recovery.py.

**Permission note (2026-09-21, second attempt).** The first attempt found the sudoers rule in place but every `nft` write refused by this session's own tool-permission classifier ("Security Weaken"). The user has authorized these writes explicitly: they create and delete one nftables table named `privyhub_fault` on this host, for fault injection, and nothing else. `.claude/settings.local.json` in the repo now allows `sudo -n /usr/sbin/nft` commands. Put all `nft` calls in one harness script under evidence/d_base_r3b_<date>/ (the draft from the first attempt was described in docs/memory/2026-09-21.md; rewrite it) so that any remaining prompt is one per run, and if a write is still refused, stop after the first refusal, record INDETERMINATE with the exact command in the dated memory file, and do not look for a way around it.

**Gate.** First command: `sudo -n /usr/sbin/nft list tables`. If it prints anything but a table listing (a password prompt, "a password is required", permission denied), stop immediately, write nothing but a one-paragraph INDETERMINATE note in the dated memory file, and report that the sudoers rule is not in place. Never enter or ask for a password.

**Fault injection**, exactly as the design note gives it, host-side, output hook, so ADB to the onn stays up:

```
sudo -n nft add table inet privyhub_fault
sudo -n nft add chain inet privyhub_fault out '{ type filter hook output priority 0; }'
sudo -n nft add rule inet privyhub_fault out udp dport {48100,48101} drop
sleep <N>
sudo -n nft delete table inet privyhub_fault
```

Always delete the table before any teardown and on every failure path; the last step of the whole task is `sudo -n nft list tables` showing no `privyhub_fault`. Each run from a fresh attract-mode session of the PS1 reference title, 25 s settled, zero input, opened through RESUME PLAYING per TOOLS.md, ended with BACK with the client seeing the game end before the companion stops.

| run | fault | pass criterion |
| --- | --- | --- |
| N05 | out drop 48100+48101, 0.5 s | no pause; receiver resyncs alone; `max_output_gap_ms` < 1,000; a sequence resync or loss recorded in the report |
| N3 | same, 3 s | pause within 1.8 s; `restarts` 0; resume within 3.5 s of the rule being deleted |
| N15 | same, 15 s | pause; if a restart fires, it is `method: restart` and **succeeds while the fault is active** (encoder alive but unheard — the case no substitute run could reach); resume through the gate within 5 s of the rule being deleted |
| N15b | same, 15 s | repeat of N15 |
| N150 | same, 150 s | pause; give-up at 120 s ± 1 s; `PAUSED_SAVED`; recovery file present; after deleting the rule, the launcher prompt appears, Resume from recovery save then RESUME PLAYING restores play |
| H5 | **input** hook, `udp dport 48102 drop`, 5 s — the client keeps receiving video but the host hears no controller packets | `desync_pause` with `trigger` = the controller-silence trigger (not `client_output_silence`) within 1.5 s; then **observe** what happens after the rule is deleted: whether the session returns to `PLAYING`, by what path, and how long it takes. If it does not resume within 30 s, that is a design gap (the client never saw a desync, so it never re-runs the gate and never posts `native-stream-ready`); record it as a defect with the log lines, end the session cleanly, **do not fix it in this task** |
| E30 | same as N150, then leave the rule in place | after give-up, wait; `ENDED` fires at `END_MS` = 30 min after entering `PAUSED_SAVED` (± 5 s); the session ends gracefully with no stranded process; delete the rule; launching the same game from the launcher shows the recovery prompt before the launch proceeds |

For H5 the chain is `hook input`, rule `udp dport 48102 drop`, in the same table; delete the table afterwards as for the others.

**C5a counters.** The installed build carries `idr_aus_rejected_waiting_for_idr`, `non_idr_aus_dropped_waiting_for_idr` and the per-discontinuity `rejected_idr_aus` / `dropped_non_idr_aus` (evidence/C5A_IDR_REJECTION_COUNT_2026-09-21.md). Every sequence resync these runs produce is the first chance to test the C5 hypothesis under loss that is still in progress: for each discontinuity in every run, report `type`, `jump_packets`, `resync_to_idr_ms`, `rejected_idr_aus`, `dropped_non_idr_aus`, `au_complete`, and apply C5a's pre-registered rule (confirmed if every resync > 250 ms carries ≥ 1 rejected IDR and those ≤ 250 ms carry 0; falsified if resyncs > 250 ms show 0; INDETERMINATE below six discontinuities or with none > 250 ms). Record that verdict in a C5 section of this run's evidence record and update the C5a record's status line.

Per run keep: the recovery log lines, heartbeat lines through the fault, the decoder session report (with its `terminal_slow_event`, top-gap and loss/resync fields from `D-BASE-R4` and `D-BASE-R1`), and for N150 and E30 a filtered uiautomator dump of the prompt. Report per run: time to pause, time to resume after the rule was deleted, restarts and their methods, `lost_packets`, `lost_packets_in_resyncs`, resync count, `max_output_gap_ms`. This is the first time loss, sequence jumps and FEC behaviour during a real outage are measured on this build — put those numbers first.

Classify per run against its criterion. `D-BASE-R3` + `D-BASE-R3a` together become RUNTIME VALIDATED only if N05, N3, N15, N15b and N150 all pass; H5 and E30 are reported on their own. Never retry a failing action more than twice; INDETERMINATE with the exact command otherwise. Teardown per TOOLS.md: no nft table left, no stopped process, no listener on 8765 / 48100-48102 / 48110, no banner on the onn, recovery save discarded.

Record raw numbers first in docs/memory/evidence/D_BASE_R3B_NFTABLES_LINK_DROP_<date>.md with artifacts and SHA-256s under evidence/d_base_r3b_<date>/; update CURRENT.md (fixed headings, `python3 tools/check_memory_health.py` healthy), MEMORY.md, handoffs/CURRENT_HANDOFF.md, investigations/ACTIVE.md, the dated memory file, KNOWN_ISSUES.md (link-drop block; any H5 defect gets its own entry), the design note's status line, and evidence/RUNTIME_VALIDATION.md. No IP addresses, ADB endpoints or device identifiers in any memory or evidence file.
