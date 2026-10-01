---
memory_schema: 1
as_of: 2026-09-30
status: DECISION 2026-09-28 (the user's gate reading of the pooled C3.L3a table, four pre-registered sessions) — C3.L4 AUTHORIZED, single transition per event; live build pending. Ramps excluded from live adaptation. Not authorized - a ramp; sampling inside the settling window; any live run before a fault-injection night with the user's nft | CLOSED 2026-09-30: C3.L4 live VALIDATED UNDER REAL LOSS on three nft nights (1 NOT, 2 and 3 WORKS UNDER LOSS); the controller as built authorized; live behind PRIVYHUB_ADAPTIVE_BITRATE_MODE=live, off by default; adoption the user's call
---

# C3.L4 — live adaptation authorized, one transition per event

**Status:** Accepted, 2026-09-28. The reading is the user's; this record
writes it down with what it rests on. No code changed for it.

**`C3.L4` classification: AUTHORIZED, single transition per event; live
build pending.** `C3.L3a` is closed by it.

## What it rests on

The pre-registered gate (`../investigations/ACTIVE.md` §C3.L3a): 10
traversals per session, dwell 55-90 s, primary W 5.0 s, ≥ 4 sessions to
≥ 20 per shape, anchored 1-10 picture rating; no threshold encoded — the
judgement is the user's. Pooled by the `C3-L3A-P2R3` rule (v2 state,
pre-registered config only; every skipped file listed).

**The four records.**

1. `../evidence/C3_L3A_R1_SESSION1_2026-09-24.md` — run `20260924_115810`.
2. `../evidence/C3_L3A_R2_SESSION2_2026-09-24.md` — run `20260924_130016`.
3. `../evidence/C3_L3A_R3_SESSION3_2026-09-24.md` — run `20260924_151953`.
4. `../evidence/C3_L3A_R4_SESSION4_2026-09-28.md` — run `20260928_122028`.

**The pooled table** (4 runs pooled, 0 skipped; Phase A 3,157 s; 81 marks;
W 5.0; every cell recomputed from the run files and matching
`c3_l3a_aggregate.json`, `../evidence/c3_l3a_r4_2026-09-28/pool_check.txt`):

| class | marked | marks | chance-expected |
| --- | --- | --- | --- |
| jump | 6 / 20 | 6 | 3.21 |
| ramp | 15 / 20 | 29 | 8.52 |
| decoy, jump-matched | 4 / 40 | 4 | 5.13 |
| decoy, ramp-matched | 13 / 40 | 14 | 16.99 |

**Picture.** 5500 and 5000 acceptable at 7-8 in the two sessions rated as
typed (9/9/9 on the smoke session); 6000 rated 8 once, otherwise
defaulted; sessions 1-2 defaulted by accidental Enter (the user's stated
rating 6-7, levels not distinguished).

**Cost per transition** (`C3.L3a-S1`, n = 60, and sessions 1-4): one
output gap, median 186.5 ms (128-225); 2 of 60 an extra GOP (~410-420 ms),
seen again as session 3's 564 ms restore and session 4's 426 ms park.
Telemetry settles in one to three client reports (≤ ~4 s; pooled max
5.0 s). Lifecycle 0 / 0 / 0 over 80 pooled cycles.

## The reading — the user's, 2026-09-28, verbatim

> A single unannounced encoder restart during play is not reliably noticed
> and the destination levels look fine, so C3.L4 is authorized for one
> restart per adaptation event — the controller goes straight to its
> target level in a single transition, with the existing hold-downs. Three
> restarts four seconds apart (a ramp) are noticed, so the ramp shape is
> excluded from live adaptation; the ladder stays for choosing the target,
> not for stepping through it. Cost per event stays ~190 ms of output gap.

## What it authorizes

- **One encoder restart per adaptation event.** The controller chooses a
  target on the validated ladder (5000 / 5500 / 6000 / 7000) and reaches
  it in **one** `video_only_restart` transition.
