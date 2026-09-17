# D-134 — Favorites load latency probe

**Date:** 2026-09-17

Diagnostic-only timing instrumentation around the existing `openTvPage()` path.

Production behavior is unchanged.

Probe:
`tools/probes/d134_favorites_load_latency_probe.py`

Runtime classifications include hydrate-, prefetch-, database-, UI-render-, and
mixed-latency outcomes.

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
