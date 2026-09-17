---
memory_schema: 1
as_of: 2026-09-16
baseline_commit: 53fd9b176647bad324a9fdae4d4f04b2f62e43a4
---

# D-102 — D5 Live TV acceptance and Linux TV-state ownership

<!-- PRIVYHUB_D114_STREAM_IDENTITY_POLICY:D102_RUNTIME_UPDATE:BEGIN -->
## Runtime update through D-114

The older EPG-not-accepted status in this decision is superseded by later D5.3
runtime evidence.

Current authoritative state:
- Linux local EPG acquisition/cache runtime validated;
- Android companion-backed EPG consumption runtime validated;
- Program Guide renders real schedule data;
- D5.3 EPG data flow accepted;
- third-party stream semantic identity remains a separate quality dimension.

D-113 found one confirmed upstream/source identity defect and a small/noisy set
of feed-name heuristic hits. D-114 explicitly declines a generic automatic
identity-suppression rule.

The original Linux-authoritative TV-state ownership decision remains unchanged.

D5.4 implementation is now active, including `manual_hidden` as durable user
intent.
<!-- PRIVYHUB_D114_STREAM_IDENTITY_POLICY:D102_RUNTIME_UPDATE:END -->

**Status:** Accepted architecture decision; implementation/runtime sync
validation pending (2026-09-16)

## Runtime evidence

Fresh onn `Catalog / EPG Status`:
- English / All Countries;
- 3356 streams;
- 22 favorites;
- 49 reliable;
- 4 hidden;
- 3 enabled providers;
- catalog refreshed 2026-09-16 15:55:38 local;
- 2 EPG mappings;
- 0 cached programmes.

Normal Live TV categories/navigation and channel playback work. Program Guide
exists and runs, but no tested channel currently has actual schedule data.

Therefore:
- D5.1 Live TV catalog/categories/playback is runtime accepted.
- EPG data is not accepted.

## Decision

Linux becomes the durable authority for TV user state. The onn keeps a local
cache for responsive operation and temporary sync-outage tolerance.

Durable user intent includes, where supported by the existing Android model:
- managed/custom provider configuration and enabled state;
- favorites;
- favorite groups and ordering;
- manual hidden state;
- custom channel profile overrides;
- auto-hide protection;
- selected language/country preferences.

Use a versioned serialized synchronization contract derived from the existing
Android TV export/import representation. Do not copy `privyhub_tv.db` or
`privyhub_epg.db` between devices.

Downloaded channel catalogs, provider-derived channel metadata, EPG mappings and
programme listings are derived/cacheable data.

Runtime observations such as last watched and stream-health counters require
explicit merge semantics before becoming generalized multi-client authority.

## Failure semantics

- Temporary Linux/sync unavailability must not make the onn TV UI unusable.
- User actions must not be silently discarded.
- When Linux returns, state must converge through the versioned contract.
- A fresh/replaced onn must be able to recover durable household TV user state.
- Linux startup must not depend on the onn being online.

## D5 boundary

D5 restores the existing EPG path and establishes/validates durable TV user-state
synchronization. Full canonical channel-model redesign, broad duplicate
reconciliation, sophisticated fuzzy EPG matching, major guide-grid UX and
centralized multi-client runtime-health aggregation remain later media/TV work.

## Immediate next step

D5.2: instrument the existing EPG pipeline stage-by-stage before changing
production matching/parser behavior.
