# D-125 — EPG non-blocking background warmer runtime acceptance — 2026-09-17

**Classification:**

`D125_NONBLOCKING_GUIDE_MISS_AND_BACKGROUND_WARMER_VALIDATED`

Measured uncached target:

- channel display name: `24 Hour Free Movies (720p)`;
- cache missing before request: true;
- interactive guide request: HTTP 200;
- interactive guide latency: 14.199 ms;
- refresh queued: true;
- immediate programme count: 0;
- immediate reason: `background_refresh_pending`;
- background acquisition duration: 10,039.458 ms;
- background cache created: true;
- background programme count: 7;
- worker pending count after completion: 0;
- worker completed count: 1;
- worker failed count: 0.

Conclusion:

D-125 eliminates the measured user-facing cache-miss stall.

The same slow upstream acquisition still exists, but it now runs behind the
Linux background worker while the interactive guide request returns in
milliseconds.