- **Minimum spacing between transitions = the existing hold-downs**
  (`../architecture/ADAPTIVE_BITRATE.md` §"The constants": blackout 3
  reports ≥ 6 s after any action; 30 reports / 60 s same direction; 60
  reports / 120 s on reversal; the oscillation guard). Every transition is
  its own event under those timers.
- A live build, as a task of its own, to this constraint.

## What it does **not** authorize

- **A ramp**: no multi-step walk through the ladder within one event, and
  no transitions closer together than the hold-downs allow. The ladder
  chooses the target; it is not stepped through.
- **Sampling telemetry inside the settling window.** After a transition
  the controller is measuring the restart, not the network; the blackout
  stays.
- **Any live run before a fault-injection night with the user's `nft`.**
  That night is the next `C3.L4` task, not this one. Until it, the flag
  stays `off` or `shadow`.
- Anything beyond bitrate: resolution, fps, GOP, FEC and the adopted
  profile's cap, cushion and redundancy are unchanged.
- It does not re-open `C3-L2`: the actuator is still `video_only_restart`;
  this reading is what makes that actuator acceptable for adaptation at
  one restart per event.

## Consequences

- `../architecture/ADAPTIVE_BITRATE.md` gains the constraint in a live-mode
  section, marked as a decision. No code change here.
- `docs/ROADMAP.md` C3: `C3.L3a` complete; `C3.L4` authorized, live build
  pending.
- Next `C3.L4` work: the live build (single transition per event), then its
  fault-injection night with the user's `nft`, then a live run.

## Appended 2026-09-29 — the live increase rule, the user's choice

**The reading.** On 2026-09-28 the user chose the live controller's
increase rule, verbatim: "Your blend, and yes fold in the low-rung
screening" (`../handoffs/QUEUE_2026-09-29.md`). "The blend" is the one
defined in `../handoffs/C3-L4-L2_INCREASE_RULE_AND_NFT_HARNESS_TASK.md`:

- **"clean"** = no ROUTINE-level sample: fps ≥ 57, queue ≤ 1 and output
  gap ≤ 150, on fresh telemetry.
- **The window**: the last 90 evaluated reports since the last SSRC
  change and its 3-report blackout. It starts empty after every change.
- **The step**: one rung up when ≥ 85 of those 90 are clean.
- Everything else in this record is unchanged: one transition per event,
  the hold-downs, the blackout, the oscillation guard, the rate limit.

**Why a rule was needed.** L1's rule was 90 *consecutive* reports at fps
≥ 59, queue 0 and gap ≤ 150, the shadow's constant. It never fired on a
clean link, so a stepped-down session stayed down
(`../evidence/C3_L4_L1_LIVE_CONTROLLER_2026-09-28.md` §5).

**This is the user's decision on the data**, not a loosening by Code. The
shadow keeps its own rule.

**As built and shown** (`../evidence/C3_L4_L2_INCREASE_RULE_2026-09-29.md`):

- On an injected FALLBACK the stream climbed 5000 → 5500 → 6000 → 7000,
  one rung per event. Each step came on a window of 90/85, 90/85 and
  90/86, and 117, 120 and 93 reports after the previous change.
- The stream then stayed at 7000 for 14 min.
- The client's own clean share was 91-96 % by rung.

**Next.** The user's `nft` night with `tools/c3_l4_nft_night.py`.

## Appended 2026-09-29 — the capacity trigger and the recovery-escalation backstop, the user's decision

**The reading.** The user's first `nft` night showed that the live
controller never stepped down under a capacity cap
(`../evidence/C3_L4_NFT_NIGHT1_2026-09-29.md`):

- the cap took fps under 50 within ~6 s;
- ~250 lost video packets per report;
- queue ≥ 1 on 3 of 357 reports;
- recovery restarted the encoder at 7000 nine times in F1.

Cowork proposed two rules. The user answered, verbatim, **"Yes, add
both"** (`../handoffs/QUEUE_2026-09-29B.md`). The rules, as the task
defines them:

- **Capacity trigger** — class FALLBACK, reason `capacity`, target 5000.
  - Over the last 5 fresh evaluated reports: **fps < 50 on all 5 and
    `lost_packets_delta` ≥ 50 on ≥ 3 of 5**. A stale report or a missing
    loss delta does not count.
  - The same blackout, hold-downs, rate limit, oscillation guard and
    guards as every FALLBACK.
