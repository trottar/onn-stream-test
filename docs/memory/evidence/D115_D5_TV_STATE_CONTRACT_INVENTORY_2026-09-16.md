# D-115 — D5.4 TV-state contract inventory — 2026-09-16

**Status:** source-validated design input

## Existing Android export/import contract

`TvRepository.exportSettingsJson()` currently emits version `2`.

It includes:

- `managed_providers`
  - `provider_id`
  - `enabled`
- `providers`
  - `name`
  - `url`
  - `language_code`
  - `enabled`
- `channels`
  - `stream_id`
  - `favorite`
  - `manual_hidden`
  - `success_count`
  - `failure_count`
  - `consecutive_failures`
  - `last_success`
  - `last_failure`
  - `last_watched`
  - `custom_name`
  - `custom_category`
  - `custom_url`
  - `custom_referrer`
  - `custom_user_agent`
  - `favorite_group`
  - `favorite_order`
  - `protect_auto_hide`

The import path also clears `auto_hidden` while restoring channel state.

## Important split

The version-2 Android backup combines two state classes:

### Durable user intent

- managed/custom provider state;
- favorites;
- manual hidden state;
- custom channel profile fields;
- favorite group/order;
- protect-auto-hide.

### Runtime observations

- success/failure counts;
- consecutive failures;
- last success/failure;
- last watched.

D5.4 must not make the runtime observations Linux-authoritative through the same
first-generation state contract.

## Language/country

Language and country are not stored by `TvRepository.exportSettingsJson()`.

They live in Android `privyhub_settings` preferences:

- `tv_language`;
- `tv_language_name`;
- `tv_country`;
- `tv_country_name`.

They are durable user intent and must be included in the D5.4 projection.

## D-115 projection

D-115 introduces:

`privyhub_tv_user_state_v1`

Fields:

- `preferences`
  - language code/name;
  - country code/name;
- `managed_providers`;
- `providers`;
- `channels` containing only durable channel intent.

The Linux plugin normalizes through a whitelist, so extra Android runtime fields
are not persisted even if a caller accidentally supplies them.

## Revision model

Linux assigns a monotonic `server_revision`.

A write supplies `base_revision`.

If `base_revision` does not equal current Linux revision, the write is rejected
as a conflict and current authoritative state is returned.

Identical writes are idempotent and do not consume a new revision.

This is sufficient for the first one-client D5.4 implementation while leaving
multi-client merge policy for later work.
