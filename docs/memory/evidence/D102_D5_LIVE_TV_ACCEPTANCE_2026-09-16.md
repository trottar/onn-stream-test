---
memory_schema: 1
as_of: 2026-09-16
baseline_commit: 53fd9b176647bad324a9fdae4d4f04b2f62e43a4
evidence_status: runtime_observed
---

# D102 D5 Live TV acceptance — 2026-09-16

## Observed on onn

`TV -> TV Settings -> Catalog / EPG Status` reported:

- Language: English
- Country: All Countries
- Streams: 3356
- Favorites: 22
- Reliable: 49
- Hidden: 4
- Enabled providers: 3
- Catalog refreshed: Sep 16, 2026 3:55:38 PM
- EPG mappings: 2
- Cached programmes: 0

Normal Live TV categories/navigation were present and normal channel playback
worked.

The Program Guide action exists and executes, but no tested channel had actual
guide schedule data.

## Classification

`D5_LIVE_TV_CATALOG_PLAYBACK_ACCEPTED`

`D5_EPG_DATA_NOT_ACCEPTED`

This evidence does not validate EPG ingestion or programme matching. It also does
not validate TV state synchronization, which is an accepted architecture
direction but remains unimplemented.

## Next evidence required

A diagnostic-only EPG ingestion probe must retain raw stage counts sufficient to
challenge its classifier:
- total upstream guide entries;
- entries with channel IDs;
- entries with sources;
- entries with supported XML sources;
- accepted mappings;
- accepted mappings matching current TV channel IDs;
- XMLTV fetch results;
- programme records matching the selected channel identity.
