---
memory_schema: 1
as_of: 2026-09-29
baseline_commit: f01c3b2
durable_memory_updated: true
---

# C3-L4-L2B: the `nft` night in one window — the harness runs `sudo -n nft` from an allow-list

## Purpose

The user works from a Windows PC over one PowerShell SSH session. On
2026-09-29 the first attempt at the L2 night was aborted: copying the
printed `sudo nft …` lines between tmux panes over SSH did not work. The
user's instruction ("The whole point of hands on is because of sudo"):
the only hands-on part is the password. Task:
`handoffs/C3-L4-L2B_NFT_HARNESS_ONE_WINDOW_TASK.md`. It replaces
`C3-L4-L2B_NFT_HARNESS_NO_COPY_TASK.md`, which is withdrawn and was not
run. Record: `evidence/C3_L4_L2_INCREASE_RULE_2026-09-29.md`, "L2B — one
window".

## Change (harness only; no companion or client change)

- `tools/c3_l4_nft_night.py`:
  - **The allow-list** `NFT_ALLOW`, with `nft_argv()` (the builder) and
    `nft_check()` (exact match). It holds the ten L1 §7 commands on table
    `inet privyhub_fault` only. The one variable is `<CAP>`, an integer
    of 200-2000 kbytes/s. Anything else raises `NftRefused` before sudo
    is called.
  - **Sudo**: `sudo -v` in the foreground at the start (preflight
    refuses if it fails); a keepalive `sudo -n -v` every 240 s. If
    `sudo -n` is refused (by the keepalive or by any call), the harness
    pauses, removes the fault if it can, asks for the password
    (`sudo -v`, 3 tries), and puts the fault back from its recipe before
    continuing.
  - **Runs the fault commands itself**: `[sudo, "-n", "nft", …]`,
    argument lists, no shell. Each call goes to `nft_commands.jsonl`
    (argv, exit code, output), and each listing to `nft_tables.txt`.
  - **Verification**:
    - after every apply, `nft list table`: the table present and chain
      `flt` holding exactly the expected rule, matched to nft's printed
      form (counters included);
    - after every remove, `nft list tables`: absent.
    - A mismatch removes the fault and stops the night through the
      normal teardown (`StepMismatch`).
  - **Every exit removes the fault** (`finish()` → `clear_fault_final()`):
    normal end, Ctrl-C, SIGHUP, SIGTERM (handlers raise `Signalled`), a
    stop, or an exception. It deletes the table, confirms absence with
    `list tables`, then tears down. Signals are ignored while this runs.
    If the removal cannot be confirmed, it prints the delete line for
    the user.
  - F3's 15 s drop is applied, timed and removed by the harness; the
    measured on-time is recorded.
  - On screen: each command with its exit code, EXPECT/DID, the 30 s
    status, and `To stop: press Ctrl-C -- the fault is removed
    automatically.` The only prompt is Enter to accept the
    pre-registration. The paste prompts are gone.
  - A leftover `privyhub_fault` table at preflight is removed (was: refuse).
  - A warning is printed when not inside tmux.
  - Every child process except the foreground `sudo -v` gets
    `stdin=DEVNULL`. Found by the first fake-sudo run: `adb shell` had
    read the piped Enter.
  - Test-only: `--fast` (60 s holds, the real command path) and
    `--sudo-cmd` must be given together; hidden `--keepalive-s` and
    `--test-fail-at F1_cap_on|F2_loss_on|F3_drop`.
  - **Unchanged**: steps, timings, expectations, the pre-registration and
    its hash, recorders, teardown, collection.
- **New** `tools/c3_l4_fake_sudo.py` (TEST ONLY): logs its argv and models
  the one table in `$FAKE_SUDO_DIR`. It renders listings in nft's format,
  with the counter growing at the 7000 wire rate. A `deny` file makes it
  refuse `-n`; a `mangle` file makes it list no rule.
- **New** `tools/test_c3_l4_nft_night.py`: unit tests for the allow-list,
  the listing parser and the fake.

## Tests (Code never ran real `nft`; one stray `sudo -n true`, see the record)

- Unit tests 18/18.
- The full `--fast` run PASS: 42 fake-sudo calls, all allow-listed; CAP
  869 from the counter; the drop on 15.02 s; teardown CLEAN; files
  23/23.
- Forced aborts, each ending with the delete, `list tables` absent and
  a CLEAN teardown:
  - A1 Ctrl-C in F1's cap: PASS;
  - A2 SIGHUP in F2: PASS;
  - A3 an exception in F3's drop: PASS;
  - A4 keepalive refused → password → continued: PASS;
  - A5 verify mismatch → clean stop: PASS.
- `--dry-run` smoke (F1, F3; no sudo): PASS.
- Two defects were found and fixed while testing: children reading
  stdin, and SIGINT when started ignored.
- Details are in the record, "L2B — one window".

## Hashes

| File | sha256 |
|---|---|
| `tools/c3_l4_nft_night.py` before (L2; copy `evidence/c3_l4_l2_2026-09-29/l2b/c3_l4_nft_night.L2.py`) | `faac44dd555cd36fb4cde3b075882a1f7946bb0f41cd4509693ee7a7cc7c7a75` |
| `tools/c3_l4_nft_night.py` after (L2B; copy `evidence/c3_l4_l2_2026-09-29/c3_l4_nft_night.py`) | `e2b50198d67c1ac5a2014f52f3eed2c6523f3cf2942b240a60cfbcc8b64f5c6d` |
| `tools/c3_l4_fake_sudo.py` (new) | `78840faea5f17dcbc16474d7be8fd948e0a9f45d736f2feb44b3e5b2925b8caa` |
| `tools/test_c3_l4_nft_night.py` (new) | `ce9bf9998a952d16fbc874ae68733164429122c76c2b9fd0f4e8426c72c294ed` |
| the pre-registration (unchanged) | `fb5ca63fe559e5b2f99eb670d38fb21532f55f2fdd98883ca3f3f0678f57c531` |

All evidence files: `evidence/c3_l4_l2_2026-09-29/sha256_manifest.txt` (regenerated).

## Not done / by the user

- The real `sudo` path runs only when the user runs the night.
- Nothing adopted. Nothing committed.
