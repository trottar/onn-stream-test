---
memory_schema: 1
as_of: 2026-09-29
baseline_commit: f01c3b2
status: C3-L4-L2 DONE — the live increase rule replaced by the user's blend (clean = fps >= 57, queue <= 1, gap <= 150; one rung when >= 85 of the last 90 reports since the last SSRC change are clean); per-report sample rows in live; 54/54 live + 21/21 shadow tests; parity 0 actions; replays with increases never rate-limited; Session B2 PARTIAL (W4) — the climb 5000 -> 5500 -> 6000 -> 7000 WIRED (windows 90/85, 90/85, 90/86; 7000 held 14 min; 0 packets lost at the 4 transitions) but the pre-registered close-out loss row missed (14.60/min, two bursts at 7000 away from the transitions; 5.0/min without them); tools/c3_l4_nft_night.py built, never runs nft, dry run PASS; the night's pre-registration written; flags unset and absent; nothing adopted, nothing committed. L2B (appended): the nft night is one window — the harness runs sudo -n nft from a fixed allow-list, sudo -v once + 240 s keepalive, verifies each step, removes the fault on every exit; fake-sudo tests PASS (unit 18/18, full --fast run, forced aborts A1-A5); the real sudo path runs only on the user's night; §7 superseded by L2B.4
---

# C3-L4-L2 — the increase rule, sample logging, and the `nft` harness

Task: `handoffs/C3-L4-L2_INCREASE_RULE_AND_NFT_HARNESS_TASK.md` (queue
`QUEUE_2026-09-29.md` item 1; Code stopped after it).

**Documents.**

- Patch: `patches/C3-L4-L2_INCREASE_RULE_AND_SAMPLES.md`.
- The decision is appended to
  `decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`.
- Evidence: `c3_l4_l2_2026-09-29/`.

**Classifications.**

- **Rule and samples: BUILT.**
- **Offline gates: PASS.**
- **Session B2: PARTIAL (W4).** The climb is WIRED. The close-out loss
  row was missed away from the transitions.
- **Harness dry run: PASS.**

## 1. The user's decision

The user's words, 2026-09-28 (`QUEUE_2026-09-29.md`): **"Your blend,
and yes fold in the low-rung screening."**

**The blend**, as the task defines it, is the L1 record's option (a)
definition of "clean" with option (b)'s count:

- **clean** = fps ≥ 57, queue ≤ 1 and gap ≤ 150: no ROUTINE-level sample;
- **step** one rung up when **≥ 85 of the last 90** reports are clean.

It replaces L1's 90 *consecutive* reports at fps ≥ 59, queue 0 and gap ≤
150, which never fired on a clean link (L1 §5). **It is the user's
decision on the data**, not a loosening by Code. The shadow keeps its own
rule.

## 2. The rule as built (`companion/adaptive_bitrate_live.py`)

- **`increase_clean(report)`**: fps ≥ 57, queue ≤ 1 and gap ≤ 150.
- **The window** (`inc_window`, at most 90) holds the evaluated reports
  since the last SSRC change and its 3-report blackout.
  - It is emptied by `_window_restart()`: on the controller's own
    transition (at the decision, and again when the actuator returns), on
    recovery's restart or full start (`note_ssrc_change`), on a session
    start or reset, and on the oscillation hold.
  - Stale and non-distinct reports return before the window, so they do
    not advance it.
  - A resync report (`waiting_for_idr`) enters the window as not clean.
- **INCREASE** is decided when the level is below 7000, the window is
  full (90) and ≥ 85 of the 90 are clean. It then goes through the
  unchanged gates: hold-down, guards, rate limit, oscillation.
  - One rung per event. The window empties after the resulting change,
    so increases are ≥ 3 + 90 = 93 reports apart.
- **Everything else is unchanged from L1**: decreases, hold-downs,
  blackout, rate limit, guards, the disable route.
- **Status** carries `policy.increase_window` {reports, clean, needed,
  rule}. A transition row carries `window_reports` and `clean_reports`.
  The diff is in `module_patch.diff`.

**Per-report samples.** The wrapper writes one `sample` row per client
report:

- time, session elapsed, fps, queue, gap, fresh, `waiting_for_idr`, lost
  delta;
- `clean`, and the **disposition** (`evaluated`, `blackout`, `resync`,
  `stale`, `non_distinct`, `oscillation_hold`, `actuator_failed`,
  `dropped_actuating`);
- `window_reports` and `window_clean`;
- state, reason, level, stream kbps, the blackout remaining, the
  hold-downs, the effective mode.

**Measured: 527 B a row, about 0.95 MB an hour.** The existing rotation
(4 MiB, three archives kept) holds about 16 hours. L1's chatty state-change rows are left
as they were (noted, not changed).

## 3. Offline

**Tests** (`unit_tests.txt`).

