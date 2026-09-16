---
memory_schema: 1
as_of: 2026-09-16
baseline_commit: 53fd9b176647bad324a9fdae4d4f04b2f62e43a4
---

# TV State Synchronization Architecture

## Current split

The mature TV catalog/user-state implementation is currently onn-local. Android
owns `privyhub_tv.db` and `privyhub_epg.db`; the companion also retains an older
lightweight IPTV-org plugin. D5 must not treat those as equivalent authorities.

## Target authority

Linux companion:
- durable household TV user state;
- future shared client synchronization authority.

onn/client:
- local TV cache;
- playback/UI;
- locally available operation during temporary sync failure.

## State classes

### Durable user intent

Linux-authoritative target:
- providers and enabled state;
- favorites;
- favorite groups/order;
- manual hidden state;
- custom channel profile overrides;
- auto-hide protection;
- language/country preferences.

### Derived/cacheable data

Rebuildable:
- provider channel catalog;
- categories/provider metadata;
- EPG mappings;
- programme listings.

### Runtime observations

Requires explicit merge semantics:
- last watched / recent viewing;
- success/failure counters;
- consecutive failures;
- auto-hidden state derived from runtime health.

Do not blindly last-writer-wins these counters across multiple clients.

## Synchronization boundary

Start from the existing Android versioned export/import representation. Extend
it only where required by the D5 contract.

Do not synchronize SQLite database files.

Use an explicit schema version and server revision. Linux assigns the durable
revision. Sync failure must be visible/diagnosable but must not discard local
user actions or make cached TV browsing unusable.

## Later evolution

Moving catalog/EPG acquisition fully to Linux may reduce client refresh latency
and centralize provider work, but that broader consolidation is not required to
establish D5 user-state durability.
