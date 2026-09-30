---
memory_schema: 1
as_of: 2026-09-29
status: TASK HANDOFF — C3-L4-L2B: make the nft night one window and hands-off — the user starts the harness over SSH and types their sudo password once; the harness runs the fault commands itself (sudo -n nft, a fixed allow-list, one table), keeps sudo alive, verifies each step, and always removes the fault on any exit; clean up the aborted first attempt; test with a fake sudo; Code never runs nft; nothing adopted; nothing committed; authorized by the user 2026-09-29 ("The whole point of hands on is because of sudo")
---

# C3-L4-L2B — the `nft` night, one window

**Why.** The user works remotely: Windows PC, PowerShell, SSH into the
host. The only reason the night is hands-on is `sudo`. Copying printed
lines between panes over SSH failed and the user aborted the first
attempt on 2026-09-29. The user's instruction: the hands-on part is the
password, nothing else. So the harness itself runs the fault commands
under the user's sudo session; the user starts it, types the password,
and waits.

Read first: `tools/c3_l4_nft_night.py` as L2 left it, the L2 record's §5
and §7, `c3_l4_l2_2026-09-29/harness_dryrun_console.txt`,
`c3_l4_l2_nft_preregistration.txt`.

## 1. Clean up the aborted attempt (first)

Check and put right: `PRIVYHUB_ADAPTIVE_BITRATE_MODE` in the manager
(unset + unit restart), a game active (`stop` route), stray harness
children (T2 sampler, status poller — kill by PID), a tmux session named
`nft` (kill it), a partial `logs/streaming/c3_l4_nft_night_*` run dir
(move to `logs/streaming/aborted/`, not deleted). Code does not run
`nft`; record whatever `nft list tables` output the user's attempt left
in the run dir.

## 2. The change (harness only)

- **Sudo, once.** At start the harness runs `sudo -v` in the foreground
  so the user types the password in the same window; it refuses to
  continue if that fails. A background keepalive runs `sudo -n -v` every
  4 minutes. If a keepalive or any `sudo -n` call fails, the harness
  pauses, clears the fault (if it can), and asks the user to type the
  password again (`sudo -v`) before continuing.
- **The harness runs the fault commands itself**, as `sudo -n nft …`
  with argument lists (no shell), from a **fixed allow-list** built only
  from the L1 §7 steps: create/delete table `inet privyhub_fault`, its
  output-hook chain, the counter rule, the cap rule (CAP computed as
  before), the 2 % random-loss rule, the 15 s drop of video + audio
  ports, `list table`, `list tables`, `flush chain`. Anything else is
  refused by the builder. Every command, its exit code and output go to
  `<run dir>/nft_commands.jsonl`; each listing to `nft_tables.txt`.
- **Verify each step** from the listing (table present with the expected
  rule, or absent) before moving on; on a mismatch, clear the fault, say
  so on screen, and stop the night cleanly (teardown), recorded.
- **Always clear the fault** — normal end, `Ctrl-C`, SIGHUP (SSH drop
  outside tmux), SIGTERM, any exception: `sudo -n nft delete table inet
  privyhub_fault` in a `finally`/signal path, then `list tables` to
  confirm absent, then the normal teardown. The 15 s drop in F3 is timed
  by the harness and removed by it.
- **On screen**: one line per step (what it applies, EXPECT, DID), the
  30 s status line, and a single standing line: `To stop: press Ctrl-C —
  the fault is removed automatically.` No paste prompts. The only Enter
  the user is asked for is to accept the pre-registration at the start.
- **Unchanged**: the steps, timings, expectations, the pre-registration
  and its hash, the recorders, teardown.

## 3. Tests — Code never runs real `nft` or `sudo`

- `--sudo-cmd <path>` (test-only) points the harness at a **fake sudo**
  shim that logs its argv and returns canned `nft list` output. With it:
  a full `--fast` run (holds shortened to 60 s) on the clean link, and
  forced aborts — `Ctrl-C` during F1's cap, SIGHUP during F2, an
  exception during F3's drop — each must end with the delete-table call
  logged, the `list tables` check, and a clean teardown (flag absent,
  stream 7000, game inactive).
- The allow-list builder: unit tests that every §7 command builds and
  anything else (another table, another port, a non-`nft` binary) is
  refused.
- The real `sudo` path is exercised only by the user on the night; say
  so in the record.

## 4. The user's hand steps (rewrite the L2 record's §7)

For someone at a Windows PC with **one** PowerShell window, SSH'd into
the host the way they always connect:

1. `tmux new -s nft`
2. `cd ~/Projects/onn-stream-test && python3 tools/c3_l4_nft_night.py`
3. Type the sudo password when asked. Press Enter to accept the
   pre-registration. Then wait ~90 minutes; nothing else to type.
4. To stop early: `Ctrl-C` (the fault is removed automatically).
5. If the SSH connection drops: reconnect and `tmux attach -t nft`
   (if the harness asks for the password again, type it).
6. At the end it prints RUN DIRECTORY; tell Claude "nft done".

Placeholders only; no addresses.

## Record and memory

Append "L2B — one window" to `evidence/C3_L4_L2_INCREASE_RULE_2026-09-29.md`
(cleanup findings, the change, the allow-list, the fake-sudo tests and
forced-abort results, the new §7); update the harness copy and hashes in
the L2 evidence dir; patch note with hashes; `PATCH_INDEX.md`;
`TOOLS.md` (the harness runs `sudo -n nft` from an allow-list, only when
the user runs it); `CURRENT.md`; the daily file. No addresses. Nothing
adopted. Nothing committed.
