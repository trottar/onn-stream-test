---
memory_schema: 1
as_of: 2026-10-16
status: TASK HANDOFF — G8-S1, session A: the first adverse-network envelope (ROADMAP §G8), run on the LAN through G8-P1's impairment shim at `@post-fec`, one PS1-STREAM per profile, with G5-S1's classifier on and G5-S2's rules off then on. Detached from the Code session (as the link watch was): Code hashes the pre-registration, launches the driver under `systemd-run --user`, confirms the first run, and exits; a status file per run; a STOP file; a cap. Measurement only; nothing adopted; nothing committed
---

# G8-S1 — the adverse-network envelope, first pass

**What this gives.** For each impairment the envelope §G8 asks for —
loss, burst loss, delay, jitter, reordering, a rate cap — what the
stack actually does: FEC recovery, the loss the client sees, rendered
fps, stale drops, the ladder's rung path, the G5-S1 class — and, in a
second arm, what G5-S2's rules change. No universal claim (one LAN, one
host, §G8's caveat); the operating envelope and the failure behaviour,
as measured.

Read first: `G8_P1_…` (the profiles, `@post-fec`, the shim's cost and
telemetry, the G8-S1 proposal), `G5_S1_…` and `G5_S2_…` (the `wan`
object, the rules, the LAN caveat on R5), `CL_B3_…` §W (the WAN
telemetry live smoke: the flag's cost), `E4_S4D_…` / `e4_s4d_watch.py`
(the detached-driver pattern: unit, status file, STOP, cap, busy skip),
E4-S2's constraint discipline (a drop-in per run, read back, removed at
teardown).

## 1. Pre-registration (hashed before the first run)

- **Runs** (`tools/e1_suite.py run --e2 --window 600`, idle gap 120 s,
  E2's warm-up): E1-PS1-STREAM ×1 per cell of {profile} × {rules off,
  rules on}; profiles in this order: `none` (the control, the shim in
  the path with no impairment — its own cost), `loss-1`, `loss-5`,
  `burst-50x20`, `delay-50`, `delay-150`, `jitter-30`, `reorder-5`,
  `cap-6000`, `cap-4500`, `delay-50+loss-1`, all `@post-fec`, seed 1.
  22 runs, ~4.6 h. Each run's `e3_flag.conf` carries exactly:
  `PRIVYHUB_WAN_TELEMETRY=1`, `PRIVYHUB_IMPAIRMENT=<profile>@post-fec,seed=1`
  (absent for `none`'s arm? no — `none` is a named profile so the shim's
  own cost is measured), and `PRIVYHUB_WAN_ADAPTATION=1` in the "on"
  arm only; written, read back from the unit's environment under load,
  removed at teardown with `flags_absent` true before the next run.
- **Validity:** E3-A3B's reading (reaches PLAYING; replaced ≤ 2× if
  not); a run whose shim telemetry shows the profile not applied
  (`impairment.jsonl` outside the G8-P1 tolerances) is `profile-not-applied`
  and repeated once.
- **Gates (host side only):** RetroArch ≥ 59.9; capture 60 ± 0.1;
  dup+drop ≤ 0.2/min; the shim's cost reported; the companion's cost
  with the two flags reported. **Everything link-side is reported, not
  gated** — this is the envelope, there is no pass/fail: per cell,
  pre-/post-FEC loss per min, FEC recovered / unrecoverable groups,
  rendered fps, stale drops/min, spikes/min, resyncs, client pauses,
  the ladder's rung path (polls) and the rules' suggestions (decisions
  with `source: wan_rules`), the `wan` class counts per window, the
  shim's own counters (in / dropped / delayed / reordered / queue
  depth max).
- **Comparisons written beforehand:** (i) `none` vs CL-B3's run (the
  shim's cost on the stream); (ii) per profile, off vs on: what the
  rules changed and whether rendered / stale / loss moved with it —
  stated, not judged; (iii) the class the G5-S1 classifier assigns vs
  the profile's intent (does `cap-4500` read `capacity-limited`, does
  `delay-150` read `latency-limited`, does `loss-5` read `lossy`?) — a
  classifier check, reported as a table.
- **Reported:** the link's own loss that night (the `none` arm is the
  baseline; the LAN has been lossy all week), the ladder's behaviour
  under the cap profiles, any session loss or recovery event.

## 2. The driver (detached)

- `g8_s1_2026-10-16/g8_s1_driver.py`, launched by Code under
  `systemd-run --user --unit=privyhub-g8-s1 --collect`; not a child of
  the Code session. Status file `~/privyhub_g8_s1/status.txt` rewritten
  after every run (UTC, cell n/22, the profile and arm, the run's status,
  loss post-FEC, rendered, class, next cell and time, a heartbeat every
  5 min when idle), `history.csv` one row per cell; a `STOP` file ends it
  cleanly after the run in flight; **busy skip**: if a game session is
  active at a cell's start (the user playing), wait 10 min and retry, up
  to 3 times, then mark the cell `busy` and move on; the cap
  **2026-10-17T06:00:00Z**. Each run's directory under
  `g8_s1_2026-10-16/runs/<cell>/` (the suite's full output: these are
  the envelope's evidence, kept in the repo).
- **Code's steps:** copy and adapt `e4_s4d_watch.py`'s scaffolding for
  this driver; a 2-min `--dry` (one cell with a 30-s window, flags
  written and removed, status line, no stream); the pre-registration
  hashed; launch; wait for the first cell's status line (≤ 15 min; the
  first cell includes the warm-up); `systemctl --user status` into the
  launch record; write `evidence/G8_S1_LAUNCH_2026-10-16.md` and
  `logs/g8_s1_git_status.txt`; **exit**. The record of the envelope
  itself is a later one-line task ("write G8-S1's record from the
  driver's files"), as with E4-S4C.

## 3. The user, meanwhile

The onn must stay on the LAN and idle for the cells to run. If the
off-site test is to start before the cap: `touch ~/privyhub_g8_s1/STOP`,
wait for `status.txt` to say stopped (≤ 12 min), then proceed; the
cells done so far stand.
