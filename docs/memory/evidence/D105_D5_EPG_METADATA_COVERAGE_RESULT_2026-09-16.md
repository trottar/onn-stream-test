# D-105 — D5 EPG metadata coverage result — 2026-09-16

**Status:** runtime validated diagnostic result

D-105 completed successfully against the onn TV database and current IPTV-org
metadata.

Measured:

- upstream guide rows: 180,681;
- unique guide channel IDs: 11,723;
- onn TV unique nonblank channel IDs: 3,286;
- exact metadata/catalog matches: 89;
- exact coverage: 2.7085%;
- English exact matches: 86;
- English exact coverage: 2.6172%;
- currently source-backed matched channels: 0;
- current public guide workers: 1 green / 3 red;
- channels on the green public worker: 2.

Largest guide-site coverage among the 89 matched catalog identities included
`sky.com` (41), `i.mjh.nz` (40), `freeview.co.uk` (34), `mytelly.co.uk` (30),
and `tvireland.ie` (27).

Interpretation:

Public hosted EPG is unavailable for the effective catalog, and guide metadata
exactly covers only a small fraction of the current catalog. A Linux-local EPG
grabber is therefore not justified yet as a broad solution.

The next diagnostic must separate:
- meaningful TV identities from synthetic `tv_stream_*` fallback IDs;
- built-in IPTV-org guide coverage from custom/managed-provider coverage.

D-106 owns that diagnostic.
