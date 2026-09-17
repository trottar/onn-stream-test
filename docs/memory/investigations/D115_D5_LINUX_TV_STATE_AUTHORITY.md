# D-115 — D5.4 Linux TV-state authority

**Status:** development patch / runtime validation next

## Narrow goal

Validate the Linux persistence/revision boundary before Android sync is enabled.

## Production changes

- new `companion/plugins/tv_state.py`;
- register `TvStatePlugin`;
- generic plugin POST routing gains an opt-in JSON-body handler.

Existing query-only plugin POST handlers are preserved unchanged.

## Runtime validation

`tools/probes/d115_tv_state_authority_probe.py`

The probe:

1. saves the exact existing `data/tv_state/state.json` bytes if present;
2. GETs status/state through the running companion;
3. writes a durable-state fixture at the current base revision;
4. GETs and verifies persistence;
5. verifies runtime-only fields were not retained;
6. repeats the same write and requires no revision increment;
7. submits a stale-revision write and requires conflict/no mutation;
8. restores the exact original state file or removes the fixture file if no
   state existed before the probe.

The plugin reads state from disk on every operation, so exact file restoration
also restores the live authority visible to later requests.

## Acceptance

Required classification:

`D115_TV_STATE_AUTHORITY_RUNTIME_VALIDATED`

This validates the Linux authority only.

Android still remains onn-local until the next patch.
