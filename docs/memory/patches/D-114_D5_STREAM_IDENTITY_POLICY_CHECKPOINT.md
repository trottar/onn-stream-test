# D-114 — D5 stream identity policy checkpoint

**Date:** 2026-09-16

**Type:** durable-memory / architecture-decision checkpoint

## Purpose

Close D-113 using measured evidence without introducing an over-broad production
heuristic.

## Recorded result

- D-113 runtime classification:
  `D113_CONFIRMED_UPSTREAM_STREAM_IDENTITY_CONTRADICTION`;
- 9 feed-name heuristic hits / 3,071 built-in rows;
- confirmed 10 Bold upstream/source identity defect;
- heuristic judged too noisy for generic automatic suppression.

## Decision

- no production `identity_suspect` heuristic from D-113;
- no hardcoded 10 Bold URL deny list;
- existing manual Hide is the safe current user action;
- manual-hidden state is durable user intent and belongs in D5.4 sync;
- EPG data path remains accepted.

## Scope

No Android or companion production code changes.

No runtime test is required beyond the already captured D-113 evidence.

Next development boundary: D5.4 Linux-authoritative TV user-state sync.
