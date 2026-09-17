# D-116 — Android TV-state synchronization policy

<!-- PRIVYHUB_D117_PULL_VALIDATION:D116_POLICY_STATUS:BEGIN -->
## Runtime status

D-116 seed and onn-to-Linux push behavior is runtime validated and accepted.

The policy still requires one directional acceptance check before D5.4 closure:
Linux deliberately newer than the onn must be pulled and applied correctly.

D-117 validates that existing policy without changing production code.
<!-- PRIVYHUB_D117_PULL_VALIDATION:D116_POLICY_STATUS:END -->

**Date:** 2026-09-17

**Status:** development implementation / runtime validation pending

## Decision

Use Linux as the durable authority while preserving onn-local fail-soft
operation.

For the initial one-client implementation:

- uninitialized Linux state is seeded from the existing onn durable state;
- initialized Linux state wins on TV entry;
- local durable user actions are pushed with the last observed server revision;
- revision conflict is fail-closed and never silently overwrites newer Linux
  state;
- no raw SQLite database is copied;
- runtime health/recency data remains onn-local.

## Mutation boundary

`TvRepository` exposes a durable-state-change listener.

Only durable mutations notify it:

- favorites;
- manual hidden;
- favorite groups/order;
- custom profile overrides;
- protect-auto-hide;
- custom/managed provider changes;
- backup import because it may change durable fields.

Health counters and watched/recency operations do not notify the durable sync
layer.

Language/country preferences live in `MainActivity`, so their save operations
explicitly request a state push.

## Failure behavior

Companion synchronization is fail-soft for availability:

- Linux unreachable -> local TV continues;
- write conflict -> local state is not erased and Linux is not overwritten;
- next explicit/open synchronization can reconcile against authority.

Multi-client semantic merge remains deferred.
