# D-132 — Favorites EPG coverage probe

**Date:** 2026-09-17

## Purpose

Classify remaining guide-coverage/status gaps in visible Favorites before the
final bounded D5 TV/EPG production change.

## Production files

None.

## Diagnostic

- `tools/probes/d132_favorites_epg_coverage_probe.py`

## Durable memory

Records D-131 runtime acceptance and advances active work to D-132.

## Validation

Installer checks exact predecessor HEAD/clean tracked state, backs up changed
memory files, compiles/runs the probe self-test, runs `git diff --check` and
memory-health validation, and restores exact predecessor bytes on deterministic
failure.

<!-- PRIVYHUB_D132_RUNTIME_RESULT:BEGIN -->
## Runtime result — 2026-09-17

`D132_FAVORITES_GUIDE_GAPS_CLASSIFIED`

- visible Favorites: 21
- Android current programme: 11
- companion programmes but no current programme: 5
- no known guide coverage: 5

The five schedule-gap rows also had Android future programmes. D-133 owns the
bounded presentation correction.

**Status: runtime measured / closed.**
<!-- PRIVYHUB_D132_RUNTIME_RESULT:END -->
