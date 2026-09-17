# D-124A — TV/EPG latency probe split-database correction

**Date:** 2026-09-17

**Type:** diagnostic-only correction

## Runtime failure

The first D-124 runtime attempt stopped before producing its report:

`sqlite3.OperationalError: no such table: programmes`

The failing measurement executed on the `privyhub_tv.db` connection while its
SQL subquery referenced `programmes`, which belongs to `privyhub_epg.db`.

This is a D-124 probe defect. It is not evidence of a TV/EPG production defect.

## Correction

D-124A keeps the same measurement plan but computes favorite EPG-cache coverage
across the two read-only snapshots explicitly:

1. collect distinct visible favorite channel IDs from the TV DB;
2. collect distinct current/future programme channel IDs from the EPG DB;
3. intersect those sets in Python.

A split-database self-test now creates separate in-memory TV and EPG databases
and requires the coverage helper to return the expected counts. This directly
guards the failure mode observed at runtime.

## Production scope

No Android production code change.

No companion production code change.

No APK build/install.

No companion restart.

D-124 runtime evidence remains pending until the corrected probe is rerun.