- **Live: 54 / 54.** L1's two consecutive-rule tests are replaced
  (`a few unclean reports do not restart the count`, and the constants
  test), and 11 are new:
  - the clean boundary (57.0 / 1 / 150 clean; 56.99, 2, 151 or no fps
    not clean);
  - the window fires at exactly 85/90;
  - 84/90 does not fire until the oldest unclean report rolls out;
  - the wander L1 rejected (fps 57.5, queue 1) is accepted;
  - a stale report is skipped;
  - the window empties after a recovery restart and after the
    increase's own change;
  - a hold-down in force blocks a full window;
  - resync reports count as not clean;
  - one rung per event, ≥ 93 reports apart;
  - a clean or wandering stream at 7000 never acts;
  - one sample row per report, with its fields.
- The rest of L1's suite is unchanged and passes, including the
  oscillation guard (the third direction change becomes `HOLD`).
- **Shadow: 21 / 21, unchanged** (`d66211b3…` / `62e1a011…`).

**Parity** (`c3_l4_l2_replays.txt` §1). The shadow night rebuilt through
live: 3,594 reports, control MATCH, **0 actions**. An increase needs a
prior decrease.

**Recorded loss under the blend** (§2).

- **Sessions.** 83 sessions and 43,855 reports. L1 had 88: the
  companion's own heartbeat logs have rotated since, and the tool cuts
  them at `C4-D1`'s analysis time.
- **Proxy: 13 transitions, bound: 21.**
  - The list now includes **increases**: ROUTINE 7000 → 6000, then
    INCREASE 6000 → 7000 186-1,064 s later, on the pre-adoption
    2026-09-21 sessions.
  - The three FALLBACKs are the link drops recovery would own.
- **At most 2 (proxy) / 3 (bound) transitions in any 10 minutes;
  RATE_LIMITED 0; no oscillation hold.**
- **What the bound variant shows.** On the long `d_base_s2` L1 night,
  ROUTINE and INCREASE alternate at intervals of 20-80 min. Each pair is
  a reversal outside the 10-minute oscillation window, so it is allowed.
  That is the blend's cost on a stream that sits near the ROUTINE line.
  It is noted for the `nft` night, not ruled on (those nights predate the
  adopted profile).

**Flag-off smoke** after the restart (`smoke_flag_off.txt`): `mode off`,
disable 200, inject 403.

## 4. Session B2 — the climb: **PARTIAL (W4)**

**Setup.**

- Pre-registration: `c3_l4_l2_b2_preregistration.txt`, written before B2.
- Live + `INJECT=1`. PLAYING at 03:29:21Z, `any_override` **false**,
  profile adopted, 7000.
- Injections came at +120 s and +150 s. The hold ran to 25 min after the
  first, then BACK at 03:56:23Z (27.2 min).

**The events** (`c3_l4_l2_analysis.txt`; `runs/decision_log_B2.jsonl`,
which holds 812 sample rows):

| UTC | event | window | reports since the previous change | gap in [ssrc, +1 s] |
| --- | --- | --- | --- | --- |
| 03:31:21.9 | injected FALLBACK 7000 → 5000 (actuation 1,376 ms) | — | — | **175 ms** (−11.5 vs 186.5) |
| 03:31:51 | injection 2 **refused `hold_down`** (15 reports left) | — | — | no change |
| 03:35:15.4 | **INCREASE 5000 → 5500** (1,223 ms) | **90 / 85** | 117 | 221 ms |
| 03:39:16.4 | **INCREASE 5500 → 6000** (1,373 ms) | **90 / 85** | 120 | 178 ms |
| 03:42:23.3 | **INCREASE 6000 → 7000** (1,274 ms) | **90 / 86** | 93 | 211 ms |
| 03:42 → 03:56 | at 7000, **no transition for 14.0 min** (window 90/86 at the end) | | | |
| 03:56:26.6 | BACK → `session_ended_reset` (7000, transitions 4 → 0) | | | |

**The per-report samples.**

- 800 were evaluated and 12 were in a blackout (3 per change).
- Clean share by rung: 5000 **91.2 %**, 5500 94.0 %, 6000 95.6 %, 7000
  95.0 %.
- Of 45 unclean reports, 44 were fps < 57 (the client's 2 s
  `recent_fps` reading 51.8-56 now and then, then 61-66 on the next
  report) and 1 was queue > 1.
- The 5000 and 5500 steps took 117 and 120 reports rather than 93. The
  window rolled until the early unclean reports left it.

**The rows:**

| row | result |
| --- | --- |
| W1: one `ssrc_change` to 5000; gap vs 186.5; blackout 3; injection 2 refused `hold_down` | **MET** (1; 175 ms; blackout 12 for 4 changes; refused) |
| W2: 5000 → 5500 → 6000 → 7000, one rung per event, each ≥ 93 reports after the previous change | **MET** (117 / 120 / 93) |
| W3: at 7000, no further transition for the rest of the hold | **MET** (14.0 min, 0) |
| W4: `ssrc_changes` = 4; report stored; lifecycle clean; the close-out rows met | **NOT MET**, on one row: post-FEC video loss **14.60 /min** (< 10). The rest held: 4 SSRC changes, report stored, `session_started`/`session_ended` only |

