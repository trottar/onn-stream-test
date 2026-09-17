# D-116 — D5.4 Android TV-state synchronization

<!-- PRIVYHUB_D117_PULL_VALIDATION:D116_RESULT:BEGIN -->
## Runtime result — 2026-09-17

D-116 passed:

`D116_ANDROID_TV_STATE_SYNC_RUNTIME_VALIDATED`

Measured:
- Linux initialized at revision 2;
- onn remembered revision 2;
- canonical local/remote state SHA-256 matched exactly;
- 25 durable channel rows;
- 22 favorites;
- 3 manual-hidden rows;
- post-seed push observed;
- `10 Bold Adelaide` manual-hidden on both sides.

D-116 seed and onn-to-Linux push are accepted.

D-117 validates the remaining Linux-to-onn pull direction before D5.4 closure.
<!-- PRIVYHUB_D117_PULL_VALIDATION:D116_RESULT:END -->

**Status:** development patch / runtime validation next

## Purpose

Connect the mature onn TV user-state implementation to D-115's validated Linux
authority.

## Initial one-client behavior

When TV is opened:

1. load the local catalog;
2. GET Linux TV state;
3. if Linux is uninitialized, seed it from the onn durable projection;
4. if Linux is initialized, Linux wins and its durable state is applied locally;
5. continue local TV operation if the companion is unavailable.

After durable local TV mutations:

- push the current durable projection using the locally remembered
  `server_revision`;
- identical writes remain idempotent;
- stale writes fail closed as revision conflicts;
- do not silently overwrite a newer Linux revision.

## Durable projection

Included:

- TV language/country;
- managed provider enabled state;
- custom providers;
- favorites;
- favorite groups/order;
- manual hidden state;
- custom channel name/category/URL/referrer/user-agent;
- protect-auto-hide.

Excluded:

- success/failure counters;
- consecutive failures;
- last success/failure;
- last watched;
- auto-hidden runtime state;
- catalog/EPG data.

## Runtime acceptance

After installing the APK:

1. open TV once so the empty Linux authority seeds from the onn;
2. hide `10 Bold Adelaide` using the existing Hide action;
3. run `tools/probes/d116_android_tv_state_sync_probe.py`.

Acceptance requires:

`D116_ANDROID_TV_STATE_SYNC_RUNTIME_VALIDATED`

The probe compares normalized Linux and onn durable state and verifies the
manual-hidden decision reached Linux at a later server revision.
