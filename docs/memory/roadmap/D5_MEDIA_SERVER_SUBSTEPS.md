---
memory_schema: 1
as_of: 2026-09-16
baseline_commit: 53fd9b176647bad324a9fdae4d4f04b2f62e43a4
---

# D5 Media / Server Restoration Substeps

<!-- PRIVYHUB_D117_PULL_VALIDATION:D5_SUBSTEPS:BEGIN -->
## D5.4 — seed/push accepted; pull validation active

D-116 accepts:
- initial Linux seed;
- onn-to-Linux durable mutation push;
- manual-hidden persistence;
- canonical local/remote parity.

D-117 is the final directional synchronization check:
Linux newer -> onn -> Linux restored -> onn restored.

If D-117 passes, assess only conflict/diagnostic UX and media regression needs
before declaring D5.4 complete.
<!-- PRIVYHUB_D117_PULL_VALIDATION:D5_SUBSTEPS:END -->

<!-- PRIVYHUB_D116_TV_STATE_SYNC:D5_SUBSTEPS:BEGIN -->
## D5.4 — D-116 Android synchronization

D-115 Linux authority is runtime accepted.

D-116 implements the first end-to-end TV durable-state synchronization:
- seed empty Linux authority from onn;
- pull initialized authority on TV entry;
- push durable mutations with optimistic revision checking;
- remain fail-soft when companion is unavailable.

Runtime acceptance requires local/remote durable parity and a real post-seed
manual-hidden push.

After D-116 passes, D5.4 can assess remaining sync UX/conflict diagnostics before
closure.
<!-- PRIVYHUB_D116_TV_STATE_SYNC:D5_SUBSTEPS:END -->

<!-- PRIVYHUB_D115_TV_STATE_AUTHORITY:D5_SUBSTEPS:BEGIN -->
## D5.4 substep 1 — Linux durable TV-state authority

D-115 establishes the server side before client synchronization.

State contract:
- versioned JSON;
- durable user intent only;
- Linux `server_revision`;
- compare-and-swap style `base_revision`;
- local ignored persistence under `data/tv_state`.

Android remains local/offline-capable and unchanged in this substep.

After D-115 runtime validation, D-116 may implement one-client bootstrap/sync.
<!-- PRIVYHUB_D115_TV_STATE_AUTHORITY:D5_SUBSTEPS:END -->

<!-- PRIVYHUB_D114_STREAM_IDENTITY_POLICY:D5_SUBSTEPS:BEGIN -->
## D5.3 closeout and D5.4 activation

D5.3 EPG data path remains runtime validated:
Linux acquisition/cache -> companion API -> Android repository -> onn SQLite ->
Program Guide.

D-113 established a separate third-party stream-identity quality issue, not an
EPG transport regression.

D-113 policy closeout:
- confirmed 10 Bold upstream/source defect;
- only 9/3,071 feed-name heuristic hits;
- several hits are ambiguous;
- no generic automatic identity-suspect production rule.

D5.4 is now ACTIVE.

First D5.4 contract must synchronize durable TV user intent, including
`manual_hidden`, while keeping catalogs/EPG derived and runtime health outside
the initial authoritative merge.
<!-- PRIVYHUB_D114_STREAM_IDENTITY_POLICY:D5_SUBSTEPS:END -->

<!-- PRIVYHUB_D113_D5_STREAM_IDENTITY:D5_SUBSTEPS:BEGIN -->
## D5.3 post-acceptance integrity checkpoint — D-113

The D-111 EPG data path remains runtime validated.

D-112 readability polish is accepted.

A mislabeled upstream stream demonstrated that a technically correct guide can
still disagree with video when stream identity metadata is wrong.

D-113 does not reopen acquisition/cache architecture. It audits semantic stream
identity metadata before D5.4 begins.

Required result:
catalog-wide count/details of explicit feed-ID/display-name contradictions, with
10 Bold examined as the known trigger case.