**The close-out rows**: spikes 24.67, fps 59.90, stale 0.55, **loss 14.60
(FAIL)**, underruns 0.37, max gap **385 ms**.

**Where the loss was** (`b2_loss_location.txt`):

- **0 packets were lost within [−2 s, +6 s] of the four controller
  changes.**
- 160 were lost in one `sequence_resync` at 14.6 min, 88 s after the
  last transition, at 7000. That is also the 385 ms gap.
- 94 were lost in one 2 s interval at 26.5 min, at 7000.
- Without those two intervals the rate is **5.0 /min**.

This is the residual burst loss already on file (`CTRL-L1`: 14-24/min on
some holds; the `T3` warm-state finding). It is not the transitions. The
row stays missed as pre-registered.

→ **PARTIAL (W4).** The controller's own rows (W1-W3) all held: it goes
down in one event and comes back one rung per event under the blend, then
stays put.

## 5. The `nft` harness — `tools/c3_l4_nft_night.py` (the user runs it)

It implements L1 §7 steps 1-13, with the blend's expectations.

- **It never runs `nft` or `sudo`.** It prints each line to paste into the
  second tmux pane and waits for Enter, recording the time.
- **It reads `nft` output through files.** Every `nft list` line it
  prints ends in `| tee -a <run dir>/nft_tables.txt`. It reads the
  calibration counters and the table state from that file.
- **Preflight refuses** on any failure, with the reason:
  - the unit's MainPID does not serve 8765;
  - a game is active;
  - any `PRIVYHUB_*` is set;
  - the stream is not on the adopted profile at 7000 with no override;
  - `adaptive_bitrate` is not off;
  - the onn is not in adb;
  - the APK is not `f31b1c18…8ae7`;
  - a `privyhub_fault` table exists, or nothing was listed;
  - the pre-registration is missing. It is printed and its sha256 is
    copied into the run dir.
- **Setup**: `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live` through the user
  manager (never `INJECT`), then a unit restart. It confirms `live`, 7000
  and only that flag. It starts the `T2` sampler (10 s) and a 5 s status
  poller.
- **Sessions**, each launched the way L1 did (adb, attract mode, PLAYING,
  `any_override` recorded), each ended with BACK, the report copied and
  the game stopped:
  - **F1 (~23 min)**:
    - calibration: a counter rule on 48100, two readings 60 s apart;
      `CAP = 0.822 ×` the 7000 wire rate, in kbytes/s (1024);
    - the cap on (`limit rate over CAP kbytes/second burst 64 kbytes
      counter drop`) for 12 min, then removed for 5 min.
  - **F2 (~19 min)**: 2 % random loss (`numgen random mod 1000 < 20`), 10
    min on and 5 min off.
  - **F3 (~10 min)**: the cap until the level reads 5000 (≤ 4 min), then
    a flush and `udp dport { 48100, 48101 } drop` for a counted 15 s, then
    deleted, then 3 min of observation.
  - **K (~8 min)**: the cap. The harness calls `.../disable` twice itself.
    2 min disabled, then removed, then BACK; it checks the next status
    reads `live`.
- **EXPECT and DID lines.** Before each fault it prints one EXPECT line.
  After each, it prints a DID line from the decision log and the status
  series: the transitions, a HOLD, refusals, `rate_limited` ever, level,
  state, mode, recovery.
- **The delete line comes first at every step**:
  `sudo nft delete table inet privyhub_fault`.
  - On Ctrl-C, an error or a stop, it prints the line again and asks for
    it before tearing down.
  - At the end it asks for `sudo nft list tables | tee -a …` and records
    whether `privyhub_fault` is absent.
- **Teardown**: the flag unset, the unit restarted, the flag confirmed
  absent in the manager and the environ, `mode off`, 7000, no game, the
  banner checked, the recorders stopped.
- **Collected**: the decision log with its sample rows, heartbeats,
  frames and the recovery log for the night's window; a redacted journal;
  `summary.json` with a file-completeness check. All of it goes to
  `logs/streaming/c3_l4_nft_night_<stamp>/`, and the directory is printed.

**Dry run: PASS** (03:58-04:13Z, `harness_dryrun/` and
`harness_dryrun_console.txt`).

- Preflight passed.
- The flag was set (only `MODE=live`) and live came up at 7000.
- All four sessions reached PLAYING with `any_override` false and stored
  their reports. The controller was back at 7000 / live after each BACK.
- Every fault was replaced by a 30 s wait, with its lines printed as "do
  NOT paste". Holds were 60 s and prompts auto-advanced.
