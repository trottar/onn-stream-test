# D-120 — D5.4 TV-state sync diagnostics

**Status:** Android production observability patch / runtime validation pending

## Purpose

Expose enough persisted TV-state synchronization metadata to understand whether
the onn is current with Linux without relying on Logcat.

D-119 proved the normal top-level TV-entry trigger is reliable. The remaining
gap is observability.

## Existing limitation

Before D-120:

- Android persisted only `tv_state_server_revision`;
- revision conflicts were visible only as a Logcat warning;
- successful sync action/time were not persisted;
- TV Settings -> Catalog / EPG Status did not expose TV-state sync status.

## D-120 scope

Persist locally on the onn:

- last successful sync timestamp;
- last successful sync action;
- last successful sync revision;
- last conflict timestamp;
- last conflict local base revision;
- last conflict Linux server revision.

Display in the existing Catalog / EPG Status dialog:

- current TV-state revision;
- last state sync action/time;
- last successful sync revision;
- last state conflict details or `Never`.

No network address or device identifier is stored in these diagnostics.

## Semantics unchanged

D-120 does not:

- auto-resolve conflicts;
- change Linux authority;
- change optimistic revision behavior;
- change fail-soft offline behavior;
- synchronize health/recency;
- change catalog/EPG/playback.

Runtime acceptance requires a top-level TV entry after APK installation followed
by the read-only D-120 probe.
