---
memory_schema: 1
as_of: 2026-09-16
baseline_commit: 53fd9b176647bad324a9fdae4d4f04b2f62e43a4
---

# TV State Synchronization Architecture

<!-- PRIVYHUB_D115_TV_STATE_AUTHORITY:TV_STATE_SYNC:BEGIN -->
## D-115 concrete authority contract

Linux persistence:
`data/tv_state/state.json`

Schemas:
- `privyhub_tv_state_status_v1`
- `privyhub_tv_state_envelope_v1`
- `privyhub_tv_state_update_v1`
- `privyhub_tv_user_state_v1`

State contains preferences, provider intent, favorites/manual-hidden, channel
overrides, group/order, and protect-auto-hide.

State does not contain runtime health/recency, catalog, or EPG data.

Concurrency:
- Linux revision starts at 0 when uninitialized;
- first successful write creates revision 1;
- every changed write increments revision;
- identical writes keep the revision;
- stale `base_revision` returns current authority without mutation.

Persistence is atomic temp-file + fsync + replace + read-back/hash validation.

The plugin does not retain client network addresses.

Android migration must seed Linux from current local durable state when the
authority is uninitialized. A fresh Linux default must never erase existing onn
user intent.
<!-- PRIVYHUB_D115_TV_STATE_AUTHORITY:TV_STATE_SYNC:END -->

<!-- PRIVYHUB_D114_STREAM_IDENTITY_POLICY:TV_STATE_SYNC:BEGIN -->
## D5.4 activation after D-113

D5.4 is now active.

D-113 reinforces why `manual_hidden` belongs in durable user intent:
users need a persistent way to suppress a third-party source they have confirmed
is semantically wrong even when transport health remains good.

The initial Linux-authoritative sync contract should therefore preserve:
- provider configuration/enabled state;
- favorites;
- favorite groups/order;
- manual hidden state;
- custom channel profile overrides;
- auto-hide protection;
- language/country.

Do not synchronize semantic-identity heuristics as if they were user intent.

Do not synchronize raw SQLite files.

Initial conflict model remains one-client-oriented with a Linux-assigned
monotonic server revision. More complex multi-client runtime-health merging is
deferred.
<!-- PRIVYHUB_D114_STREAM_IDENTITY_POLICY:TV_STATE_SYNC:END -->

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
