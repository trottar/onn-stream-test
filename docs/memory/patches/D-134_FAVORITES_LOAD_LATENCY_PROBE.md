# D-134 — Favorites load latency probe

**Date:** 2026-09-17

Diagnostic-only timing instrumentation around the existing `openTvPage()` path.

Production behavior is unchanged.

Probe:
`tools/probes/d134_favorites_load_latency_probe.py`

Runtime classifications include hydrate-, prefetch-, database-, UI-render-, and
mixed-latency outcomes.
