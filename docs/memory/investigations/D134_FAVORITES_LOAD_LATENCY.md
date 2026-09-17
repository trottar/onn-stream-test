# D-134 — Favorites load latency stage probe

**Date:** 2026-09-17
**Status:** diagnostic / runtime measurement required

The user reports Favorites can take >15 seconds to open after D-133.

Existing `openTvPage()` order:
1. count;
2. query;
3. companion prefetch;
4. rejected-guide prefetch;
5. synchronous `hydrateCompanionGuides()`;
6. UI render.

D-134 timestamps exactly these calls. It does not reorder or change behavior.
The leading hypothesis is hydration, but raw timings decide the next patch.
