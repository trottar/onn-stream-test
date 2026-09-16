---
memory_schema: 1
as_of: 2026-09-16
status: runtime_validated
classification: D4_FINAL_GAMES_REGRESSION_CONFIRMED_WITH_NO_FIXTURE_SKIPS
---

# D4 final Linux Games acceptance — 2026-09-16

## Checkpoint

Regression ran against Git checkpoint:

`5bb2d68e2f9b6b3e300a484471eff57eef96d0c5`

## First-run preserved evidence

The first guided run completed these stages before a probe-side read-only API
exception at the cheat stage:

- library/search/art normal;
- NES library count 0 -> `SKIPPED_NO_LOCAL_FIXTURE`;
- SNES library count 44;
- Donkey Kong Country (USA) launched normally;
- SNES active/fresh-log/Linux-P1 check true;
- P1-P4 configured ports 1-4;
- P1-P4 Linux virtual pads present;
- SNES video/audio/input normal;
- SNES analog-to-D-pad convenience normal;
- SNES End inactive and uinput pads removed;
- Genesis library count 0 -> `SKIPPED_NO_LOCAL_FIXTURE`;
- Crash Bandicoot (USA) PS1 lifecycle active/fresh-log/Linux-P1 check true;
- P1-P4 configured ports 1-4;
- P1-P4 Linux virtual pads present;
- PS1 video/audio/controller normal;
- frozen preview + paused controls normal;
- Save/Load normal;
- resume normal;
- PS1 End inactive and uinput pads removed.

The interruption was a probe robustness issue, not evidence of a Games failure.

## R1 continuation

R1 verified the prior required evidence with zero gaps and resumed at the
unfinished stages.

Passed:
- cheat session active;
- cheat session-config marker present;
- cheat effect/gameplay normal;
- cheat End/cleanup;
- IPS mod session active;
- IPS launch markers present;
- visible mod/gameplay normal;
- mod End/cleanup;
- named A8 input-profile session active;
- named-profile marker present;
- configured custom mapping normal;
- input-profile End/cleanup;
- fresh post-regression launch active;
- fresh launch video/audio/controller normal;
- recovery End/cleanup;
- `git diff --check` clean.

No status-read retries were needed in R1.

## Existing evidence reused

D-088 already runtime validated PS1 Port-1 multitap:
- Players 3/4 available;
- four remotes independently routed.

## Coverage interpretation

D4 acceptance is coverage-aware.

Runtime exercised:
- SNES;
- PS1.

Not runtime exercised because no local fixtures existed:
- NES;
- Genesis.

Do not convert no-fixture skips into runtime-validation claims.

## Final classification

`D4_FINAL_GAMES_REGRESSION_CONFIRMED_WITH_NO_FIXTURE_SKIPS`

D4 is accepted. Phase D proceeds to D5 media/server restoration.