- The CAP fell back to the estimate, 869 kbytes/s, because a dry run has
  no counters.
- **The kill switch**: #1 `already_disabled false`, #2 `true`; status
  `mode shadow, configured live, acts false`; `live` again after BACK.
- **Teardown CLEAN**: `PRIVYHUB_*` 0 in the manager and the environ,
  `mode off`, 7000, no game, 0 banners.
- **Recorders**: files **23/23**; 169 status rows, 86 `T2` rows, 339
  heartbeats, 339 sample rows, 8 recovery rows (4 × started/ended).
- On a clean link there was no transition anywhere, as expected.

**The night's pre-registration** is `c3_l4_l2_nft_preregistration.txt`.
The harness prints it and hashes it. The user may amend it before
starting. It is L1's "WORKS UNDER LOSS" with the blend's F1:

- **F1**: one decrease per event, then the climb to 5500, the climb to
  6000 over the cap, the fall back, then `HOLD` (oscillation);
  `rate_limited` never true; no ramp. If the calibrated cap lets 6000
  through clean, the HOLD row is not applicable.
- **F2**: at most one decrease.
- **F3**: no controller action while recovery is not PLAYING, and
  recovery restarts at 5000.
- **K**: as the dry run showed.

## 6. Teardown

The B2 night script and then the dry run's own teardown:

- flags unset, and **absent** from the manager and the MainPID's environ;
- the companion under systemd, the MainPID serving 8765;
- `adaptive_bitrate` off, inject 403;
- profile adopted, stream 7000, `any_override` false;
- no game, **0 banners**, samplers stopped;
- the installed APK's hash confirmed as **`f31b1c18…8ae7`** (04:13Z).

No `nft` was run by Code at any point.

## 7. The user's hand steps for the `nft` night

> **SUPERSEDED 2026-09-29 by L2B.4 below (one window, no pasting).** Kept
> for the record; do not follow it.

Run this when no Code queue is running. Allow **~75-90 minutes**, most of
it waiting. Nothing is needed on the TV; the game plays itself.

1. **SSH to the host and open a two-pane tmux window**: `tmux new -s nft`,
   then `Ctrl-b %`. The **left** pane is for the harness, the **right**
   pane for `sudo`. In the right pane, run `sudo -v` once so the password
   is cached.
2. *(Optional)* **Amend the pre-registration** before starting:
   `docs/memory/evidence/c3_l4_l2_2026-09-29/c3_l4_l2_nft_preregistration.txt`.
3. **Start the harness** in the left pane:
   `cd ~/Projects/onn-stream-test && python3 tools/c3_l4_nft_night.py`
4. **Preflight (~1 min).** The harness prints the pre-registration, then
   a `sudo nft list tables | tee -a …` line.
   - Paste it in the right pane and press Enter in the left.
   - Press Enter again to accept the pre-registration.
   - If it says **REFUSED**, fix the reason and start again. Nothing has
     been changed.
5. **Setup (~30 s).** The harness turns live mode on and starts its
   recorders. The TV opens the stream by itself at each session.
6. **F1, calibration (~2 min).**
   - Paste the three lines it prints (table, chain, counter) and press
     Enter.
   - Paste the `list table … | tee` line and press Enter.
   - The harness waits 60 s. Paste the same line again and press Enter.
   - It prints the **CAP**. A number far from ~870-900 means the listing
     was not read; the harness says so and uses the estimate.
7. **F1, the cap (~17 min).**
   - Paste the flush, the cap rule and the list line, then press Enter.
   - Watch the EXPECT and DID lines, and the 30 s status line (level,
     window, recovery). 12 minutes pass.
   - Then paste the delete and `list tables` lines and press Enter. 5
     more minutes pass. BACK is automatic.
8. **F2, random loss (~19 min).** Paste the table, chain, loss rule and
   list line; press Enter. After 10 minutes, paste the delete and list
   lines; press Enter. 5 minutes, then BACK.
9. **F3, the link drop (~10 min).**
   - Paste the table, chain, cap and list lines; press Enter. Wait until
     the harness says `at 5000` (≤ 4 min).
   - Then paste the flush and the **drop** line, and press Enter
     **at once**.
   - After the 15 s countdown, paste the delete and list lines and press
     Enter.
   - The stream freezes briefly and recovers. 3 minutes of observation
     follow.
10. **K, the kill switch (~8 min).** Paste the table, chain, cap and list
    lines; press Enter. The harness calls the disable route itself. After
    2 minutes, paste the delete and list lines; press Enter.
11. **The end (~2 min).**
    - Paste the final `sudo nft list tables | tee -a …` line and press
      Enter. The harness checks that no `privyhub_fault` table remains.
    - It then tears down (flag off, companion restarted, game ended) and
      prints **RUN DIRECTORY: …**.
    - Note that directory for Code's scoring prompt.
