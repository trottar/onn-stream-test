---
memory_schema: 2
state_updated: 2026-09-17
active_work_item: D7
maintenance_status: healthy
baseline_commit: 663d2e4484afb7d88980aefb691f0b45a0ae6358
---

# Current Project State

## Active Objective

Begin D7 native Linux regression from the closed D5 media/server baseline,
without reopening validated D5 subsystems absent new evidence.

## Current Work Item

**D7 — Native Linux regression.**

D5 media/server restoration is **COMPLETE / RUNTIME VALIDATED**.

Final closure evidence:
- D-136 focused automated TV/media regression validated after D-137 repaired the
  stale schema-v2 diagnostic projection;
- D-122 automated TV/media baseline validated;
- D-133 guide layout/status validated;
- D-135 Favorites executor isolation/state reconciliation validated;
- final manual onn smoke passed for Live TV playback, Favorites/guide navigation,
  and VOD playback.

D6 UDP replay remains deferred unless new evidence requires reopening it.

## Verified State

- External/removable VOD: **runtime validated**.
- Live TV catalog/categories/playback: **runtime validated**.
- Linux EPG + Android guide cache/UI: **runtime validated**.
- Linux-authoritative TV durable state: **runtime validated**.
- Incorrect-guide durable intent: **runtime validated**.
- One-column guide/status presentation: **runtime validated**.
- TV/Favorites responsiveness with serialized state authority: **runtime validated**.
- Focused automated TV/media regression: **validated**.
- Final manual Live TV / guide / VOD smoke: **passed**.
- D5 media/server restoration: **CLOSED / COMPLETE**.

## Current Repository / Patch State

D-139 is the D5 closeout/checkpoint memory update.

No production source, APK, companion runtime, database, playback, network, or
state-sync behavior changes are part of D-139.

**Status: D5 CLOSED / D7 NEXT.**

## Next Action

Start D7 with the minimum native Linux normal-use regression from
`docs/ROADMAP.md`:

1. server boot/start;
2. client discovery/control;
3. media;
4. Games launch;
5. video/audio/controller;
6. pause/resume;
7. Save/Load;
8. profiles/cheats/mod state;
9. End/teardown;
10. restart/recovery.

Reuse existing accepted evidence and probes wherever possible.

## Success Criteria

- D7 covers the minimum normal-use Linux regression set;
- validated D5 TV/media behavior remains stable;
- validated D4 Games behavior remains stable;
- any regression is isolated with the normal one-hypothesis/one-probe workflow;
- D8 can then record the Linux baseline checkpoint.

## Do Not Reopen Without New Evidence

- D5 external VOD storage architecture.
- D5 Live TV/EPG acquisition/cache/presentation.
- D5.4 Linux-authoritative TV-state contract.
- D-127 incorrect-guide state.
- D-131/D-135 executor scheduling.
- D-137 diagnostic projection repair.
- D6 UDP replay remains deferred.
- Resolved Linux Games controller/multitap/video/audio lifecycle work.

## Relevant References

- `evidence/D5_TV_MEDIA_CLOSEOUT_2026-09-17.md`
- `evidence/D136_FOCUSED_TV_MEDIA_AUTOMATED_ACCEPTANCE_2026-09-17.md`
- `roadmap/D5_MEDIA_SERVER_SUBSTEPS.md`
- `roadmap/STATUS.md`
- `../../ROADMAP.md`
- `2026-09-17.md`