- **Recovery-escalation backstop** — class FALLBACK, reason
  `recovery_escalation`, target 5000.
  - When recovery has **restarted the encoder twice at the same level
    within 180 s** (encoder restarts, not pauses), the controller makes
    **one** FALLBACK decision. It comes after recovery is back to
    PLAYING and the 3-report blackout has passed.
  - If the level is 5000, the decision is `at_floor`, logged. All guards,
    hold-downs and the rate limit apply.
  - **Recovery itself is unchanged**: C3-F1 stays level-preserving. The
    controller moves the level; recovery never does.
- **Everything else in this record is unchanged**: one transition per
  event, the blend's increase rule, the blackout, the hold-downs, the
  rate limit, the oscillation guard, the guards and the disable route.
  The shadow is unchanged.

**This is the user's decision on the data**, not a retune by Code.

**As built and checked**
(`../evidence/C3_L4_N1_CAPACITY_TRIGGER_2026-09-29.md`):

- Live only, with 30 new synthetic tests.
- Night 1's samples replayed: a capacity FALLBACK 13.6 s after F1's cap,
  16.7 s after F3's and 19.7 s after K's. Nothing in the baselines, after
  removal, or under F2's 2 % loss.
- Every recorded clean-link series replayed: neither rule fires (the stop
  rule passed).

**Next.** The user's `nft` night 2 (`--only F1,F3`), under
`../evidence/c3_l4_n1_2026-09-29/c3_l4_nft_night2_preregistration.txt`.

## Appended 2026-09-29 (later) — the mild capacity rule, the user's decision

**The reading.** The user's `nft` night 2 scored WORKS UNDER LOSS
(`../evidence/C3_L4_NFT_NIGHT2_2026-09-29.md`). But at 6000 under the cap
the stream sat degraded for 3 min 56 s and nothing fired:

- fps median 55.8, under 50 on 17 %;
- ~60 lost per report;
- no queue.

The strict capacity bar needs fps < 50 on all 5, and ROUTINE needs
queued frames. Cowork proposed a milder form. The user answered,
verbatim, **"Go"** (`../handoffs/C3-L4-N2_NFT_NIGHT2_SCORE_AND_MILD_CAPACITY_TASK.md`).

**The rule — `capacity_mild`**, class ROUTINE, one rung down (7000 →
6000, 6000 → 5500, 5500 → 5000; `at_floor` at 5000):

- The bar: over the last 5 fresh evaluated reports, **fps < 57 on ≥ 4 of
  5 and `lost_packets_delta` ≥ 50 on ≥ 3 of 5**.
- The strict capacity FALLBACK keeps precedence.
- ROUTINE's blackout, hold-downs (60), rate limit, oscillation guard and
  guards all apply.
- A stale report or a missing delta does not count.
- **Everything else in this record is unchanged. The shadow is
  unchanged.**

**This is the user's decision on the data**, not a retune by Code.

**As built** (`../evidence/C3_L4_N2_MILD_CAPACITY_2026-09-29.md`):

- On night 2's own samples the bar is met 46 s into the 6000 rung. The
  rule acts at 119 s, after the 60-report reversal hold-down that follows
  the increase.
- On night 1 the strict FALLBACK still fires first (13.6-19.7 s). The
  mild bar is met at ~10 s but waits for FALLBACK.
- It does not fire on any adopted clean-link series.

**Next.** The user's `nft` night 3 (`--only F1`), under
`../evidence/c3_l4_n2_2026-09-29/c3_l4_nft_night3_preregistration.txt`.

**One open point for the user.** The handoff expected the mild step
"within 90 s of arriving at 6000". The ROUTINE reversal hold-down makes
that ~120 s. Night 3 is pre-registered to the hold-down's bound. Shorter
needs a rule change, which is the user's call.

## Appended 2026-09-30 — C3.L4 CLOSED: live validated under real loss on three `nft` nights

