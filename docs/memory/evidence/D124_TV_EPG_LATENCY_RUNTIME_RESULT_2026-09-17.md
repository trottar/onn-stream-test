# D-124 — TV/EPG latency runtime result — 2026-09-17

**Classification:**

`D124_COMPANION_GUIDE_FETCH_LATENCY_OBSERVED`

Measured:

- companion `/status`: 12.802 ms;
- EPG status: 1.093 ms;
- Favorites: 21 distinct meaningful channel IDs;
- Favorites with current/future Android programme cache: 8;
- favorite programme-cache ratio: 0.381;
- Android EPG programme rows: 361 across 9 channels;
- fallback `guide_mappings`: 2;
- representative SQLite query maximum: 0.352 ms;
- cached guide samples: 1.498 ms and 1.212 ms;
- uncached CBS Sports HQ guide acquisition: 19,080.876 ms.

Conclusion:

SQLite is not the observed interactive bottleneck.

The current synchronous companion cache-miss acquisition path is capable of
blocking the Android guide request for roughly 19 seconds.

The next production change should remove synchronous acquisition from normal
interactive guide reads and perform acquisition behind a background queue.
