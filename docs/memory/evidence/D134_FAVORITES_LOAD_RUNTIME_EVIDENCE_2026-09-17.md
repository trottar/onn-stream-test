# D-134 — Favorites load runtime evidence

**Date:** 2026-09-17

Probe classifier output:

`D134_FAVORITES_UI_RENDER_DOMINANT`

Raw timings:

- total: 24,382 ms
- count: 26 ms
- query: 0 ms
- prefetch: 181 ms
- rejected prefetch: 2 ms
- hydrate: 477 ms
- UI render: 844 ms

Named measured stages sum to 1,530 ms. Residual:

`24,382 - 1,530 = 22,852 ms`

The classifier selected UI render only by comparing named stage durations; it did
not classify the residual interval. The raw measurements therefore override the
classifier label.

Source inspection shows `page_begin` is emitted before `networkExecutor.execute`,
and both D-131 background TV-state synchronization and `openTvPage()` use the
same single-thread `networkExecutor`. The ~22.85-second residual is consistent
with Favorites waiting in that executor queue behind the ~24-second TV-state pull.

Conclusion: D-134 closes with executor queue contention as the evidence-backed
cause. Do not optimize the 844 ms renderer as the primary fix.