D5.4 state sync remains next after this bounded integrity decision.
<!-- PRIVYHUB_D113_D5_STREAM_IDENTITY:D5_SUBSTEPS:END -->

<!-- PRIVYHUB_D112_D5_GUIDE_NEWLINE:D5_SUBSTEPS:BEGIN -->
## D5.3 accepted — D-112 visual polish

D-111 completed the D5.3 EPG data path.

Runtime acceptance:
- Linux acquisition/cache accepted;
- Android companion consumption accepted;
- onn SQLite persistence confirmed;
- Program Guide schedule rendering confirmed.

D5.3 is **runtime validated / accepted**.

D-112 is a non-architectural polish:
replace literal `\n` separators in the Program Guide with real line breaks.

After D-112 visual confirmation, begin D5.4 TV durable-state ownership/sync.
<!-- PRIVYHUB_D112_D5_GUIDE_NEWLINE:D5_SUBSTEPS:END -->

<!-- PRIVYHUB_D111_D5_ANDROID_COMPANION_EPG:D5_SUBSTEPS:BEGIN -->
## D5.3 execution checkpoint — D-111

D-110 Linux EPG service/cache seam is runtime validated.

D-111 is the Android integration substep.

Scope:
1. retain fresh onn SQLite guide as first read;
2. use companion EPG for refresh;
3. persist companion programmes into onn SQLite;
4. fail soft to local data;
5. preserve old hosted-source path as fallback;
6. runtime-validate both UI schedule and DB companion-success marker.

D5.3 may be marked functionally accepted only after D-111 runtime validation.

D5.4 TV-state ownership/sync remains next after that acceptance.
<!-- PRIVYHUB_D111_D5_ANDROID_COMPANION_EPG:D5_SUBSTEPS:END -->

<!-- PRIVYHUB_D110_D5_LINUX_EPG_SERVICE:D5_SUBSTEPS:BEGIN -->
## D5.3 execution checkpoint — D-110

D-109 local programme acquisition is runtime validated across multiple guide
sites.

D5.3 remains ACTIVE / not accepted because the result is still a diagnostic
toolchain path rather than a PrivyHub service boundary.

D-110 adds and validates the Linux companion EPG plugin/cache seam.

Acceptance for this substep:
1. status endpoint responds with the expected schema;
2. persistent toolchain bootstrap succeeds;
3. two representative canonical channels return programmes;
4. repeated first-channel read is served from cache;
5. companion startup remains independent of EPG bootstrap.

Android integration remains D-111 and is not part of D-110.
<!-- PRIVYHUB_D110_D5_LINUX_EPG_SERVICE:D5_SUBSTEPS:END -->

<!-- PRIVYHUB_D109_D5_EPG_PORTABLE_NODE:D5_SUBSTEPS:BEGIN -->
## D5.3 execution checkpoint — D-109

D-108 is complete as an environment diagnostic:
the Linux host has no Node/npm, so acquisition was not attempted.

D5.3 remains ACTIVE / not accepted.

D-109 reruns the exact D-108 acquisition path under a temporary verified Node
runtime without altering the appliance toolchain.

Next branch depends only on D-109/D-108 runtime evidence:
- multi-site programme output -> design smallest production EPG acquisition/cache
  seam;
- setup failure -> diagnose upstream toolchain;
- acquisition failure -> diagnose first failing site boundary.
<!-- PRIVYHUB_D109_D5_EPG_PORTABLE_NODE:D5_SUBSTEPS:END -->

<!-- PRIVYHUB_D108_D5_EPG_LOCAL_GRABBER:D5_SUBSTEPS:BEGIN -->
## D5.3 execution checkpoint — D-108

D-107 feed-aware identity measurement is complete.

Accepted diagnostic facts:
- built-in exact canonical metadata coverage is 40.3712%;
- base-channel metadata presence is higher;
- public hosted guide-source availability remains only 2 canonical IDs.

D5.3 remains ACTIVE / not accepted.

