# D-111 decision — Android companion-first EPG lookup

<!-- PRIVYHUB_D112_D5_GUIDE_NEWLINE:D111_DECISION_STATUS:BEGIN -->
## Runtime status

**Runtime validated / accepted on 2026-09-16.**

The companion-first policy produced 65 programmes for
`10Bold.au@Sydney`, persisted them into the onn EPG SQLite database, and the
existing Program Guide rendered the schedule.

The D-112 literal-newline UI polish does not alter this decision.
<!-- PRIVYHUB_D112_D5_GUIDE_NEWLINE:D111_DECISION_STATUS:END -->

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