12. **Abort at any point.**
    - Paste `sudo nft delete table inet privyhub_fault` in the right pane
      (the harness prints this line first at every step), then press
      Ctrl-C in the left pane.
    - The harness asks for the delete line once more; press Enter. It
      then tears down.
    - If the harness itself is gone:
      - paste the delete line;
      - then `systemctl --user unset-environment PRIVYHUB_ADAPTIVE_BITRATE_MODE && systemctl --user restart privyhub-companion`;
      - then `curl -X POST localhost:8765/plugins/games/stop`.
13. **Afterwards.** `sudo nft list tables` shows no `privyhub_fault`.
    Nothing else is needed. The next prompt to Code scores the night from
    the run directory, then runs `C5-M2` / `C5-M3`.

## Files (`c3_l4_l2_2026-09-29/`)

- **Rules**: `c3_l4_l2_b2_preregistration.txt`,
  `c3_l4_l2_nft_preregistration.txt`.
- **Code**:
  - `module_patch.diff` (the live module against L1);
  - `pre_patch_sha256.txt`, `post_patch_sha256.txt`;
  - copies of `adaptive_bitrate_live.py`, `test_adaptive_bitrate_live.py`
    and `c3_l4_nft_night.py`.
- **Offline**: `unit_tests.txt`, `c3_l4_l2_replays.txt`,
  `smoke_flag_off.txt`.
- **Session B2**:
  - the harness: `c3_l4_l2_night.sh` (its log `c3_l4_l2_night.log`) and
    `c3_l4_l2_run.sh`;
  - the sampler: `t2_sample.py`, `t2_samples.jsonl`, `t2_sampler.log`;
  - scoring: `c3_l4_l2_analyze.py`, `c3_l4_l2_analysis.txt`,
    `c3_l4_l2_summary.json`, `b2_loss_location.txt`;
  - `runs/`: `decision_log_B2.jsonl` with the sample rows,
    `abr_series_B2.jsonl`, `report_B2.json`, `heartbeat_B2.jsonl`,
    `frames_B2.jsonl`, `armcheck_B2`, `status_end_B2`, `status_B2`,
    `inject{1,2}_B2.json`, the redacted journal `companion_B2.log`,
    `alpha_B2.log`, `encoder_cmd_B2.txt`, `adb_during_hold_B2.txt`,
    `recovery_log.jsonl`, `index.txt`.
- **Harness dry run**: `harness_dryrun/` (the whole run directory) and
  `harness_dryrun_console.txt`.
- `sha256_manifest.txt`.

**Privacy.** `h2_prep_redact.py --check` passes on every Markdown and text
record written. The code, JSON status files and journals match its IPv4
pattern only for the loopback and bind-all addresses, the RetroArch core
version string, and an RFC 5737 documentation address in two route
tests. No device address, MAC, SSID, ADB endpoint or credential appears
anywhere.

---

# L2B — one window (2026-09-29)

Task: `handoffs/C3-L4-L2B_NFT_HARNESS_ONE_WINDOW_TASK.md`, authorized by
the user 2026-09-29 ("The whole point of hands on is because of sudo").
It replaces `C3-L4-L2B_NFT_HARNESS_NO_COPY_TASK.md`, which is withdrawn
and was not run. Patch: `patches/C3-L4-L2B_NFT_HARNESS_ONE_WINDOW.md`.
Evidence: `c3_l4_l2_2026-09-29/l2b/`.

**Classifications.**

- **Cleanup: DONE.** The aborted attempt changed nothing.
- **Harness: BUILT.** It runs `sudo -n nft` from a fixed allow-list,
  verifies each step, and removes the fault on every exit.
