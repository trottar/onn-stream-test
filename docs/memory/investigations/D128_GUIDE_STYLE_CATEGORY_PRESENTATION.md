# D-128 — Guide-style category presentation

**Date:** 2026-09-17

**Status:** runtime failed / superseded by D-129

## Purpose

Attempt to make existing Favorites/category channel tiles more guide-like by
adding cached current/next programme time ranges.

## Development history

- Rev1 failed the Kotlin compile gate because a duplicate
  `formatTvGuideTime(Long)` member was inserted; installer rollback restored the
  predecessor.
- Rev2 corrected the transform, but the supplied Bash wrapper could terminate
  the interactive shell before installation.
- Rev3 passed the Android build but failed repository memory-health because the
  generated `CURRENT.md` omitted two required headings; installer rollback
  restored the predecessor.
- Rev4 corrected those deterministic failures, built, committed, pushed and was
  installed on the onn.

## Runtime result

Probe classification:

`D128_GUIDE_STYLE_ROWS_NOT_OBSERVED`

Counts were zero for visible Now rows, Next rows and marked-guide rows. Manual
inspection reported that the screen looked exactly like the previous UI: the
same button grid rather than an actual TV guide.

## Root cause

D-128 changed `tvChannelToNode()` text but did not change the rendering seam.
The shared source page remained a three-column `GridLayout`, and
`createSourceButton()` still rendered fixed-width channel controls. Therefore the
patch could not satisfy the intended one-column TV-guide UX even when guide text
was available.

## Resolution

D-129 supersedes this approach by changing TV result-page layout itself to a
one-column full-width guide list and by hydrating the Android guide cache from
already-warmed companion data before rendering.
