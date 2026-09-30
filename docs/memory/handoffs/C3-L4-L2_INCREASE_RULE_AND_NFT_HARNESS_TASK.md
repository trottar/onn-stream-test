---
memory_schema: 1
as_of: 2026-09-29
status: TASK HANDOFF — C3-L4-L2: (1) the live controller's increase rule replaced by the user's choice of 2026-09-28 ("your blend": clean = no ROUTINE-level sample, step up one rung when >= 85 of the last 90 reports are clean); (2) per-report sample logging in live; (3) Session B repeated to show the climb 5000 -> 7000; (4) the nft-night harness the user runs themselves, dry-run tested; nothing adopted; nothing committed; authorized by the user 2026-09-28/29
---

# C3-L4-L2 — the increase rule, sample logging, and the `nft` harness

**Why.** `C3_L4_L1_LIVE_CONTROLLER_2026-09-28.md` §5: the pre-registered
increase rule (90 **consecutive** reports with fps ≥ 59, queue 0,
gap ≤ 150) is not reachable on a clean link — longest runs 21 at 7000
and 32 at 5000 — so a stepped-down session stays down (Session B
PARTIAL, B6). The replays show the live controller would have stepped
down 5 times (ROUTINE 7000 → 6000) over the recorded soak nights and
never come back. **The user chose the blend on 2026-09-28**: "clean" =
no ROUTINE-level sample (fps ≥ 57, queue ≤ 1, gap ≤ 150, the record's
option (a) definition), and an increase when **≥ 85 of the last 90**
reports are clean (the heartbeat proxies: 96.2-96.9 % of reports clean by
that definition on a clean link). This is a decision the user made on
the data, recorded as theirs; it is not a loosening by Code.

