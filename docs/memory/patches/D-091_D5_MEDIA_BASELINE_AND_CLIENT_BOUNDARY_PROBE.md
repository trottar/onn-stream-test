---
memory_schema: 1
as_of: 2026-09-16
patch: D-091_D5_MEDIA_BASELINE_AND_CLIENT_BOUNDARY_PROBE
durable_memory_updated: true
---

# D-091 D5 media baseline and client request-boundary probe

Purpose:
record validated D5 baseline/symlink evidence and add one read-only diagnostic
for the next unresolved onn playback boundary.

Production behavior changed:
none.

Installed diagnostic:
`tools/probes/d091_vod_client_request_boundary.py`

Required predecessor runtime evidence:
- `logs/d5_linux_media_baseline_audit.txt`
- `logs/d5_vod_symlink_playback_probe.txt`

Preserved conclusions:
- host-side external-VOD path through HTTP Range is healthy;
- symlink remains temporary and does not replace configurable-media-root design;
- browser/camera PowerShell runners remain separate Linux seams.

Next:
reproduce one exact onn VOD failure and inspect sanitized new port-8000 request
records.
