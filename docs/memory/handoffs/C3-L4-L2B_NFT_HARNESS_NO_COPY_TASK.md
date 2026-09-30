---
memory_schema: 1
as_of: 2026-09-29
status: TASK HANDOFF — C3-L4-L2B: make the nft-night harness usable from the user's PC over SSH with no copy-paste — the harness writes each step's nft lines to one fixed script the user runs with a single repeated command in a second SSH window, and verifies it ran; clean up anything the user's aborted first attempt left behind; dry run again; no companion change; nothing adopted; nothing committed; authorized by the user 2026-09-29
---

# C3-L4-L2B — the `nft` harness, no copy-paste

**Why.** The user works remotely: a Windows PC, PowerShell, SSH into
the host. Copying printed lines between tmux panes over SSH did not work
(the paste landed back in the harness pane), and the user aborted the
first attempt on 2026-09-29. The fault commands are always the same
shape, so the user should never have to copy anything: they should type
one command once and then repeat it.

Read first: `tools/c3_l4_nft_night.py` as L2 left it, the L2 record's §5
and §7, `c3_l4_l2_2026-09-29/harness_dryrun_console.txt`.

## 1. Clean up the aborted attempt (first, before any change)

The user's aborted run may have left: `PRIVYHUB_ADAPTIVE_BITRATE_MODE` set
in the manager, a game active, a T2 sampler or status poller still
running, a tmux session named `nft`, a partial run directory under
`logs/streaming/c3_l4_nft_night_*`. Check each and put it right (flag
unset + unit restart, `stop` route, stray harness children killed by
PID, tmux session `nft` killed if it exists). The harness never ran
`nft`; still, record whether the user's `sudo nft list tables` output
exists in the run dir and what it shows — Code cannot run `nft` and does
not. Move the partial run directory to
`logs/streaming/aborted/` (not deleted) and say so.

## 2. The change (harness only)

- **`logs/streaming/nft_step.sh`**: at every step where the harness today
  prints lines to paste (apply, calibrate, list, remove, the final check),
  it instead writes those exact lines, in order, to this one file
  (`#!/bin/bash`, `set -e`, the lines, then the step's
  `nft list … | tee -a <run dir>/nft_tables.txt`), mode 0600, owned by
  the user, overwritten per step with a step id and a comment saying what
  it does. It prints, large and alone on the screen:

  ```
  >>> In your SECOND window: press Up-arrow, then Enter.
      (first time only, type:  sudo bash logs/streaming/nft_step.sh)
      Step: <id> — <one line of what it does>
  >>> Then come back here and press Enter.
  ```

- **Verification**: after Enter, the harness checks that the step ran —
  the `nft_tables.txt` grew and its newest listing shows the expected
  state (table present with the expected rule / table absent). If not,
  it says `That step has not run yet` and shows the same box again. It
  never proceeds on an unverified step.
- **`logs/streaming/nft_clear.sh`**: written once at start, contains only
  `nft delete table inet privyhub_fault 2>/dev/null || true` and a
  `nft list tables | tee -a` line. The abort instruction the harness
  shows at every step becomes: `In your SECOND window type:
  sudo bash logs/streaming/nft_clear.sh — then press Ctrl-C here.`
- **Preflight** also checks the step files are not left over from an
  earlier run (removes them) and that `logs/` is out of git (it is).
- **The CAP** is computed as before and written into the step file.
- **Nothing else changes**: steps, timings, expectations, the
  pre-registration and its hash, teardown.
- `--dry-run` writes the step files too (marked `# DRY RUN — do not run`),
  auto-advances, and skips verification.

## 3. Dry run

Run `--dry-run` once end to end; record the console; confirm each step
file's contents in the console log; confirm teardown clean. Update the
harness copy and hashes in the L2 evidence dir.

## 4. The user's hand steps (rewrite the L2 record's §7)

Written for someone at a **Windows PC** using **two PowerShell windows**,
each SSH'd into the host the way they always do. Window 1: `tmux new -s
nft`, then the harness command. Window 2: `cd ~/Projects/onn-stream-test`
then `sudo -v`, then only ever `sudo bash logs/streaming/nft_step.sh`
(typed once, then Up-arrow + Enter). No panes, no copying, no tmux keys.
If the SSH window for window 1 drops: reconnect and `tmux attach -t nft`.
Abort: window 2 `sudo bash logs/streaming/nft_clear.sh`, window 1
`Ctrl-C`. Placeholders only; no addresses.

## Record and memory

Append a section "L2B — no copy-paste" to
`evidence/C3_L4_L2_INCREASE_RULE_2026-09-29.md` (the cleanup findings,
the change, the dry run, the new §7); patch note with hashes;
`PATCH_INDEX.md`; `TOOLS.md`; `CURRENT.md`; the daily file. No addresses.
Nothing adopted. Nothing committed.
