# D-110 decision — Linux EPG acquisition/cache seam

**Date:** 2026-09-16

**Status:** development accepted / runtime validation pending

## Decision

Use the Linux companion as the EPG acquisition/cache owner for D5.

Expose EPG through the existing companion plugin API.

Keep Android's existing local EPG SQLite/UI behavior until the Linux seam passes
runtime validation.

## Rationale

D-109 proved local programme acquisition across three independent upstream
sites, so acquisition is technically viable.

The reference toolchain also measured:

- approximately 77 seconds initial setup;
- approximately 446 MB disposable upstream dependency tree;
- approximately 7–8 seconds per representative uncached grab.

Therefore rebuilding the grabber per request is unsuitable.

A persistent rebuildable toolchain and programme cache are appropriate for
Prototype-1, while system-wide Node/npm installation is not.

## Constraints

- runtime/tooling state belongs under ignored `data/`;
- no bundled Node binary in Git or patch ZIP;
- official runtime checksum verification is mandatory;
- upstream EPG commit is pinned;
- companion startup must not block on EPG bootstrap;
- exact feed-aware IDs remain authoritative;
- no fuzzy matching;
- cache and acquisition failures fail soft;
- final production dependency optimization remains open because the reference
  toolchain footprint is large for future low-cost Linux targets.

## Follow-up

D-110 runtime-validates the Linux plugin/cache boundary.

D-111 may then connect Android `TvEpgRepository` to the companion endpoint while
preserving local cache/offline behavior.
