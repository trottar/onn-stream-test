---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 0206017cfd8f0fc57decb7a5e9e8632e6a4f6cdd
---

# Curated Project Memory

<!-- PRIVYHUB_D129_SINGLE_COLUMN_GUIDE:MEMORY:BEGIN -->
## TV guide presentation rule

D-128 runtime established that adding Now/Next text to the generic three-column
source-button grid is not equivalent to a TV guide. TV result pages (Favorites,
category results, search/result pages) must use a dedicated one-column,
full-width row presentation. Non-TV catalog/VOD/Games pages retain their normal
tile layout.

D-129 runtime validated this contract: four visible Favorites guide rows were
full-width and one-column; three carried current-programme data and one showed an
explicit unavailable-guide state.

Guide presentation and guide acquisition remain separate. Android may perform a
bounded companion-only hydration pass to copy already-warmed guide data into its
local cache, but normal UI rendering must not restore synchronous upstream EPG
acquisition. Missing data is represented explicitly in the guide row.
<!-- PRIVYHUB_D129_SINGLE_COLUMN_GUIDE:MEMORY:END -->

<!-- PRIVYHUB_D128_GUIDE_STYLE:UI_RULE:BEGIN -->
## TV guide-row presentation rule

TV category/Favorites rendering consumes Android cached guide state only.
Rendering must not synchronously acquire EPG data or mutate channel state.
D-125/D-126 remain responsible for non-blocking acquisition/warm-ahead.

Guide-backed rows may present compact current/next time ranges. A D-127
`guide_incorrect` mark overrides those cached rows: rejected guide data may remain
cached for recheck but is not presented as trusted Now/Next content.
<!-- PRIVYHUB_D128_GUIDE_STYLE:UI_RULE:END -->

## Incorrect-guide durable-intent rule (D-127 accepted)

A bad EPG mapping is not a playback-health failure and must not hide an otherwise
playable channel. D-127 carries incorrect-guide state as Linux-authoritative
durable user intent, separate from `manual_hidden`/`auto_hidden`. The rejected
guide source is stored as a stable fingerprint rather than a raw upstream URL.

Marked guide programme data may remain cached for comparison/recheck but is not
presented as trusted. Background recheck may warm replacement data after a
bounded delay; it never clears the user's mark. Trust is restored only by an
explicit Retry/Accept or Clear action. TV user-state v2 is fail-closed at the
Android sync boundary; Linux alone migrates persisted v1 authority to v2 without
advancing the household revision.

**Status:** runtime validated by D-127 durable Android/Linux parity evidence.


This file contains durable rules and repeatedly useful validated facts. It is not
a patch log or current-task tracker. Current work belongs in `CURRENT.md`.

## Mission and trust model

PrivyHub is a local-first, privacy-preserving, modular smart-home/media system.
The trusted home/PrivyHub network is distinct from ordinary upstream Internet
connectivity. The architecture should remain portable from the current onn
Android TV + Linux prototype toward inexpensive Linux server hardware and
additional trusted clients without mandatory cloud, subscriptions, or
proprietary infrastructure.

Local deterministic control is the baseline.

## Development method

- One narrow hypothesis -> one targeted diagnostic -> fresh evidence -> inspect
  evidence -> one coherent patch.
- Current local source and newest specific runtime evidence outrank summaries.
- Raw measurements outrank classifiers when they disagree.
- Compile/build success is not runtime validation.
- Do not reopen resolved/deferred investigations without contradictory evidence.
- Preserve stable subsystems for unrelated work.
- Never ask the user to provide or paste IP addresses.
- Shareable diagnostics must exclude addresses, private ADB endpoints, device
  identifiers, credentials, and secrets.

Memory maintenance follows `MAINTENANCE.md`.

## Games / Linux runtime

The Linux Games path is accepted for the representative exercised systems.

Durable architecture:

- managed RetroArch frontend;
- exact owned X11 window capture through `x11grab`;
- VAAPI H.264 on the Renoir Linux prototype;
- isolated PulseAudio process audio;
- PHI1 -> Linux uinput -> RetroArch udev controllers;
- P1-P4 routing and PS1 Port-1-only multitap;
- pause/resume, Save/Load, cheats/mod isolation, A8 profiles, and graceful End.

SNES and PS1 have representative Linux runtime evidence. NES/Genesis remain
configured/supported but must not be described as Linux runtime validated
without fixtures.

Do not disturb the validated video/audio/controller/lifecycle stack for TV or
memory-maintenance work.

## Native-stream rules

Portable stream/profile semantics are distinct from host capture/encoder policy,
audio, controller transport, and telemetry.

Windows fixed-bitrate evidence and the old Opal UDP pathology are not universal
product constants. The Opal/Siflower transport reverse-engineering branch is
paused unless a bounded new measurement can change a product decision.

