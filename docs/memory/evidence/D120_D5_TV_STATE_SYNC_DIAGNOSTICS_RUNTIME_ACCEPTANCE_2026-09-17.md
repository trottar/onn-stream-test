# D-120 — D5.4 TV-state sync diagnostics runtime acceptance — 2026-09-17

**Status:** runtime validated / accepted

Classification:

`D120_TV_STATE_SYNC_DIAGNOSTICS_RUNTIME_VALIDATED`

Measured:

- Linux authority initialized: true;
- Linux server revision: 6;
- onn stored server revision: 6;
- Linux canonical durable-state SHA-256:
  `cea4fa1fba5ad7a903cf0c60ffbc528dc7d754932402ab77d11f9696ec65f2c3`;
- onn canonical durable-state SHA-256: identical;
- local/remote parity: true;
- last successful action: `pulled`;
- last successful revision: 6;
- last-conflict metadata: all zero / `Never`.

Visual confirmation in TV Settings -> Catalog / EPG Status:

- TV state revision: 6;
- Last state sync: Pulled;
- Last sync revision: 6;
- Last state conflict: Never.

Conclusion:

D-120 last-success diagnostics are runtime accepted. Conflict diagnostics are
implemented but require one controlled stale-write conflict before D5.4 closure.