**The close.** `C3.L4` live is **VALIDATED UNDER REAL LOSS** on the
user's three `nft` nights:

- **Night 1** (2026-09-29, all four parts): NOT "WORKS UNDER LOSS". There
  was no decrease under a capacity cap, and it led to the capacity trigger
  and the recovery-escalation backstop
  (`../evidence/C3_L4_NFT_NIGHT1_2026-09-29.md`).
- **Night 2** (2026-09-29, `--only F1,F3`): WORKS UNDER LOSS (F1, F3). 6000
  sat degraded under the cap below every bar, and it led to
  `capacity_mild` (`../evidence/C3_L4_NFT_NIGHT2_2026-09-29.md`).
- **Night 3** (2026-09-30, `--only F1`): WORKS UNDER LOSS (F1), with the
  pre-registered shape: capacity at +15.5 s, the climb to 6000, the mild
  step back at 121 s, then HOLD `oscillation` at 5500
  (`../evidence/C3_L4_NFT_NIGHT3_2026-09-30.md`).

**What is authorized is the controller as built:**

- **the triggers:**
  - the queue/gap FALLBACK;
  - the strict capacity FALLBACK;
  - the recovery-escalation backstop;
  - `capacity_mild` (ROUTINE, one rung down);
  - the queue ROUTINE (→ 6000);
- **the user's blend increase;**
- **the controls:** the 3-report blackout, the hold-downs, the oscillation
  guard, the 4 / 10 min rate limit, and the guards (recovery PLAYING, age
  ≥ 60 s, reference profile, no override);
- **one transition per event**, through the validated actuator;
- **recovery unchanged** (`C3-F1`, level-preserving), and **the shadow
  byte-identical**.

The rules are tabled in `../architecture/ADAPTIVE_BITRATE.md` ("C3.L4 —
the controller as closed").

**Live stays behind `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`, off by
default.** Making it the default is an adoption and the user's call; it
is not made here.

**The change that would make it the default.**

- **Where the mode is read.** `adaptive_bitrate_live.get_controller()`
  reads `PRIVYHUB_ADAPTIVE_BITRATE_MODE` once, at the companion's first
  use (`mode_from_env`). Unset, it is off.
- **The persistent change.** A systemd drop-in for the user unit,
  `~/.config/systemd/user/privyhub-companion.service.d/adaptive.conf`,
  containing `[Service]` and `Environment=PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`.
  Then `systemctl --user daemon-reload && systemctl --user restart
  privyhub-companion`.
  - The unit file itself stays as H3 wrote it ("no PRIVYHUB_* diagnostic
    variable is ever set here").
  - The `set-environment` used on the test nights does not survive a
    reboot, so it is not the adoption.
- **What would show.**
  - `native-stream-status` → `adaptive_bitrate.mode live`,
    `configured_mode live`, `acts true`.
  - `encoder_overrides.any_override` stays **false**: it is about the
    encoder only, and the adaptive mode is not an encoder override.
  - The companion's environ carries the one `PRIVYHUB_ADAPTIVE_BITRATE_MODE`.
    The harnesses' "no PRIVYHUB_*" preflights would then need that one
    name allowed.
- **Turning it back off.**
  - Delete the drop-in, then `daemon-reload` and restart: mode off.
  - For one session, at runtime,
    `POST /plugins/games/adaptive-bitrate/disable` switches to shadow;
    the next session is live again.

**One open point, left open.** The mild step's delay after an increase is
bounded by the 60-report ROUTINE reversal hold-down (~120 s; night 3: 121
s). It is not the ~90 s once expected. Shortening it is a rule change for
the user to ask for, or not.

## Appended 2026-10-01 — made the default (`C3-L4-D1`)

The user authorized it on 2026-09-30 ("do the loss row look first and
then the live default"). The drop-in above was written on 2026-10-01 at
13:07Z, exactly as described. Live is the default from then on.

- Record: `C3-L4_LIVE_DEFAULT_2026-10-01.md`.
- Evidence: `../evidence/C3_L4_D1_LIVE_DEFAULT_2026-10-01.md`.