## External VOD storage contract

Bulk VOD physical storage is separate from the logical `/vod` namespace.

Validated rules:

- logical source identity survives physical mount-path changes;
- removable storage may be absent while the companion remains healthy;
- missing storage is availability, not authoritative deletion;
- stale Continue Watching entries fail cleanly while media is absent;
- reinsertion repopulates the same logical library without desktop/file-manager
  activation;
- normal appliance operation keeps the system automount available and uses
  read-only media access;
- raw filesystem identifiers remain machine-local and out of shareable logs.

Do not reopen this storage architecture without new regression evidence.

## TV durable-state authority

Linux is the durable authority for TV user intent. The onn keeps a local cache
for responsive/offline operation.

The versioned durable state includes:

- language/country preferences;
- provider definitions/enabled state;
- favorites;
- favorite groups/order;
- manual hidden;
- custom channel name/category/URL/referrer/user-agent overrides;
- protect-auto-hide;
- other explicitly accepted durable user-intent fields.

It excludes:

- EPG/cache data;
- downloaded catalog rows;
- playback-health counters;
- last-watched/recency;
- auto-hidden runtime result.

Never synchronize raw SQLite databases.

Linux owns monotonic `server_revision`. Writes use `base_revision`; stale writes
fail closed. Identical canonical state is idempotent.

Validated D5.4 behavior includes:

- seed from onn only while Linux authority is uninitialized;
- initialized Linux authority pulls to onn;
- local durable mutations push with revision protection;
- stale writes are rejected without overwriting Linux;
- conflict diagnostics are recorded;
- later authoritative pull restores exact parity;
- top-level TV entry invokes the normal pull path;
- companion outage does not make local TV unusable.

Do not add multi-client merge semantics casually.

## EPG ownership and cache rules

Linux owns EPG acquisition/cache generation. Android owns its local SQLite/UI
cache.

Canonical IPTV-org identity is feed-aware:

- blank feed -> `channel`;
- nonblank feed -> `channel@feed`.

Do not compare a composite stream identity only against a guide's bare channel
field.

Android guide policy:

1. use fresh nonempty onn SQLite data immediately;
2. otherwise use the Linux companion;
3. persist successful companion programmes locally;
4. preserve stale/nonempty local data if Linux is temporarily unavailable;
5. legacy public-hosted mapping/acquisition remains fallback behavior.

Playback must not depend on EPG success.

`guide_mappings` is a legacy/fallback mapping count. It is not total guide
coverage from the companion.

## EPG performance rule

Synchronous upstream guide acquisition must not occur on the normal interactive
request path.

Measured evidence established:

- cached guide reads are effectively immediate;
- upstream uncached acquisition can take many seconds;
- representative SQLite query cost is negligible by comparison.

D-125 therefore makes normal missing/stale reads cache-first and non-blocking,
with deduplicated Linux background acquisition. Explicit force-refresh may remain
synchronous.

D-126 submits stale/missing Favorites on TV entry and visible-page identities on
TV result pages so likely guide data warms before an explicit guide open.

Do not regress these boundaries when implementing incorrect-guide state or guide
UI.

## Semantic stream/guide integrity

Transport health, catalog/feed metadata consistency, actual video identity, and
EPG correctness are separate dimensions.

A stream may play successfully and have a functioning guide while carrying the
wrong semantic channel.

The confirmed 10 Bold mismatch demonstrates this boundary. Do not hardcode one
third-party URL or treat a heuristic feed-name contradiction as universal proof.

Current product rule:

- Hide is durable user intent for hiding a bad source.
- Incorrect-guide intent should be separate from Hide so a playable channel can
  remain visible while its guide is distrusted.

## Diagnostic and patch discipline

Meaningful patches:

- verify exact predecessor state/hash;
- reject wrong state before modification;
- back up changed files;
- preserve line endings/BOM where relevant;
- compile changed Python;
- run applicable real builds;
- run `git diff --check`;
- restore exact predecessor bytes on deterministic failure;
- update durable memory in the same work;
- set `durable_memory_updated: true`.

Use explicit result classes:

- `INSTALLED SUCCESSFULLY`
- `FAILED BEFORE MODIFICATION`
- `ROLLED BACK`

## Memory architecture

- `CURRENT.md` — single active resumable state.
- `MEMORY.md` — durable knowledge only.
- `MAINTENANCE.md` — memory lifecycle policy.
- dated memory / patch history — chronology.
- evidence — detailed proof.
- investigations — active/closed diagnostic detail.
- architecture/decisions — long-lived subsystem/decision records.
- `CURRENT_HANDOFF.md` — small handoff-only note.

Do not recursively summarize old summaries. Check canonical evidence before
removing important detail from active memory.
