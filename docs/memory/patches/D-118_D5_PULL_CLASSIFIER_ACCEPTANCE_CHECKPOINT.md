# D-118 — D5 pull-classifier acceptance checkpoint

**Date:** 2026-09-17

**Type:** diagnostic correction / durable-memory checkpoint

## Purpose

Correct D-117's final classifier and record the measured D5.4 Linux-to-onn pull
as runtime accepted.

## Diagnostic defect

D-117 deleted its session when restored Linux/onn parity was achieved, but its
classification still returned `D117_FINAL_RESTORE_PARITY_FAILED` unless the
earlier temporary marker revision had also been observed.

That made the label contradict its raw final measurements.

## Correction

`final_classification()` now distinguishes:

- full marker + restore validation:
  `D117_LINUX_AUTHORITY_PULL_AND_RESTORE_RUNTIME_VALIDATED`;
- restored-authority pull validation without marker observation:
  `D117_LINUX_AUTHORITY_RESTORE_PULL_RUNTIME_VALIDATED`;
- actual restore/parity failure:
  `D117_FINAL_RESTORE_PARITY_FAILED`.

## Production scope

No Android or companion production code changes.

No APK build/install or companion restart required.

D5.4 core synchronization directions are now runtime validated. The remaining
work is sync trigger/UX and conflict/diagnostic polish before D5.4 closure.
