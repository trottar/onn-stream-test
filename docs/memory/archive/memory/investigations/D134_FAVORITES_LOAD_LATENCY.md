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

<!-- PRIVYHUB_D134_RUNTIME_RESULT:BEGIN -->
## Runtime result — 2026-09-17

Probe label: `D134_FAVORITES_UI_RENDER_DOMINANT`.

Raw evidence overrides that label:

- total 24,382 ms;
- named stages sum 1,530 ms;
- residual 22,852 ms.

Source confirms the residual is consistent with pre-stage executor queue wait
behind D-131 TV-state synchronization on the shared single-thread executor.

**Status: diagnostic closed; D-135 owns executor isolation.**
<!-- PRIVYHUB_D134_RUNTIME_RESULT:END -->
