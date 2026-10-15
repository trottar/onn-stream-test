---
memory_schema: 1
as_of: 2026-10-15
status: TASK HANDOFF — E4-S4D, session A item 2: launch the link watch that E4-S4C specified, as a DETACHED process that does not depend on the Code session staying alive. Code hashes the pre-registration, starts the watch under `systemd-run --user`, confirms the first status line, and EXITS. The watch then probes every 45 min until 2026-10-20T04:00Z (or a stop file), runs the deferral set on the first clean window, and writes a one-line status after every probe. E4-S4C's content stands; only the execution model changes
---

# E4-S4D — the link watch, detached

**Why this shape.** The 10-10 Code session stalled after its first job
and nobody could see it for five days. A multi-day measurement must not
live inside a Code session. It lives in a `systemd --user` transient
unit, and its state is a file anyone can `cat`.

Read first: `handoffs/E4-S4C_LINK_WATCH_AND_DEFERRAL_TASK.md` (**the
spec — every probe field, the ping trace, the clean gate, the deferral
runs and bar, the storage rule, the record**, unchanged except as below),
`e4_s4c_2026-10-10/e4_s4c_watch.py` and its helpers (`o1_*`, `p4_harvest.py`,
`e4_s4c_passrule.py`, `e4_s4c_history.py`), `e4_s4c_preregistration.draft`.

## 1. Changes to E4-S4C (the only ones)

- **Detached:** `systemd-run --user --unit=privyhub-link-watch
  --collect -p WorkingDirectory=<repo> python3 e4_s4d_watch.py …`. Not
  `nohup`, not a Code-session child. The watch's own log goes to the
  journal and to `~/privyhub_link_watch/watch.log`.
- **Status file:** `~/privyhub_link_watch/status.txt`, rewritten after
  every probe and every run: one line — UTC time, probe number, loss/min,
  rendered, resyncs, `clean`/`dirty`, what the watch is doing next and
  when, the deferral set's progress (`control: -`, `conc1: ok`,
  `conc150: link_voided` …), and the cap. A second file
  `history.csv` appends one row per probe (the E4-S4C fields). Both are
  copied into `e4_s4d_2026-10-15/` at the end by the record task.
- **Stop file:** if `~/privyhub_link_watch/STOP` exists, the watch
  finishes the probe or run in flight, tears down, writes a final status
  line, and exits. The user can stop it with one `touch`.
- **Busy skip:** if a game session is active at probe time (the user
  playing), the probe is skipped and logged `busy`; the next is 45 min
  later. The ping trace continues through it.
- **The cap:** `2026-10-20T04:00:00Z`.
- **The adopted state is five lines** (E4-S5D): the precondition and
  every `flags_absent` read-back use it; `PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1`
  is still the only flag the watch ever sets, for the flagged runs only.
- **Self-check:** the watch writes a heartbeat timestamp to the status
  line every 5 min even when idle; a reader can tell "idle" from "dead".

## 2. What Code does (and then stops)

1. Copy `e4_s4c_watch.py` → `e4_s4d_2026-10-15/e4_s4d_watch.py` with the
   changes above (diff kept); a 2-min dry run (`--dry`) that writes a
   status line and exits, no stream.
2. Fill the pre-registration from the draft (`e4_s4d_preregistration.txt`:
   E4-S4C §1 verbatim, the cap and the stop file added), **hash it**,
   `preregistration_hashed_at.txt`.
3. Launch the unit. Wait for the first probe's status line (≤ 10 min).
   Read it back; `systemctl --user status privyhub-link-watch` into the
   record.
4. Write `evidence/E4_S4D_LINK_WATCH_LAUNCH_2026-10-15.md` (the launch,
   the unit, the status file's path, the stop file, how to read it, the
   first probe's line); `logs/e4_s4d_git_status.txt`; the queue's close
   (KNOWN_ISSUES, `CURRENT_HANDOFF.md`, the redactor, `CURRENT.md` last).
   **Exit.** The record of the watch itself is a later one-line task.
