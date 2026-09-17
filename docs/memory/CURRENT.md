---
memory_schema: 2
state_updated: 2026-09-17
active_work_item: D-135
maintenance_status: healthy
baseline_commit: 634bc0affc17f9f4317df896a0068c61f8f2afc3
---

# Current Project State

## Active Objective

Finish bounded D5 TV/EPG performance and regression closeout without reopening
validated media, TV-state authority, Games, or transport behavior.

## Current Work Item

**D-135 — isolate serialized TV-state synchronization from navigation work.**

D-134's classifier printed `D134_FAVORITES_UI_RENDER_DOMINANT`, but the raw
measurements contradict that conclusion. Total Favorites latency was 24,382 ms,
while the named measured stages sum to only 1,530 ms. The 22,852 ms residual is
outside those stages.

Source inspection explains the residual: the D-134 `page_begin` marker is emitted
before submitting to the single-thread `networkExecutor`, while D-131 leaves the
~24-second Linux TV-state pull running on that same executor after TV home becomes
visible. Favorites therefore waits in the executor queue before its measured
count/query stages begin.

## Verified State

- Live TV guide presentation through D-133: **runtime validated**.
- D-131 fast top-level TV render with eventual Linux-authority reconciliation:
  **runtime validated**.
- D-134 raw evidence: total 24,382 ms; count 26; query 0; prefetch 181;
  rejected-prefetch 2; hydrate 477; UI render 844; named sum 1,530; residual
  22,852 ms.
- D-134 classifier label is **not authoritative** because it ignored the dominant
  unmeasured pre-executor queue interval.

## Current Repository / Patch State

Expected D-135 predecessor:

`634bc0affc17f9f4317df896a0068c61f8f2afc3`

D-135 adds a dedicated single-thread `tvStateSyncExecutor`, routes all TV-state
push/pull operations through it, and releases the general `networkExecutor`
immediately after TV-home catalog/prefetch work. Linux authority operations remain
serialized; navigation/page work no longer queues behind the long state pull.

**Status: DEVELOPMENT PATCH / RUNTIME VALIDATION NEXT.**

## Next Action

1. install/build/push/APK-install D-135;
2. prepare the D-135 probe;
3. from the top-level app, open TV and then Favorites promptly;
4. verify that Favorites queue wait and total load collapse while the Linux
   state pull still completes and reconciles.

Target:

`D135_FAVORITES_QUEUE_CONTENTION_REMOVED`

## Success Criteria

- Favorites executor queue wait <= 1,500 ms;
- Favorites total load <= 5,000 ms in the representative cached case;
- Linux TV-state sync still completes and reconciles;
- TV-state pushes and pulls remain serialized on one dedicated executor;
- D-129/D-133 guide layout/status behavior remains unchanged;
- no network address or device identifier is written to the probe report.

## Do Not Reopen Without New Evidence

- D5.4 Linux-authoritative TV-state semantics.
- D-125/D-126 EPG background behavior.
- D-127 incorrect-guide state.
- D-129 guide geometry.
- D-131 first-render scheduling.
- D-132 coverage classes.
- D-133 status distinction.
- External VOD architecture.
- Linux Games lifecycle.
- Deferred UDP work.

## Relevant References

- `evidence/D134_FAVORITES_LOAD_RUNTIME_EVIDENCE_2026-09-17.md`
- `investigations/D134_FAVORITES_LOAD_LATENCY.md`
- `investigations/D135_TV_STATE_EXECUTOR_ISOLATION.md`
- `architecture/TV_STATE_SYNC.md`
- `patches/D-135_TV_STATE_EXECUTOR_ISOLATION.md`
- `roadmap/STATUS.md`
- `2026-09-17.md`
