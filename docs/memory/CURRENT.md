---
memory_schema: 2
state_updated: 2026-09-17
active_work_item: D-127
maintenance_status: healthy
baseline_commit: c01bb79ddbf6763a48ce9487ee31cdb8aef9aef6
---

# Current Project State

## Active Objective

Finish the bounded D5 TV/EPG usability work without reopening validated media,
TV-state, Games, or transport subsystems.

## Current Work Item

**D-127 — durable `Mark Guide Incorrect` intent and deferred recheck policy.**

D-127 development patch is installed when this file is present. Runtime
validation is still required before D-127 is accepted.

The user can mark a guide incorrect without hiding or disabling its channel. The
mark is Linux-authoritative durable intent, the rejected guide source is
fingerprinted, marked guide data is not presented as trusted, and background
recheck remains separate from user acceptance.

## Verified State

- D5 external/removable VOD: **COMPLETE / runtime validated**.
- D5 Live TV catalog/categories/playback: **runtime validated**.
- Linux EPG acquisition plus Android EPG consumption/cache: **runtime validated**.
- D5.4 Linux-authoritative durable TV-state sync: **COMPLETE / runtime validated**.
- D-125 non-blocking EPG miss handling: **runtime validated**.
- D-126 Favorites/visible-page prefetch: **runtime validated**.
- D-127 source/design pre-state was audited against synchronized checkpoint
  `c01bb79ddbf6763a48ce9487ee31cdb8aef9aef6`.
- D-127 intentionally does not change playback health, Hide, Favorites, stream
  transport, Linux EPG acquisition algorithms, or guide-grid/category layout.

## Current Repository / Patch State

Predecessor synchronized checkpoint:

`c01bb79ddbf6763a48ce9487ee31cdb8aef9aef6`

D-127 development implementation changes:

- Android TV DB schema 3 with `guide_incorrect`, rejected-source fingerprint and
  mark timestamp;
- durable TV user-state schema v2 with v1 migration support;
- Linux authority v1 -> v2 migration preserving server revision;
- Android guide-source fingerprints plus delayed rejected-guide prefetch;
- explicit Mark / Retry / Accept / Clear UI behavior;
- diagnostic probe `tools/probes/d127_incorrect_guide_probe.py`.

**Status: DEVELOPMENT PATCH / RUNTIME VALIDATION NEXT.**

## Blockers

None known before runtime validation.

## Next Action

Runtime-validate D-127 through the normal onn path using a visible/playable
channel with a known incorrect guide:

1. mark the guide incorrect;
2. confirm the channel remains visible and playable while current-program/guide
   presentation is suppressed;
3. reopen TV after app/companion restart and confirm the mark survives Linux
   authority synchronization;
4. run `python3 tools/probes/d127_incorrect_guide_probe.py` and inspect
   `logs/tv/d127_incorrect_guide_probe.txt`;
5. exercise Retry and confirm an unchanged rejected source is not silently
   trusted; then explicitly Accept or Clear and confirm normal guide display can
   be restored deliberately.

## Success Criteria

- Channel remains visible and playable after `Mark Guide Incorrect`.
- Known rejected guide is not presented as trusted/current.
- Mark survives restart and Linux-authoritative TV-state synchronization.
- Rejected source fingerprint is nonblank and synchronized.
- Later background recheck does not silently clear user intent.
- Explicit Retry/Accept or Clear can restore guide trust deliberately.
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

- `investigations/D127_INCORRECT_GUIDE_INTENT.md`
- `architecture/TV_STATE_SYNC.md`
- `architecture/TV_MEDIA.md`
- `evidence/D125_EPG_BACKGROUND_WARMER_RUNTIME_ACCEPTANCE_2026-09-17.md`
- `evidence/D126_ANDROID_EPG_PREFETCH_RUNTIME_ACCEPTANCE_2026-09-17.md`
- `roadmap/STATUS.md`
- `2026-09-17.md`
- `MAINTENANCE.md`
