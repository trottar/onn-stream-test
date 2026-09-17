# D-136 — Focused TV/media regression

**Date:** 2026-09-17
**Status:** regression gate active

## Purpose

Close the bounded post-D5 TV/EPG UX/performance sequence with the smallest
existing regression seam.

## Automated gate

Reuse `tools/probes/d122_d5_tv_media_regression_probe.py`, which checks:
- companion status;
- source catalog;
- EPG readiness;
- exact Linux/onn TV-state parity;
- sync diagnostic baseline.

D-136 additionally requires:
- D-133 guide status/layout acceptance;
- D-135 Favorites queue/contention acceptance.

## Manual smoke

The automated probe does not prove visible/audio playback. Repeat the established
short onn smoke:
1. play one Live TV channel;
2. browse Favorites/guide and confirm navigation/display remains normal;
3. play one VOD item.

If automated and manual checks are clean, D5 bounded TV/media work can close.
