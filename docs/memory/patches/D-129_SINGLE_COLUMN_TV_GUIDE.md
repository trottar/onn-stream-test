# D-129 — Single-column TV guide

**Date:** 2026-09-17

**Status:** runtime accepted

## Purpose

Replace the failed D-128 text-only tile treatment with the requested actual TV
result layout: one full-width row per channel/program in a single vertical
column.

## Production files

- `PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt`
- `PrivyHub/app/src/main/java/com/safeiot/privyhub/TvEpgRepository.kt`

## Safety / validation

Installer verified exact D-128 predecessor blobs, backed up every changed file,
compiled the diagnostic probe, ran probe/installer self-tests, ran the real
Android debug build, ran `git diff --check` and memory-health validation.

## Runtime acceptance

`D129_SINGLE_COLUMN_TV_GUIDE_RUNTIME_VALIDATED`

The runtime probe measured four visible TV guide rows, all full-width and in one
column. Three rows contained current-programme data and one explicitly reported
unavailable guide data.

Evidence:
`docs/memory/evidence/D129_SINGLE_COLUMN_TV_GUIDE_RUNTIME_ACCEPTANCE_2026-09-17.md`.
