# D-111 decision — Android companion-first EPG lookup

**Date:** 2026-09-16

**Status:** development accepted / runtime validation pending

## Decision

For D5 Android guide requests:

- keep the onn SQLite cache as the immediate/offline layer;
- prefer the runtime-validated Linux companion EPG service when cache refresh is
  needed;
- preserve the older public hosted-guide path only as a fallback;
- do not move TV UI/catalog ownership in this patch.

## Rationale

D-110 proved:

- Linux guide acquisition works;
- uncached acquisition is several seconds;
- cached acquisition is effectively immediate;
- Linux can persist/reuse the expensive toolchain;
- Android already performs EPG work on its network executor.

Therefore companion-first refresh plus onn-local cache gives the desired
local-first behavior without coupling Android to upstream EPG implementation
details.

## Failure behavior

- fresh onn cache: no Linux request;
- Linux unavailable + stale/nonempty onn cache: keep local data;
- Linux reachable but no exact guide: do not erase local data;
- no local data + Linux unavailable: previous public fallback remains;
- playback remains independent from EPG success.
