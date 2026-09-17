# D-129 — Single-column TV guide

**Date:** 2026-09-17

## Purpose

Replace the failed D-128 text-only tile treatment with the requested actual TV
result layout: one full-width row per channel/program in a single vertical
column.

## Production files

- `PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt`
- `PrivyHub/app/src/main/java/com/safeiot/privyhub/TvEpgRepository.kt`

## Safety / validation

Installer verifies exact D-128 predecessor blobs, backs up every changed file,
compiles the diagnostic probe, runs probe/installer self-tests, runs the real
Android debug build, runs `git diff --check` and memory-health validation, and
restores exact predecessor bytes if a post-write gate fails.

## Runtime acceptance

Open TV -> Favorites and verify with:

`python3 tools/probes/d129_single_column_tv_guide_probe.py --repo . --verify`

Target:

`D129_SINGLE_COLUMN_TV_GUIDE_RUNTIME_VALIDATED`