- **Fake-sudo tests: PASS**, with two harness defects found and fixed on
  the way:
  - unit tests 18/18;
  - the full `--fast` run;
  - forced aborts A1 (Ctrl-C in F1's cap), A2 (SIGHUP in F2), A3 (an
    exception in F3's drop);
  - extras A4 (keepalive refused → password again) and A5 (verify
    mismatch → clean stop).
- **The real `sudo` path is not exercised.** It runs only when the user
  runs the night.

## L2B.1 Cleanup of the aborted first attempt

Checked at 14:14Z:

| Item | Found | Action |
|---|---|---|
| `PRIVYHUB_ADAPTIVE_BITRATE_MODE` in the manager / MainPID environ | absent / absent | none |
| game active | no (`recovery ENDED`); stream 7000, `adaptive_bitrate` off, adopted profile, `any_override` false; MainPID serves 8765 | none |
| stray harness children (T2 sampler, status poller) | none | none |
| tmux session `nft` | none (only `s1`, an idle shell from the 2026-09-24 C3.L3a night, not touched) | none |
| partial run dirs | three: `c3_l4_nft_night_20260929_140802Z`, `…_140824Z`, `…_140904Z` | moved to `logs/streaming/aborted/` (not deleted) |

- The first two runs were **REFUSED at preflight**: "nothing was written
  to nft_tables.txt". The printed `sudo nft list tables | tee -a …` line
  never reached the right pane.
- The third was **aborted at preflight** (Ctrl-C at the same prompt).
- In all three, the flag was never set, and no game, recorder or fault
  was started.
- **No `nft_tables.txt` exists in any of them.** The user's `nft list
  tables` output never reached a run dir, so there is nothing of it to
  record. The companion journal for 14:07-14:15Z shows only the
  harness's two status GETs per attempt.
- Code did not run `nft`.
- **One slip.** Checking the environment, Code ran `sudo -n true` once
  (≈14:16Z). It was refused ("a password is required") and did nothing.
  It is recorded here because the task says Code does not run sudo. No
  other sudo call was made by Code; every later sudo call in this task
  went to the fake.

## L2B.2 The change — `tools/c3_l4_nft_night.py`

- **Sudo, once.**
  - `sudo -v` runs in the foreground at the start, and the password is
    typed in the same window. Preflight refuses if it fails, with
    nothing changed.
  - A daemon keepalive runs `sudo -n -v` every 240 s.
  - On a refused keepalive, or any `sudo -n` call refused ("a password
    is required"), `reauth()`:
    - pauses, and removes the fault if sudo still lets it;
    - asks for `sudo -v` (3 tries; otherwise the night stops);
    - then rebuilds the table from its recipe if it was removed, and
      verifies it before continuing.
- **The allow-list** (`NFT_ALLOW`, the builder `nft_argv()`, the exact
  matcher `nft_check()`). The argv is passed to
  `sudo -n` as a list, with no shell:

| name | argv |
|---|---|
| `add_table` | `nft add table inet privyhub_fault` |
| `add_chain` | `nft add chain inet privyhub_fault flt` `{ type filter hook output priority 0; }` |
| `counter_rule` | `nft add rule inet privyhub_fault flt udp dport 48100 counter` |
| `cap_rule` | `… udp dport 48100 limit rate over <CAP> kbytes/second burst 64 kbytes counter drop` (`<CAP>` integer 200-2000) |
| `loss_rule` | `… udp dport 48100 numgen random mod 1000 < 20 counter drop` |
| `drop_rule` | `… udp dport` `{ 48100, 48101 }` `counter drop` |
| `list_table` / `list_tables` | `nft list table inet privyhub_fault` / `nft list tables` |
| `flush_chain` | `nft flush chain inet privyhub_fault flt` |
| `delete_table` | `nft delete table inet privyhub_fault` |

  Anything else raises `NftRefused` before sudo is called.

- **Logged.** Every sudo call (validate, keepalive, nft) goes to
  `<run dir>/nft_commands.jsonl` with argv, exit code and output. Every
  listing goes to `nft_tables.txt`.
- **Verify each step.**
  - After an apply: `nft list table`. The table must be present and
    chain `flt` must hold exactly the expected rule, matched against
    nft's printed form (counters included; `1 mbytes/second` is
    accepted when CAP is 1024).
  - After a remove: `nft list tables` shows it absent. One retry, then
    a mismatch.
  - A mismatch prints `!! MISMATCH`, raises `StepMismatch`, and the
    night stops through the normal exit path, which removes the fault.
- **Always clear the fault.** `finish()` runs on every exit once sudo
  was validated: normal end, Ctrl-C (`KeyboardInterrupt`; an explicit
  SIGINT handler), SIGHUP and SIGTERM (handlers raise `Signalled`), a
  stop, or any exception.
  - It ignores further signals.
  - It runs `delete table`, then `list tables`, and records
    `no_fault_table_at_end`.
  - Then it runs the unchanged teardown and collection.
  - If absence cannot be confirmed, it prints the delete line for the
    user.
- **F3's drop** is applied, timed (15 s from the verified apply) and
  removed by the harness. The measured on-time is in
  `summary.sessions.F3.drop_s_measured`.
- **On screen.**
  - Each command, with its exit code.
  - VERIFY lines, EXPECT/DID lines, and the 30 s status line.
  - `To stop: press Ctrl-C -- the fault is removed automatically.` in
    every banner and before the one prompt.
  - The one prompt: Enter to accept the pre-registration. There are no
    paste prompts.
- **Small additions.**
  - A leftover `privyhub_fault` table at preflight is removed and
    verified (L2 refused).
  - A warning is printed when `$TMUX` is unset.
  - `stdin=DEVNULL` for every child except the foreground `sudo -v`
    (found in testing, below).
  - `--dry-run` runs no sudo and prints the commands it would run.
- **Test-only flags.** `--fast` (60 s holds, the real command path) and
  `--sudo-cmd` must be given together. Hidden: `--keepalive-s` and
  `--test-fail-at F1_cap_on|F2_loss_on|F3_drop`.
- **Unchanged**: the steps, timings (`REAL`), expectations, the
  pre-registration (`fb5ca63f…`) and its hashing, recorders, teardown,
  collection.
- **New test files.**
  - `tools/c3_l4_fake_sudo.py` (TEST ONLY): logs its argv and models the
    one table, printing listings in nft's format. The counter grows at
    1,083 kB/s. A `deny` file makes `-n` refuse; a `mangle` file makes
    the listing show no rule.
  - `tools/test_c3_l4_nft_night.py`.

**Known limit (real sudo, not testable with the fake).** Debian's
default `timestamp_type=tty` keys sudo's cached credential to the
terminal. If the SSH connection drops **outside tmux**, the harness
still catches SIGHUP and tries the delete. But sudo may then refuse
`-n`, because the terminal is gone. The harness then logs `COULD NOT
CONFIRM THE FAULT IS GONE` with the delete line. Inside tmux the
terminal survives the drop, so the removal works. This is why step 1
below is `tmux new -s nft`.

## L2B.3 Tests — fake sudo only; Code never ran real `nft` or `sudo`

**Unit tests** (`python3 -m unittest tools/test_c3_l4_nft_night.py -v`): **18/18 OK**.

- Every §7 command builds, and passes the exact check.
- Refused:
  - unknown names;
  - another table (`filter`; `ip` family);
  - another port (22, 48102, `{ 48100, 22 }`);
  - another binary (`iptables`, `/usr/sbin/nft`, `bash`, `sh`, `tc`,
    `nft;`);
  - other verbs and shapes (`flush ruleset`, `list ruleset`, `-f`,
    extra args, `; rm -rf ~`, `insert`, a drop with no counter, a
    `< 200` loss rule, an input hook);
  - the literal `<CAP>`;
  - CAP tokens `8690`, `199`, `2001`, `869.5`, `-869`, full-width
    digits, trailing space, hex, empty;
  - CAP values `None`, `0`, a float, a string, `True`.
- The listing parser and rule patterns (absent, empty chain, set rule,
  mbytes).
- `sudo_refused()`.
- The fake's own listings verify for every recipe; flush-then-cap; an
  absent delete is an nft error, not a sudo refusal; deny and password;
  the fake refuses non-`nft` argv.

**Defects found and fixed during testing.**

1. **The first `--fast` attempt (14:19Z)** saw EOF at the Enter prompt,
   so it aborted at preflight. That abort path worked: delete (rc 1, no
   table), `list tables` absent, exit 130. The cause: children inherited
   stdin, and `adb shell` consumed the piped newline. On the night the
   same `adb shell` could read the user's keyboard. Fix: `stdin=DEVNULL`
   on every child except `sudo -v`. The run dir was discarded.
2. **The first A1 (14:44:58Z) was not a valid test.** The driver starts
   the harness with `&` in a non-interactive bash script, which starts
   it with SIGINT ignored. Python then keeps SIGINT ignored, so the run
   went to a normal end (exit 0; the checker still passed the fault
   removal). At a real terminal Ctrl-C would have worked. Fix: `run()`
   installs `signal.default_int_handler` explicitly. The first batch's
   A1 and A4 are kept in `logs/streaming/c3_l4_l2b_tests/first_batch/`.

Also changed during testing:

- The final clear no longer runs a second time inside `teardown()`
  (the full run shows it twice).
- `reauth()` now says "the fault stayed on; verified" when sudo refused
  the delete (the first A4 said "re-applied").

**Code versions.**

- The full run, A2 and A3 ran on the code before the SIGINT handler,
  the teardown dedupe and the reauth wording. None of these touches
  their paths except the dedupe, which removes a repeat of the same
  delete and list.
- A5 ran on the code before the reauth wording.
- A1 and A4 were re-run on the final code.

**The full `--fast` run** (14:24:17-14:41:59Z, clean link, sessions
F1,F2,F3,K, holds 60 s): **PASS**, exit 0.

- **Sudo calls.** 42 fake-sudo calls, all of them `-v`, `-n -v` or
  `-n nft …` from the allow-list: 1 validate, 4 keepalives, 4
  add_table, 4 add_chain, 1 counter, 3 cap, 1 loss, 1 drop, 2 flush, 6
  delete, 8 list_table, 7 list_tables.
- **Calibration** from the counter: 1,083 kB/s, CAP **869** kbytes/s.
- **Verification.** Every apply verified the expected rule; every
  remove verified the table absent. F3's drop was on **15.02 s**.
- **K.** Status `mode shadow, configured live, acts false`; `live`
  again after BACK.
- **At the end.** Delete, then `list tables`: absent. Teardown
  **CLEAN**: `PRIVYHUB_*` 0/0, mode off, stream 7000, no game, 0
  banners.
- **Files** 23/23. 415 sample rows. No transition, as expected on a
  clean link: the fake drops nothing.

**Forced aborts** (`l2b/l2b_abort_tests.sh`; each checked by
`l2b/l2b_check.py`). Each check requires:

- every fake-sudo call is `-v`, `-n -v` or `-n nft`;
- the delete-table call is logged;
- a `list tables` after the last delete with rc 0 and no
  `privyhub_fault`;
- nothing added after it;
- `no_fault_table_at_end`;
- teardown clean, with no flags;
- the fake's table absent.

| Test | What | Harness | Result |
|---|---|---|---|
| A1 | SIGINT 10 s into F1's cap (15:01:34Z, final code) | `ABORTED (Ctrl-C)` → delete rc 0 → absent → CLEAN; exit 130 | **PASS** |
| A2 | SIGHUP 10 s into F2's loss (14:49:24Z) | `ABORTED (SIGHUP)` → delete → absent → CLEAN; exit 129 | **PASS** |
| A3 | an exception in F3's drop countdown (`--test-fail-at F3_drop`) | `ERROR RuntimeError` → delete → absent → CLEAN; exit 4 | **PASS** |
| A4 | the fake refuses `-n` from 2 s after F2's apply (keepalive 20 s; final code, 15:03:43Z) | keepalive refused → `PAUSED` → delete refused (fault stayed on) → `sudo -v` → verified → "the fault stayed on; verified" → F2 finished normally → removed → CLEAN; exit 0 | **PASS** |
| A5 | the fake's listing shows no rule (the mismatch path) | F2 apply → `VERIFY … NOT AS EXPECTED` → `!! MISMATCH` → STOPPED → delete → absent → CLEAN; exit 3 | **PASS** |

**Dry-run smoke** (`--dry-run --sessions F1,F3`, no sudo): **PASS** (15:06:37-15:14:04Z, exit 0). No sudo call was made (no `nft_commands.jsonl`); each fault printed as "not run" with its allow-listed argv; CAP from the estimate, 869; teardown CLEAN; files 17/17.

**Not tested.** The real `sudo` and `nft`: the password prompt, the
real keepalive, nft's real listing format, and a real SSH drop. These
run only when the user runs the night. The verify patterns follow nft's
documented output. If the real listing differs, the night stops at the
first verify, with the fault removed and the listing in
`nft_tables.txt`: a safe failure, not a silent one.

## L2B.4 The user's hand steps (replaces §7 above)

For a Windows PC with **one** PowerShell window, SSH'd into the host the
way you always connect. Allow ~90 minutes, with no Code queue running.
Nothing is needed on the TV.

1. `tmux new -s nft`
2. `cd ~/Projects/onn-stream-test && python3 tools/c3_l4_nft_night.py`
3. Type the sudo password when asked. Press Enter to accept the
   pre-registration. Then wait ~90 minutes; there is nothing else to
   type.
4. To stop early: `Ctrl-C`. The fault is removed automatically.
5. If the SSH connection drops: reconnect and `tmux attach -t nft`. If
   the harness asks for the password again, type it.
6. At the end it prints `RUN DIRECTORY: …`; tell Claude "nft done".

Notes:

- *(Optional, before step 2)* the pre-registration can be amended:
  `docs/memory/evidence/c3_l4_l2_2026-09-29/c3_l4_l2_nft_preregistration.txt`.
- If it says **REFUSED**, fix the reason it gives and start again at
  step 2. Nothing has been changed.
- If the harness itself is gone and it says `COULD NOT CONFIRM THE
  FAULT IS GONE`, type:
  - `sudo nft delete table inet privyhub_fault`
  - `systemctl --user unset-environment PRIVYHUB_ADAPTIVE_BITRATE_MODE && systemctl --user restart privyhub-companion`
  - `curl -X POST localhost:8765/plugins/games/stop`

## L2B.5 Files (`c3_l4_l2_2026-09-29/l2b/`)

- `c3_l4_nft_night.py` is updated in the parent dir. The L2 version is
  kept as `l2b/c3_l4_nft_night.L2.py`.
- Test code: `c3_l4_fake_sudo.py`, `test_c3_l4_nft_night.py`,
  `unit_tests.txt`.
- The driver and checker: `l2b_abort_tests.sh`, `l2b_check.py`.
- `runs/<test>/`: for the full run and A1-A5, the console,
  `summary.json`, `events.jsonl`, `nft_commands.jsonl`,
  `nft_tables.txt` and the fake's `argv.jsonl`.
- `runs/dryrun_F1_F3/`: the dry-run smoke.
- `aborted_attempts.txt`: the three aborted run dirs' harness logs,
  pre-registration lines elided.
- Full run directories stay in `logs/streaming/c3_l4_l2b_tests/`;
  the aborted attempts are in `logs/streaming/aborted/`.
- `sha256_manifest.txt` (parent dir) is regenerated.

Nothing adopted. Nothing committed. No companion or client change.
