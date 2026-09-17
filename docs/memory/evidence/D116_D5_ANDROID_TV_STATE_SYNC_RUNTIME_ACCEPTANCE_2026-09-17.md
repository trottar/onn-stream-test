# D-116 — D5.4 Android TV-state sync runtime acceptance — 2026-09-17

**Status:** runtime validated / accepted for seed + onn-to-Linux push

Classification:

`D116_ANDROID_TV_STATE_SYNC_RUNTIME_VALIDATED`

## Linux authority

- HTTP: 200;
- initialized: true;
- server revision: 2;
- canonical user-state SHA-256:
  `cea4fa1fba5ad7a903cf0c60ffbc528dc7d754932402ab77d11f9696ec65f2c3`.

## Onn durable projection

- ADB ready;
- snapshot successful;
- remembered server revision: 2;
- stable TV-state client ID present;
- durable channel rows: 25;
- favorites: 22;
- manual-hidden rows: 3;
- canonical user-state SHA-256 matched Linux exactly.

## Sync checks

- local/remote durable-state parity: true;
- post-seed push observed: true;
- `10 Bold Adelaide` present;
- local `manual_hidden`: true;
- Linux `manual_hidden`: true.

The probe did not modify Android or Linux state.

## Acceptance boundary

D-116 proves:

1. an uninitialized Linux authority can be seeded from the onn;
2. durable onn mutations can advance Linux revisioned state;
3. normalized Linux and onn durable projections can reach exact parity;
4. manual-hidden state survives through the authority boundary.

One remaining D5.4 acceptance question is Linux-to-onn pull when Linux is
intentionally newer. D-117 tests that direction reversibly.
