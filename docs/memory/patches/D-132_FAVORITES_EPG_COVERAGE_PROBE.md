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
