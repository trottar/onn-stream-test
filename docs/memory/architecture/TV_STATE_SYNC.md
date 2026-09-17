---
memory_schema: 1
as_of: 2026-09-16
baseline_commit: 53fd9b176647bad324a9fdae4d4f04b2f62e43a4
---

# TV State Synchronization Architecture

<!-- PRIVYHUB_D120_SYNC_DIAGNOSTICS:ARCH:BEGIN -->
## Local sync diagnostics

D-120 adds onn-local observability metadata alongside the existing remembered
server revision.

These fields are operational diagnostics, not household durable user intent:
- last success timestamp/action/revision;
- last conflict timestamp/base/server revision.

They are never included in `privyhub_tv_user_state_v1`.

The normal top-level TV-entry trigger is runtime validated by D-119.

Conflict semantics remain:
- stale write is rejected by Linux;
- local TV remains usable;
- no silent overwrite;
- no automatic merge in D5.4.
<!-- PRIVYHUB_D120_SYNC_DIAGNOSTICS:ARCH:END -->

<!-- PRIVYHUB_D118_PULL_ACCEPTANCE:ARCH:BEGIN -->
## Bidirectional runtime acceptance

D5.4 architecture has now been exercised in both directions:

```text
onn durable intent -> Linux revisioned authority
Linux revisioned authority -> onn durable projection
```

Validated properties:
- seed only when Linux is uninitialized;
- local durable mutation push;
- Linux monotonic revision;
- stale-write conflict rejection;
- initialized Linux pull;
- exact canonical local/remote parity after pull;
- runtime observations excluded.

The remaining issue is not data-contract correctness. It is when/how the TV UI
invokes the synchronization path and how sync/conflict status is surfaced to the
user.
<!-- PRIVYHUB_D118_PULL_ACCEPTANCE:ARCH:END -->

<!-- PRIVYHUB_D117_PULL_VALIDATION:ARCH:BEGIN -->
## Runtime status through D-116

Validated:
- Linux revisioned authority;
- seed from onn when authority is empty;
- durable onn mutation push;
- optimistic server revision;
- exact local/remote durable-state parity.

Still to validate:
- initialized/newer Linux authority pulled into onn.

D-117 tests this without changing any channel-selection preference:
only `country_name` changes, while `country_code` remains identical.

This preserves the distinction between testing synchronization mechanics and
changing TV product behavior.
<!-- PRIVYHUB_D117_PULL_VALIDATION:ARCH:END -->

<!-- PRIVYHUB_D116_TV_STATE_SYNC:ARCH:BEGIN -->
## D-116 Android client seam

```text
onn local durable intent
        |
durable projection JSON
        |
TvStateSyncClient
        |
/plugins/tv_state/state
        |
Linux revisioned authority
```

TV entry:
- ensure local catalog;
- GET authority;
- seed if revision 0/uninitialized;
- otherwise apply Linux state locally.

Durable mutation:
- export current durable projection;
- POST using locally remembered `base_revision`;
- update remembered revision on success;
- reject conflict without overwriting Linux.

Import preserves runtime observations:
channel health counters, last-watched data, and auto-hidden state are not reset
as part of durable synchronization.

Provider changes may refresh catalog data before channel-level durable overrides
are applied.

Initial model assumes one actively mutating client. Multi-client merge is
deferred.
<!-- PRIVYHUB_D116_TV_STATE_SYNC:ARCH:END -->

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
