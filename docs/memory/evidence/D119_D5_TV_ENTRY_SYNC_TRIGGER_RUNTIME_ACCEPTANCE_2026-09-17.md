# D-119 — D5.4 top-level TV-entry sync-trigger runtime acceptance — 2026-09-17

**Status:** runtime validated / accepted

Classification:

`D119_TOP_LEVEL_TV_ENTRY_SYNC_TRIGGER_AND_RESTORE_VALIDATED`

Measured:

- initial Linux/onn revision: 4;
- prepared Linux marker revision: 5;
- top-level TV entry observed the prepared revision without Refresh;
- Linux restore revision: 6;
- final onn revision: 6;
- local/remote canonical durable-state parity: true;
- Linux original user-state content restored: true;
- onn original user-state content restored: true;
- D-119 session removed.

The test changed only the temporary Linux country display name. `country_code`
was never changed.

Conclusion:

Selecting TV from the true top-level PrivyHub source list reliably executes the
existing `openTvHome()` synchronization path. The earlier ambiguous D-117
observation was caused by imprecise navigation/test instructions, not a
production lifecycle defect.

No Android trigger/lifecycle patch is required.
