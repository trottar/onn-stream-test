---
memory_schema: 2
state_updated: 2026-09-17
active_work_item: D-134
maintenance_status: healthy
baseline_commit: 6866ee1a2b9e6dab7e0490796a7d6de74860788a
---

# Current Project State

## Active Objective

Finish the bounded D5 TV/EPG work without reopening validated media, TV-state,
Games, or transport subsystems.

## Current Work Item

**D-134 — Favorites load latency stage probe.**

D-133 is runtime accepted with `D133_EPG_STATUS_ACCURACY_RUNTIME_VALIDATED`.
The guide presentation is correct. The user reports opening Favorites can still
take more than 15 seconds. D-134 instruments the existing page-load path only.

## Verified State

- D5 external/removable VOD: **runtime validated**.
- Live TV catalog/categories/playback: **runtime validated**.
- Linux EPG plus Android guide cache: **runtime validated**.
- D5.4 Linux-authoritative TV state: **runtime validated**.
- D-125 non-blocking EPG miss handling: **runtime validated**.
- D-126 Favorites prefetch: **runtime validated**.
- D-127 incorrect-guide durable intent: **runtime validated**.
- D-129 single-column guide: **runtime validated**.
- D-131 non-blocking TV entry: **runtime validated**.
- D-132 coverage classification: **runtime measured / closed**.
- D-133 EPG status accuracy: **runtime validated**.

## Current Repository / Patch State

Expected D-134 predecessor:

`6866ee1a2b9e6dab7e0490796a7d6de74860788a`

D-134 adds monotonic timing around the existing `openTvPage()` count, query,
prefetch, rejected-guide prefetch, synchronous companion hydration, and UI-render
stages. It does not reorder or alter those calls.

**Status: DIAGNOSTIC INSTRUMENTATION / RUNTIME MEASUREMENT NEXT.**

## Next Action

1. install/build/push/APK-install D-134;
2. prepare the probe;
3. open TV -> Favorites once;
4. verify the probe;
5. target only the measured dominant stage.

## Success Criteria

- all existing Favorites stages have raw elapsed measurements;
- the dominant stage is classified;
- page behavior and guide semantics remain unchanged;
- no network address or device identifier is written to the report.

## Do Not Reopen Without New Evidence

- D5.4 TV-state authority semantics.
- D-125 Linux EPG non-blocking boundary.
- D-126 prefetch semantics.
- D-127 incorrect-guide state.
- D-129 guide geometry.
- D-131 top-level TV-entry scheduling.
- D-132 coverage classes.
- D-133 status distinction.
- External VOD architecture.
- Linux Games lifecycle.
- Deferred UDP work.

## Relevant References

- `evidence/D133_EPG_STATUS_ACCURACY_RUNTIME_ACCEPTANCE_2026-09-17.md`
- `investigations/D134_FAVORITES_LOAD_LATENCY.md`
- `patches/D-134_FAVORITES_LOAD_LATENCY_PROBE.md`
- `roadmap/STATUS.md`
- `2026-09-17.md`
