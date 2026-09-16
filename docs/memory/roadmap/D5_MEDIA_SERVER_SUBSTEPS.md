---
memory_schema: 1
as_of: 2026-09-16
baseline_commit: 53fd9b176647bad324a9fdae4d4f04b2f62e43a4
---

# D5 Media / Server Restoration Substeps

<!-- PRIVYHUB_D103_D5_EPG_INGESTION_PROBE:D5_SUBSTEPS:BEGIN -->
## D5.2 execution checkpoint — D-103

D5.2 moved from planned diagnostic to **probe ready / runtime evidence next**.

The probe is intentionally read-only and must classify the first divergence
among upstream guide shape, Android-equivalent mapping acceptance, catalog-ID
intersection, onn cached mapping state, XML source fetch/format, and exact
programme identity/window matching.

D5.3 remains blocked until that evidence exists.
<!-- PRIVYHUB_D103_D5_EPG_INGESTION_PROBE:D5_SUBSTEPS:END -->


This file is the detailed D5 execution order. `docs/memory/roadmap/STATUS.md`
remains the compact current roadmap view.

## D5.1 — Live TV catalog/playback acceptance

**Status: COMPLETE / runtime validated**

Accept current onn TV catalog/categories/navigation and normal playback.
EPG is a separate acceptance boundary.

## D5.2 — EPG ingestion diagnostic

**Status: ACTIVE / NEXT**

One hypothesis, one diagnostic probe. Measure the existing pipeline from
upstream guide data through mapping and XMLTV programme matching. Retain raw
counts/rejection reasons. No production EPG patch before the first divergent
boundary is evidenced.

## D5.3 — Existing EPG path repair and acceptance

**Status: PENDING**

Repair only the first evidenced failure. Validate representative mapped channels
show current/upcoming programmes, refresh works, cached data works, and channels
without guide data still play normally.

## D5.4 — TV state ownership/sync contract

**Status: PENDING**

Formalize Linux durable authority for TV user intent, onn local cache semantics,
schema/revision rules, conflict/failure behavior, and the boundary between user
state, derived cache and runtime observations.

## D5.5 — Linux durable TV state store/API

**Status: PENDING**

Implement atomic/versioned companion persistence and bounded API surface. Do not
make Linux startup depend on a client.

## D5.6 — onn <-> Linux synchronization

**Status: PENDING**

Reuse/version the Android TV serialized export/import state. Do not copy SQLite
DB files. Local onn state remains available during temporary sync failure.

## D5.7 — TV synchronization runtime acceptance

**Status: PENDING**

Prove existing state imports to Linux, onn changes reach Linux, restart
persistence, fresh-client restore, temporary sync failure survival, and
post-recovery convergence.

## D5.8 — Integrated media/diagnostics regression

**Status: PENDING**

Bounded smoke/regression pass:
- already-validated VOD path;
- Live TV categories/search/favorites/playback;
- EPG current/upcoming/cache/refresh/no-guide fallback;
- TV sync;
- TV Diagnostics and Catalog / EPG Status;
- main diagnostics/Self-Test and relevant support-bundle behavior.

Do not repeat the full VOD hotplug campaign unless fresh regression evidence
requires it.

## D5.9 — D5 checkpoint

**Status: PENDING**

Record runtime evidence, update durable memory, create clean checkpoint and move
to D7/D8.

## Explicitly deferred from D5

- legacy browser/camera Linux runner ports;
- full canonical TV channel-model rebuild;
- broad duplicate-reconciliation redesign;
- sophisticated fuzzy EPG matching;
- major guide-grid/timeline UX;
- centralized multi-client stream-health aggregation;
- broader TV UX polish.

Browser/app and camera/live generalized native sources remain C6 after D7/D8.
