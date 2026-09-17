---
memory_schema: 2
state_updated: 2026-09-17
active_work_item: D-127
maintenance_status: healthy
baseline_commit: 0206017cfd8f0fc57decb7a5e9e8632e6a4f6cdd
---

# Current Project State

## Active Objective

Finish the bounded D5 TV/EPG usability work without reopening validated media,
TV-state, Games, or transport subsystems.

## Current Work Item

**D-127 — durable `Mark Guide Incorrect` intent and deferred recheck policy.**

The user should be able to mark a guide as incorrect without hiding the channel.
The bad guide must stop being presented as trusted, survive restart/sync as
durable user intent, and become eligible for a later controlled recheck.

## Verified State

- D5 external/removable VOD: **COMPLETE / runtime validated**.
- D5 Live TV catalog/categories/playback: **runtime validated**.
- Linux EPG acquisition plus Android EPG consumption/cache: **runtime validated**.
- D5.4 Linux-authoritative durable TV-state sync: **COMPLETE / runtime validated**.
- D-125 non-blocking EPG miss handling: **runtime validated**.
  - measured uncached interactive request: 14.199 ms;
  - slow acquisition continued in the Linux background and cached 7 programmes.
- D-126 Android Favorites/visible-page prefetch: **runtime validated**.
  - 21 favorite channel identities requested;
  - 21 queued;
  - Favorites loaded immediately.
- The first top-level TV entry still spends a few seconds on `Loading TV
  catalog...`; this is separate from D-125/D-126 EPG blocking and is not the
  current work item.
- `EPG mappings` is the legacy/fallback mapping-table count, not total companion
  guide coverage.
- Playback health and semantic channel identity are separate. The confirmed
  10 Bold mismatch remains the motivating example for explicit incorrect-guide
  user intent.

## Current Repository / Patch State

GitHub checkpoint after D-126:

`0206017cfd8f0fc57decb7a5e9e8632e6a4f6cdd`

D-126 APK/runtime validation is complete. No D-127 production patch is installed
yet.

## Blockers

None known.

## Next Action

Inspect the current TV-state durable schema and EPG cache/mapping ownership, then
implement one coherent D-127 change that:

1. adds durable incorrect-guide user intent distinct from Hide;
2. suppresses presentation of a guide explicitly marked incorrect;
3. records enough identity to avoid immediately trusting the same rejected guide;
4. permits deferred/background recheck on a later refresh cycle;
5. provides a user action to retry/clear the incorrect-guide mark;
6. never changes channel visibility/playability solely because the guide is
   incorrect.

Do not combine D-127 with the guide-grid/category redesign.

## Success Criteria

- Channel remains visible and playable after `Mark Guide Incorrect`.
- Known rejected guide is not presented as trusted/current.
- Mark survives restart and Linux-authoritative TV-state synchronization.
- Later retry/recheck can clear or replace the rejected guide deliberately.
- Existing Favorites, Hide, playback, EPG background warming, and TV-state sync
  regressions remain clean.

## Do Not Reopen Without New Evidence

- D5.4 TV-state seed/push/pull/conflict contract.
- D-125 non-blocking Linux EPG request boundary.
- D-126 Favorites/visible-page prefetch seam.
- External VOD hotplug/storage architecture.
- Linux Games controller/multitap/video/audio lifecycle.
- Deferred Opal/Siflower UDP reverse-engineering branch.
- ADB recovery unless ADB actually becomes a blocker.

## Relevant References

- `evidence/D125_EPG_BACKGROUND_WARMER_RUNTIME_ACCEPTANCE_2026-09-17.md`
- `evidence/D126_ANDROID_EPG_PREFETCH_RUNTIME_ACCEPTANCE_2026-09-17.md`
- `investigations/D126_ANDROID_EPG_PREFETCH_INTEGRATION.md`
- `architecture/TV_MEDIA.md`
- `roadmap/STATUS.md`
- `2026-09-17.md`
- `MAINTENANCE.md`
