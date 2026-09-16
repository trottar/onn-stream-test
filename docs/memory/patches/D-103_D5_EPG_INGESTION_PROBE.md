# D-103 — D5.2 EPG ingestion probe

**Date:** 2026-09-16
**Type:** diagnostic-only development patch
**Durable memory updated:** yes

Adds one read-only Linux diagnostic probe for the D5.2 EPG failure.

Changed:
- `tools/probes/d103_epg_ingestion_probe.py`;
- D5 current/handoff/roadmap/investigation memory;
- D-103 patch/investigation records.

Intentionally unchanged:
- Android production code;
- `TvEpgRepository`;
- `TvRepository`;
- companion runtime;
- VOD/Games/controller/video/audio paths;
- onn EPG and TV databases.

Installer note:
- initial D-103 delivery rolled back before commit because its daily-memory append
  created a blank line at EOF rejected by `git diff --check`;
- D-103R1 corrects only that installer behavior and adds a regression test.

Runtime acceptance is not claimed by installation. The next evidence is the fresh
`logs/tv/d103_epg_ingestion_probe.txt` result.

<!-- PRIVYHUB_D103R1_STAGED_WHITESPACE_REPAIR:PATCH -->
## D-103R1 staged-validation follow-up

The installer completed, but the first commit attempt was intentionally blocked
by `git diff --cached --check` because this record and the D-103 investigation
record contained Markdown trailing whitespace. The whitespace was corrected
before commit. Probe behavior was not changed.
