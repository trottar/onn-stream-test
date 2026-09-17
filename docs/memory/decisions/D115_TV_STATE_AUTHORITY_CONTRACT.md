# D-115 — Linux TV-state authority contract

**Date:** 2026-09-16

**Status:** development implementation / runtime validation pending

## Decision

Create the Linux durable TV-state authority before changing Android sync
behavior.

Linux persists only the D5.4 durable user-intent projection under:

`data/tv_state/state.json`

The file is ignored runtime state and is not committed.

## API

Through the existing companion plugin API:

- `GET /plugins/tv_state/status`
- `GET /plugins/tv_state/state`
- `POST /plugins/tv_state/state`

The POST request uses a bounded JSON body.

Generic plugin POST routing gains an opt-in
`handle_post_json_request(...)` path; existing plugins keep their current
query-only POST behavior.

## Schemas

- status: `privyhub_tv_state_status_v1`
- envelope: `privyhub_tv_state_envelope_v1`
- update: `privyhub_tv_state_update_v1`
- user state: `privyhub_tv_user_state_v1`

## Durable state

Linux stores:

- language/country preferences;
- managed provider enabled state;
- custom provider definitions/enabled state;
- favorite state;
- manual hidden state;
- custom channel profile overrides;
- favorite group/order;
- protect-auto-hide.

Linux does **not** store in this contract:

- success/failure counters;
- consecutive failures;
- last success/failure;
- last watched;
- auto-hidden runtime health result;
- catalog rows;
- EPG mappings/programmes.

## Concurrency

Linux owns `server_revision`.

Write rules:

- caller supplies `base_revision`;
- exact current revision is required;
- stale write returns `revision_conflict`;
- no state mutation occurs on conflict;
- identical state is idempotent and retains the current revision.

## Persistence

Writes use a temporary file, fsync, `os.replace`, post-write verification, and
mode `0600`.

The state includes a canonical SHA-256 for corruption detection.

## Privacy

The plugin does not retain client network addresses.

`updated_by` comes only from an explicit application `client_id`.

## Follow-up

After D-115 Linux runtime validation, D-116 may add Android projection,
bootstrap, pull/apply, push, retry, and conflict handling.

A first Android migration must seed an uninitialized Linux authority from the
current onn durable projection before Linux is allowed to overwrite local user
intent.