Read first: the L1 record in full (§1 mapping table, §5 the finding and
its proxies, §7 the `nft` hand-step list and its proposed
pre-registration), `c3_l4_l1_2026-09-28/increase_rule_check.txt`,
`c3_l4_l1_run.sh`, `c3_l4_l1_analyze.py`, `companion/adaptive_bitrate*.py`
as L1 left them, `decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`,
`evidence/D_BASE_R3B_NFTABLES_LINK_DROP_2026-09-22.md` (the fault shape,
the table name, how R3b's harness and the user split the work),
`evidence/D_BASE_R3D_HAND_RUNS_2026-09-22.md` (hand-run ergonomics that
worked), `TOOLS.md`.

**Scope.** Companion: `LivePolicy`'s increase rule and its constants;
a per-report `sample` row in the live controller's log; nothing else.
The shadow policy is **unchanged** (its suite passes unchanged; its
increase rule stays its own). No profile, encoder, FEC or client change;
adopted APK stays. One new tool: `tools/c3_l4_nft_night.py` (or `.sh`).
No `nft` is ever run by Code or by the harness; the harness prints the
lines for the user to paste.

## 1. The rule, as code

- `clean(report)` = fps ≥ 57 **and** queue ≤ 1 **and** output gap ≤ 150
  **and** telemetry fresh (a stale report is neither clean nor unclean:
  it is skipped and does not advance the window).
- The window: the last 90 evaluated reports **since the last SSRC change
  and its 3-report blackout** (a transition, recovery's restart, a
  session start — the window starts empty after each).
- **INCREASE** one rung (5000 → 5500 → 6000 → 7000) when the window is
  full (90) and ≥ 85 are clean **and** every hold-down in force has
  expired **and** the oscillation guard allows it. One rung per event;
  the window starts empty again after the resulting SSRC change, so the
  minimum spacing between increases is 3 + 90 = 93 reports ≈ 186 s.
- Decreases, hold-downs, blackout, rate limit, age and recovery guards,
  disable route: **unchanged** from L1.

Tests (synthetic, offline): the window fills and fires at exactly 85/90;
84/90 does not fire; a stale report does not count; the window empties
after every SSRC change; a hold-down in force blocks a full window; the
oscillation guard turns the third direction change in 10 min into `HOLD`;
one rung per event, never two; the L1 suite otherwise unchanged and
passing; the shadow suite unchanged and passing; **parity** re-run (the
shadow night through live: still zero actions — an increase needs a prior
decrease); the recorded-loss replays re-run with the new rule, the
would-fire list now including increases, the rate limit never tripping
(else say so).

## 2. Per-report samples

In live mode, one `sample` row per evaluated report in the controller's
log: time, session elapsed, fps, queue depth, output gap, fresh, clean
(by the new rule), window count/clean count, state, level, blackout
remaining, hold-downs remaining. Rotated with the existing log (state the
size per hour). This is what lets the `nft` night be re-scored offline
under any rule later. The chatty state-change lines L1 noted are left as
they are (noted, not changed here).

## 3. Session B2 — the climb, pre-registered before it runs

Live + inject (test-only, as L1). After 120 s of PLAYING, one injected
FALLBACK; 30 s later a second. Then no input, clean link, up to **25
minutes** after the first injection, then BACK.

**WIRED** if all of:
- one `ssrc_change` from the first injection, to 5000, output gap
  reported against 186.5 ms; blackout 3; the second injection refused
  `hold_down`;
- the stream then climbs **5000 → 5500 → 6000 → 7000**, one rung per
  event, each increase ≥ 93 reports after the previous SSRC change, each
  recorded with its time, window count, clean count and gap;
- at 7000, no further transition for the rest of the hold;
- `ssrc_changes` over the session = 4; the report stored; lifecycle
  clean; close-out rows met (reported).

**PARTIAL** naming what did not hold (e.g. the climb stopped at a rung —
then the per-report samples say why).

## 4. The `nft` night harness — the user runs it

`tools/c3_l4_nft_night.py`, run by the user in tmux on the host, one
pane for the harness and one for `sudo`. It implements the L1 record's
§7 steps 1-13, **with the expectations updated for the blend** (§7's
"[if (a)/(b)]" branches now apply: under the cap the stream steps down,
tries 5500, then 6000, falls back, and the oscillation guard holds it).
The harness:

- **preflight** (idle host, no game, no `PRIVYHUB_*` in the manager,
  adopted profile, adopted APK hash) and refuses to start on any failure
  with the reason;
- sets `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live` through
  `systemctl --user set-environment` and restarts the unit (never
  `INJECT`); confirms `mode live, level 7000`;
- starts the T2 sampler, the 5 s status poller and the heartbeat capture
  as `c3_l4_l1_run.sh` does, and launches the attract-mode title to
  PLAYING the same way L1 did (adb), recording `any_override`;
- at each fault step **prints the exact `sudo nft …` line to paste** in
  the other pane (the table, chain and rule as §7 gives them, the video
  port only, audio and adb untouched) and waits for Enter, recording the
  time the user pressed it; every `nft list` line it prints ends in
  `| tee -a <run dir>/nft_tables.txt` so the harness reads the counters
  itself;
- **computes CAP** from the two counter readings (step 5) and prints the
  cap rule with the number filled in;
- prints, before each fault, one line of **what the controller should do**
  and, after each, one line of what it did (from the status series), so
  the user can see it live;
- runs Fault 1 (cap, 12 min, then removed, 5 min), Fault 2 (2 % random
  loss, 10 min, removed, 5 min), Fault 3 (cap to reach 5000, then a 15 s
  full drop of 48100 and 48101, removed), and the kill switch twice
  during a fault (the harness calls the disable route itself);
- at every step and on Ctrl-C, prints the **delete-table line first**
  so the user can always clear the fault; at the end confirms (by asking
  the user to paste `sudo nft list tables | tee -a …`) that no
  `privyhub_fault` table remains;
- tears down: flag unset, unit restarted, flags absent from the manager
  and the MainPID environ, stream at 7000, game inactive, banner cleared,
  samplers stopped;
- writes everything to `logs/streaming/c3_l4_nft_night_<stamp>/` and
  prints the directory at the end. Scoring is a later Code task, from
  those files.

**The pre-registration for the night** is written by this task, before
the night, to `c3_l4_l2_nft_preregistration.txt` in the evidence dir and
printed by the harness at start: the L1 record's proposed
"WORKS UNDER LOSS" rule with the blend's Fault 1 expectation (one
decrease per event; the climb/fall/`HOLD` sequence; `rate_limited`
never true; no ramp), Fault 2 at most one decrease, Fault 3 no controller
action while recovery is not PLAYING and recovery restarts at the held
level, the kill switch as described. The user may amend it before
starting; the harness records the file's hash.

**Dry run** by Code: `--dry-run` runs the whole flow with each fault
replaced by a 30 s wait (no `nft` lines printed as required; prompts
auto-advance), holds shortened to 60 s, on the clean link. Pass = the
harness gets from preflight to teardown with all recorders writing, the
flag set and unset correctly, and the directory complete. Record its
output.

**Hand steps for the user**: the record ends with the numbered list the
user follows on the night — open tmux with two panes, the one command
that starts the harness, what to paste where, what they should see, how
long each part takes (~75-90 min total), and how to abort safely at any
point. Placeholders only; no addresses.

## 5. Teardown

Flags unset and confirmed absent, companion under systemd, profile
adopted, adopted APK hash confirmed, stream at 7000, game inactive,
banner cleared, samplers stopped.

## Record and memory

`evidence/C3_L4_L2_INCREASE_RULE_<date>.md` (the user's decision quoted,
the rule as built, the tests, the replays, Session B2 and its outcome,
the harness and its dry run, the night's pre-registration, the user's
hand steps); evidence dir with tests, logs, report, samples, harness
dry-run output, manifest; `patches/C3-L4-L2_*.md`; `PATCH_INDEX.md`;
`decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md` (append: the increase
rule, the user's choice); `architecture/ADAPTIVE_BITRATE.md` (live
increase rule as built); `docs/ROADMAP.md` C3; `CURRENT.md` (Next Action
1: the user's `nft` night with the harness); `investigations/ACTIVE.md`;
`TOOLS.md` (the harness; never leave live or inject set); the daily file;
`evidence/RUNTIME_VALIDATION.md`. No addresses. Nothing adopted. Nothing
committed.
