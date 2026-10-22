---
memory_schema: 1
as_of: 2026-10-21
baseline_commit: 357ee73 (UX-R2 committed; the tree carried the two user prompts and A's UX-R3 task file, not touched)
---

# LAN-R1 — why the ladder sat at 7000 through Sunday, and a step-down rule behind a flag

**Classification: software only.**
- **§1:** the replay reproduces both evenings exactly. The ladder cannot step down on loss alone: every decrease bar
  needs an fps term, and Sunday's fps mostly held ≥ 57.
- **§2:** `PRIVYHUB_LAN_LOSS_RULE=1` is BUILT (absent = today, proved by replay).
  - It steps one rung down on sustained FEC-unrecoverable groups: T 4 per 10-s window on K 2 windows.
  - On Sunday its first step is **05:03:05Z, ~3 min before the 05:06 burst**.
  - It makes 0 asks in every clean window on file. Last night it made two asks, refused by the session-age guard.
- **The separation is thin and in sample**, and the rule also fires on random loss (G8-S1 loss-1).
- **NOT ADOPTED, nothing committed, no live run.** The live test is session A's.

Task: `handoffs/LAN-R1_LOSS_STEPDOWN_REPLAY_AND_DESIGN_TASK.md`, session B. **The user's standard (verbatim):** "This
product needs to work at any house especially lan as long as the Internet is over 50mb/s."

Design `lan_r1_2026-10-21/design_written_before_code.md`, sha256 `6370e9fd…14d5`, hashed **20:54:35Z, before any code
edit** (the §1 replay ran on HEAD first).
- **UX-R3 had not landed** when §1 and the design were done, so the steps and bursts were used.
- **It landed during this task** (`UX_R3_FIND_THE_DEATHS_2026-10-21.md`, session A), and was read before this record.
  §1.2b adds its death seconds. It changes no number above it, and nothing under `ux_r3_2026-10-21/` was touched.

## 0. The inputs (`lan_r1_2026-10-21/inputs/`, `inputs_sha256.txt`, `copied_at.txt`)

All copied before use:
- **From `ux_r1_2026-10-20/session/` and `ux_r2_2026-10-21/session/`:** the ladder log
  (`adaptive_bitrate_shadow.jsonl` and `stream_log_archive/…​.1-3`), the recovery log and the heartbeat log, each
  checked byte-equal to its source.
- **From the UX records:** their `timeline.json` (the per-minute tables).
- **From `logs/games/stream_log_archive/`, read only:** `native_stream_heartbeat.log.1-3`. These are for the clean
  windows of 10-18/19 and the G8-S1 cells.

Each ladder `sample` (what the controller read) is joined to the nearest client heartbeat within 1.5 s / 1,500 ms
of elapsed (`lan_r1_series.py`):
- **Joined:** 1,686 / 1,709 samples on Sunday, 1,172 / 1,180 last night, and 100 % in the clean windows.
- **The ladder's loss and the heartbeat's agree:** 10,353 / 10,195 on Sunday, resync jumps included.
- **Disclosed:** 04:55-05:08 on 10-21, the heartbeat and the telemetry were two sends ~0.5 s apart, not the same
  report.

## 1. The replay (before any design)

### 1.1 HEAD, flag absent: **exact** (`replay_head.md`)

Through G5-S2's harness (`../g5_s2_2026-10-16/replay.py`, reused unchanged), fed from `inputs/`:

| evening | client sessions | sample rows | recorded decision / state events | recorded reproduced | controller HEAD vs tree |
| --- | ---: | ---: | ---: | --- | --- |
| UX-R1 Sunday | 41 | 1,709 | 505 | **exact** | **identical** (2,256 rows) |
| UX-R2 last night | 12 | 1,180 | 318 | **exact** | **identical** (1,510 rows) |

The same table again **after the code** (`replay_after_code_console.txt`): exact, identical, the same counts.

### 1.2 `PRIVYHUB_WAN_ADAPTATION=1` on the same inputs (`replay_head.md` / `.json`)

**The rules are not gated on a remote `path_class`** (`wan_adaptation.py`, read):
- R2 (latency-limited / starved) and R3.1 (capacity-limited → one rung) run on any path.
- Only R3.2 (the 4000 floor) and R5's K depend on `path_class`.
- `lossy` is not a step-down class: it only makes a window not clean for R5. **At 7000 there is no increase to
  block.**
- So "gated / gate lifted" is moot. Both readings are tabulated and they are identical.

| evening | suggestions (by rule) | per minute | what they did |
| --- | --- | --- | --- |
| Sunday | 6: R3.1 4, R1.2 2 | **05:11 only** | R3.1 `step_down` on the same tick as the ladder's own `capacity_mild` 7000→6000 (05:11:01): `transition`; then R1.2 `no_step_up` ×2 |
| Last night | **0** | — | — |

- **Where R2 / R3 would have stepped down:** nowhere but 05:11.
  - **Not at 04:56, 05:06, 05:10 or 05:20.** No window there was `capacity-limited`: G5-S1's bar is the ladder's
    own capacity terms, which need fps < 57 / < 50.
  - **Not at last night's 04:52 step.**
  - No two consecutive windows were `latency-limited`.
  - G5-S1's `starved` class (stale output drops) cannot be met on the evenings: the ladder log carries no
    stale-drop field and there is no run telemetry (disclosed).

### 1.2b UX-R3's death seconds (last night, 04:54:55-04:54:59Z; read from UX-R3 §1 / §3, not re-derived)

- **G5-S2's rules:** no suggestion last night at all (§1.2), so none in the death.
- **The LAN rule (§2), on the same reports:**
  - Unrecoverable groups 1 (04:54:53.9), missing (04:54:59.4, the held report) and 7 (04:54:59.9).
  - The window before held 0 (04:54:31-04:54:51).
  - **No 2 × 10-s run reached ≥ 4, so no ask.**
- **This agrees with UX-R3 §3:** "No rule of the adopted ladder can act on a 3-5-s bidirectional drop."
  - The rule built here acts on sustained loss (Sunday's minutes), not on a one-report drop.
  - UX-R3 also notes that a step down would not prevent a link drop.
- **The second death is not distinguishable** (UX-R3: five small hitches in 04:56-05:03Z). Those minutes count among
  last night's clean minutes here (§2.1), and the rule made no ask in them.

### 1.3 What `live` saw, per bad minute, and why none of its bars was met (`what_live_saw.md`)

The adopted ladder's decrease bars, over the last 5 evaluated reports:
- capacity_mild: **fps < 57 on ≥ 4 AND lost ≥ 50 on ≥ 3**;
- capacity: fps < 50 on all 5 AND lost ≥ 50 on ≥ 3;
- FALLBACK: fps < 50 on all 5 AND (queue ≥ 2 on ≥ 3 OR gap > 250 ms on ≥ 2);
- ROUTINE: fps < 57 on ≥ 4 AND queue ≥ 1 on ≥ 3.

**Every bar carries an fps term. Loss alone never meets one.**

| minute | post-FEC lost (ladder) | unrec groups | fps min / mean | most fps<57 / lost≥50 in one 5-window | why no bar |
| --- | ---: | ---: | --- | --- | --- |
| 04:56-05:05 (the step) | 28-80 per min | 2-13 per min | 25.8-53.8 / 57.0-60.9 | ≤ 4 / **0** | the loss came as a few packets per report: never ≥ 50 in one report |
| 05:06 (burst) | 491 | 29 | 16.0 / 56.1 | 3 / 1 | the loss in one report; fps < 57 on 3 of 5 at most |
| 05:09 | 128 | 15 | 23.9 / 59.2 | 2 / 0 | as above |
| 05:10 (burst, fps 47) | 5,376 (4,229 in resyncs) | 60 | 0 / 53.2 | 3 / 2 | the loss in 2 reports; 2 resync + 3 blackout reports are not evidence |
| 05:11 | 1,310 | 25 | 0 / 50.8 | 4 / 4 | **met: capacity_mild 7000→6000 at 05:11:01** (the one acted step; reset to 7000 at the next start) |
| 05:20 (burst) | 279 | 25 | 31.9 / 63.1 | 2 / 1 | the loss in one report |
| 05:21 (burst) | 899 | 64 | 12.0 / 56.6 | 4 / 3 | **both counts reached, never in the same 5-report window** |

**The answer to "why 7000 throughout":**
- Sunday's loss arrived as small per-report amounts (under 50 in every report from 04:56 to 05:05), then as
  single-report bursts. The picture's fps stayed ≥ 57 on most reports.
- The ladder was tuned on the capacity shortfall of the nft nights, where fps falls *and* every report loses ≥ 50.
  It reads loss only behind an fps term.
- The FEC-unrecoverable groups are in its telemetry, and it does not read them.

### 1.4 G8-S1's loss cells at a 7000 start (from `G8_S1_ADVERSE_NETWORK_ENVELOPE_2026-10-17.md` §2c)

| cell | post-FEC loss / min; fps | the ladder's rung path |
| --- | --- | --- |
| loss-1 off / on | 46 / 65; 59.5 | **7000 throughout** / **7000 throughout** |
| loss-5 off | **809; 52.6** | **7000 throughout** |
| loss-5 on | 3,305 (wan); 53.8 | 7000→5000 `recovery_escalation` (recovery's two restarts, not loss) |
| burst-50x20 off / on | 829 / 148; 57.5 / 59.7 | 7000→6000 `capacity_mild` / 7000 throughout |
| delay-50+loss-1 off / on | 117 / 162; 59.2 / 59.3 | 7000 throughout |

**The bench showed the same gap four days before Sunday.** At 5 % random loss (809 / min, fps 52.6) the ladder held
7000: fps never under 50 on all 5, and the loss did not reach ≥ 50 on ≥ 3 reports together with fps < 57 on ≥ 4.

## 2. The rule

### 2.1 T and K from the data (`threshold_search.md` / `.json`)

The search:
- the rule fires when each of the newest K non-overlapping 5-evaluated-report windows (10 s each) holds ≥ T, with
  session age ≥ 60 s;
- two metrics: the post-FEC loss the ladder reads, and the FEC-unrecoverable groups;
- T × K = 13 × 12 (loss) and 10 × 12 (unrec).

**Clean windows:** CL-B5 A / B / L, CL-B6 1 / 2, CL-B7's three arms, G4-S3, and last night's clean minutes.
- **G4-S3 has no LAN part:** it was over the overlay at 4000, and it is kept as a remote clean window.
- **A clean minute last night** was defined before the search: hb_s ≥ 50, fps ≥ 59.5, resync 0, underruns ≤ 10,
  no ctrl gap > 1 s. That gives 31 of 43 minutes.

| | post-FEC loss | FEC-unrecoverable groups |
| --- | --- | --- |
| per-window max in the clean windows | 2-253 (spikes inside resyncs: CL-B5 L 253, CL-B7 lean 150) | **1-4** |
| per-window p99, Sunday / last night | 186 / 53 | 12 / 6 |
| zero-false-trigger pairs that fire on Sunday 04:51-05:06 | **none** (T 10 K 5 is zero-false but fires at 04:45 in King's Field, then not until 05:06) | **two: T 3 K 3 (05:01:38), T 4 K 2 (05:03:05)** |

**The finding:**
- **Post-FEC loss does not separate Sunday's pre-burst minutes from the clean windows.** The clean windows' own
  resync spikes are as large as Sunday's early loss.
- **The unrecoverable groups do, just:**

| unrec | K 1 | K 2 | K 3 |
| --- | --- | --- | --- |
| **T 3** | 42 false | 6 false | **0; Sunday 05:01:38** |
| **T 4** | 19 false | **0; Sunday 05:03:05 (chosen)** | 0; 05:11:00 |
| **T 5** | 4 false | 0; 05:06:57 | 0; 05:11:00 |

- **Both pre-05:06 pairs are edge cells.** One step toward sensitivity false-triggers; one step away fires only in
  the bursts.
- They were chosen on the data they are scored on. **The live test is the out-of-sample check.**
- **T 4 K 2 was chosen** over T 3 K 3 because it also fires in every burst minute (05:06, 05:10, 05:20), where
  T 3 K 3 misses 05:06 and 05:20.

### 2.2 The code (`lan_r1.diff`, `diffstat.txt`; predecessor `predecessors/adaptive_bitrate_live.py`)

- **New `companion/lan_loss_rule.py`** (120 lines, pure).
  - On each evaluated report it takes `telemetry.fec.unrecoverable_groups_delta`. That value is host-computed by
    `client_feedback.py` from each client-health report; missing counts 0.
  - When both of the newest 2 windows hold ≥ 4, it calls the ladder's own `_decide("ROUTINE", …)` with
    `capacity_mild`'s one-rung target, relabelled `lan_loss`. Every gate holds: the hold-downs, the blackout, the
    60-s age, the guards, the rate limit and the oscillation guard.
  - **Floor 5000.** Re-climb by the existing increase rule.
  - It asks only on a tick where the ladder decided nothing, with nothing pending (G5-S4's `after_feed` condition).
  - Its windows clear at a session reset, a blackout re-arm, and after each ask.
  - It writes one `lan_loss_rule` row per ask.
- **`companion/adaptive_bitrate_live.py` (+10 lines):** one guarded module-level import (`PRIVYHUB_LAN_LOSS_RULE`
  `1` only) and one `if` in `observe()` after G5-S4's hook. **The actuator is unchanged:** a step is the policy's
  `pending`, carried out by the existing `_maybe_actuate`.
- **Tests (in the `/tmp/b_lan_r1` copy of `companion/`, `tools/`, `tests/`):**
  - new `tests/lan_loss_rule` **21 OK** (`tests_lan_loss_rule.txt`);
  - wan_adaptation 23, wan_telemetry 18, remote_ladder 26, remote_cap 16, start_rung 17, overlay 17,
    session_identity 88, audio_codec 20, encoder_rc 16, impairment 14: all OK;
  - `tools/test_adaptive_bitrate_shadow.py` 21 OK;
  - `tools/test_adaptive_bitrate_live.py` **126 OK.** 125 ran in the copy. The 126th reads a golden file from
    `docs/memory/evidence/`, which the copy does not hold; it was run alone from the tree with `-B` (temporary
    directories only; `git status` unchanged before and after) and was OK (`tests_regression.txt`).
  - Two of the new tests' own expectations were wrong on the first run (the window cap; the designed re-climb from
    5000). The tests were fixed; the rule was not changed.
  - `git diff --check` clean.

### 2.3 The proof, through the real controller (`replay_after_code_console.txt`)

- **The flag absent:** §1.1's table repeated after the code: exact, identical.
- **The rule on:**
  - unrecoverable groups are injected per report from the heartbeat join;
  - a decision is actuated at once and the stream follows the ladder, except that each new client session starts
    at its recorded 7000 (C1);
  - the link is open loop: later reports are the recorded ones, which a lower rung would itself have changed.
    **No claim of improvement.**

| span | asks | steps taken (the rung path) | refused |
| --- | ---: | --- | --- |
| **Sunday** | 7 | **05:03:05 7000→6000; 05:06:07 →5500; 05:10:48 →5000**; (Zelda, a new session at 7000) **05:20:52 →6000** | hold-down 3 |
| **Last night** | 2 | — | **guard 2: the session-age guard**, 24.6 s and 26.6 s into the Soul Reaver and Symphony sessions (05:12:50, 05:17:32; neither a clean minute) |
| CL-B5 A / B / L, CL-B6 1 / 2, CL-B7 pcm / today / lean, G4-S3 | **0 each** | — | — |
| G8-S1 loss-1 off / on | 6 / 7 | 7000→6000→5500→5000, both: first step 3-4 min after the cell's start, 5000 at 9-11 min | hold-down / guard |
| G8-S1 loss-5 off | 15 | 7000→6000→5500→5000 (21:14:58-21:19:11) | |
| G8-S1 loss-5 on | 2 | — (the ladder's own `recovery_escalation` had taken 5000) | guard 2 |
| G8-S1 burst-50x20 off / on | 5 / 0 | 7000→6000 (00:49:33, 2 s before the recorded `capacity_mild`) →5500 / — | |
| G8-S1 delay-50+loss-1 off / on | 13 / 10 | 7000→…→5000, both | |

**Read plainly:**
- **Sunday, with the rule:** 6000 three minutes before the 05:06 burst, 5500 in it, 5000 in the 05:10 burst. That is
  what the user's standard asks of the ladder. Whether 5000 would have spared the room the bursts, the open-loop
  replay cannot say.
- **The clean windows:** no ask at all.
- **Last night:** the condition held twice, both inside a session's first 30 s, and both were refused by the
  60-s age guard. **Not in the death (04:54:55-04:54:59Z), §1.2b.** The user's "two memorable instances where I
  literally died" are not what this rule addresses.
- **The cost:** under G8-S1's 1 % random loss the rule takes the stream to 5000 within 9-11 min of the start. A lower rate does not
  reduce random loss.
  - On such a link the rule spends picture for nothing. The increase rule climbs back (loss does not make a report
    unclean), and the oscillation guard ends a down / up / down cycle.
  - **Whether Sunday's room was congestion-like or random-like is not known** (UX-R1: the link or the onn, not
    split).

### 2.4 What the client already sends, and what the ladder reads

| signal | sent by the client | in the ladder's telemetry | read by the ladder today |
| --- | --- | --- | --- |
| post-FEC lost packets (per report) | yes (client health) | `receiver.lost_packets_delta` | yes, behind an fps term |
| FEC-recovered packets | yes | `fec.recovered_packets_delta` | read into the sample, unused |
| **FEC-unrecoverable groups** | yes | `fec.unrecoverable_groups_delta` | **no** (this rule, behind the flag) |
| output gap (per report) | yes | `latency.output_gap_ms` | yes: FALLBACK's > 250 ms term, behind fps < 50 on all 5; the increase rule's ≤ 150 |
| decode queue (video) | yes | `decoder.queue_depth` | yes: ROUTINE / FALLBACK queue terms |
| audio underruns, concealment, arrival gaps | yes (the heartbeat) | no | no |
| Opus decode queue depth / wait | the session report, at the end | no | no |

**What a per-second signal would add (noted, not built):** the client's per-second output gap or audio arrival gap.
- Sunday's burst minutes show 543-1,287-ms audio arrival gaps, and the host's control gaps reached 434-991 ms in 7
  of the 8 minutes 04:58-05:05. The 2-s report sees the burst, and the per-minute counters average it away.
- A per-second gap would date the onset inside a report and need no fps term.

## 3. For the live test (session A, later; sketched)

1. The shim at a 7000 start: loss-1, loss-5 and burst-50x20, each with the flag absent and then with
   `PRIVYHUB_LAN_LOSS_RULE=1` (a drop-in, restart; removed after).
2. Read the `lan_loss_rule` rows, the rung path and the host gates.
3. **The prediction from this replay:**
   - loss-1 and loss-5 step down 3-4 min in and reach 5000 by ~8-11 min;
   - burst-50x20 steps ~2 s before `capacity_mild`;
   - flag absent, as G8-S1.
4. Then the user's room, on an evening.

## 4. Files

**`lan_r1_2026-10-21/`:**
- `baseline_head.txt`, `git_status_at_start.txt`;
- `inputs/` (with `inputs_sha256.txt`, `copied_at.txt`);
- `lan_r1_series.py`, `lan_r1_replay.py`, `lan_r1_analysis.py`;
- `replay_head.md` / `.json` / `_console.txt`;
- `what_live_saw.md`, `threshold_search.md` / `.json`, `analysis_console.txt`;
- `design_written_before_code.md`, `design.sha256`, `design_hashed_at.txt`;
- `predecessors/`, `predecessor_sha256.txt`, `after_sha256.txt`, `lan_r1.diff`, `diffstat.txt`;
- `tests_lan_loss_rule.txt`, `tests_regression.txt`;
- `replay_after_code_console.txt`;
- `redact_check.py`, `redact_check.txt`, `manifest.sha256`.

**Elsewhere:**
- `companion/lan_loss_rule.py` (new), `companion/adaptive_bitrate_live.py` (+10);
- `tests/lan_loss_rule/test_lan_loss_rule.py` (new);
- `patches/LAN-R1_LOSS_STEPDOWN_RULE.md`;
- `docs/KNOWN_ISSUES.md` (the top item), `docs/ROADMAP.md` (§G8, one line);
- `logs/lan_r1_git_status.txt`;
- `handoffs/SESSION_B_STATUS.txt`, `handoffs/SESSION_B_DONE_2026-10-21.md`.

**A byproduct, left (nothing deleted):** `lan_r1_2026-10-21/__pycache__/`. One helper import of `lan_r1_series.py`
ran without `-B`. Everything else ran with `-B`, and no cache was written under `companion/`, `tools/` or `tests/`.
`docs/memory/CURRENT.md`, `UX_R3_…` and `ux_r3_2026-10-21/` show in `git status`; they are session A's, not touched
here.

**Left outside the tree:** `/tmp/b_lan_r1` (the copy of `companion/`, `tools/`, `tests/` and the test output) and
`/tmp/b_lan_r1_replay_tmp` (the harness's temporary controller logs). Nothing deleted.

No companion restart, no stream, no adb, no sudo, no nft, the Opal untouched, nothing fetched. Before each replay and
suite, `systemctl --user` showed no `privyhub-*` unit active but the companion service itself, which is always
running and was neither restarted nor loaded by the work. Nothing of A's touched. Nothing adopted; nothing committed.