D-108 tests one narrow question:
whether Linux-local acquisition can produce actual programme data from the
current upstream EPG site definitions for a small exact-matched multi-site
sample.

If viable, the following production patch should design the smallest companion
EPG cache/acquisition seam. If not, diagnose the measured acquisition/toolchain
failure before changing architecture.
<!-- PRIVYHUB_D108_D5_EPG_LOCAL_GRABBER:D5_SUBSTEPS:END -->

<!-- PRIVYHUB_D107_D5_EPG_FEED_IDENTITY:D5_SUBSTEPS:BEGIN -->
## D5.3 execution checkpoint — D-107

D-106 completed but exposed a representation error in the guide-coverage
diagnostics.

D5.3 remains ACTIVE / not accepted.

D-107:
1. rebuild guide identity as `channel@feed` when feed is present;
2. recompute built-in English playlist exact coverage;
3. measure base-channel and blank-feed fallback candidates separately;
4. recompute provider-specific onn coverage;
5. preserve public hosted-source availability as an independent measurement.

Only after D-107 should D5 choose between Linux-local guide acquisition,
feed-aware production mapping, or alternative guide sources.
<!-- PRIVYHUB_D107_D5_EPG_FEED_IDENTITY:D5_SUBSTEPS:END -->

<!-- PRIVYHUB_D106_D5_EPG_PROVIDER_IDENTITY:D5_SUBSTEPS:BEGIN -->
## D5.3 execution checkpoint — D-106

D-105 is complete and showed weak metadata coverage:
89 exact matches among 3,286 nonblank onn channel IDs.

D5.3 remains ACTIVE / not accepted.

D-106 now measures:
1. built-in English playlist `tvg-id` completeness;
2. built-in playlist exact guide-metadata coverage;
3. onn meaningful versus synthetic `tv_stream_*` identity counts;
4. provider-specific meaningful identity and guide coverage.

Only after D-106 should D5 choose between provider identity work, alternative
guide sources, or a limited Linux-local EPG acquisition path.
<!-- PRIVYHUB_D106_D5_EPG_PROVIDER_IDENTITY:D5_SUBSTEPS:END -->

<!-- PRIVYHUB_D105_D5_EPG_LOCAL_SOURCE_VIABILITY:D5_SUBSTEPS:BEGIN -->
## D5.3 correction — D-105 source-availability boundary

D-104R2 did not increase runtime EPG mappings or programmes.

D5.3 remains ACTIVE, not accepted.

The next substep is D-105:
1. measure all guide metadata IDs against the onn catalog before `sources[]`;
2. measure English guide metadata coverage;
3. measure currently source-backed matched channels;
4. identify the guide sites with the largest matched channel coverage;
5. decide between Linux-local EPG acquisition/cache and an identity/provider
   investigation.

TV-state ownership/sync remains D5.4 after the EPG direction is resolved.
<!-- PRIVYHUB_D105_D5_EPG_LOCAL_SOURCE_VIABILITY:D5_SUBSTEPS:END -->

<!-- PRIVYHUB_D104R2_D5_EPG_GZIP_SOURCE_SUPPORT:D5_SUBSTEPS:BEGIN -->
## D5.2/D5.3 execution checkpoint — D-104

D5.2 is complete:
- the upstream guide endpoint is reachable;
- the XML-only source gate reduced 180,681 records to 2;
- the onn cache exactly reflected that 2-row result.

D5.3 begins with one compatibility repair:
- XML preferred;
- GZIP fallback;
- gzip-magic decompression into the existing XMLTV parser;
- mapping-source parser version forces one refresh after upgrade.

Not included:
- JSON guide parsing;
- fuzzy/canonical channel matching;
- guide-grid UX;
- broader catalog redesign.

Post-fix D-103 decides whether D5.3 is accepted or whether a new measured
identity/programme boundary remains.
<!-- PRIVYHUB_D104R2_D5_EPG_GZIP_SOURCE_SUPPORT:D5_SUBSTEPS:END -->


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
