# D-127 — Durable incorrect-guide intent and deferred recheck

<!-- PRIVYHUB_D128:D127_ACCEPTANCE:BEGIN -->
## Runtime result — accepted

Classification:

`D127_INCORRECT_GUIDE_DURABILITY_CONFIRMED`

Observed one marked Android channel with exact Linux durable-state match,
`manual_hidden = 0`, `auto_hidden = 0`, rejected source key present, mark
timestamp present and no problems.

D-127 is closed/runtime validated. D-128 proceeds as a separate Android
presentation-only change.
<!-- PRIVYHUB_D128:D127_ACCEPTANCE:END -->

**Date:** 2026-09-17

**Status:** development patch / runtime validation pending

## Narrow question

How can a user reject an incorrect programme guide without hiding a playable
channel, while preventing the same rejected guide from immediately returning as
trusted data and still allowing later controlled recheck?

## Pre-state

- Linux is already the durable authority for TV user intent.
- Android owns its local TV/EPG SQLite caches and UI.
- D-125 makes normal companion guide misses non-blocking.
- D-126 warms Favorites and visible pages.
- Linux EPG guide responses already include source provenance (`site`,
  `site_id`, `language`).
- Existing durable state v1 has no incorrect-guide field.

## D-127 contract

Per stream, durable state v2 adds:

- `guide_incorrect`;
- `rejected_guide_source_key`;
- `guide_incorrect_at_ms`.

The source key is a stable fingerprint, not a raw provider URL.

`guide_incorrect` is independent of `manual_hidden`, `auto_hidden`, playback
health and Favorites.

## Presentation behavior

While marked incorrect:

- the channel remains queryable/visible/playable;
- cached current-program text is omitted from channel tiles;
- opening Program Guide presents the incorrect-guide state, not programme rows;
- normal EPG cache/acquisition data is retained so a later recheck can compare
  against it.

## Recheck behavior

- normal D-126 prefetch excludes marked channels;
- after the mark is at least 24 hours old, a bounded background recheck may use
  the existing companion prefetch seam;
- background recheck never clears durable user intent;
- explicit Retry performs a fresh guide refresh;
- Retry may discover the same or a different source, but neither is trusted
  automatically;
- the user explicitly accepts the refreshed guide or keeps the mark;
- Clear Mark always remains available.

## Schema migration

Android exports `privyhub_tv_user_state_v2`. The Android sync client fails
closed on legacy authority responses; local repository import remains v1/v2
capable for migration compatibility. Linux accepts v1 only when reading its
existing persisted authority, canonicalizes that state to v2, and rejects v1
client writes.

The predecessor v1 hash is verified before migration; the migrated v2 hash is
then persisted.

## Explicit non-goals

D-127 does not:

- hide channels because a guide is wrong;
- change transport-health classification;
- invent fuzzy EPG remapping heuristics;
- change Linux EPG candidate selection;
- redesign guide/category pages;
- add multi-client merge semantics.

## Runtime acceptance

Use a visible/playable channel with a known bad guide. Confirm UI suppression,
playback independence, restart/sync durability and explicit Retry/Accept/Clear.
Then run:

`python3 tools/probes/d127_incorrect_guide_probe.py`

Expected durable-state classification while marked:

`D127_INCORRECT_GUIDE_DURABILITY_CONFIRMED`
