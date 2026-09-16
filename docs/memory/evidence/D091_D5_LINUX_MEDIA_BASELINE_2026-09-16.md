---
memory_schema: 1
as_of: 2026-09-16
status: diagnostic_validated
classification: D5_VOD_SYMLINK_HOST_RANGE_PATH_HEALTHY
---

# D5 Linux media baseline / external-VOD host boundary

Checkpoint:
`c7fe53a613d55f9d38b37b16609c590118465efd`

## Baseline audit

Read-only measurements:
- control status HTTP 200;
- sources HTTP 200;
- four root catalog categories;
- 91 dynamic VOD sources;
- VOD byte-range fixture available and passed with HTTP 206;
- diagnostics health HTTP 200;
- stream telemetry HTTP 200;
- Self-Test HTTP 200;
- IPTV categories HTTP 200.

Source audit:
- companion media root is fixed to project `media/`;
- dynamic media paths are confined beneath that selected root;
- Linux range server is launched using that project media root;
- `range_server.py` itself supports a generic `--root`;
- browser and camera runners remain PowerShell.

## External movie symlink probe

Current development setup contains one directory symlink beneath `media/vod`.

Representative movie measurement:
- symlink target resolves to a directory;
- direct read through symlink succeeded;
- direct read of resolved target succeeded;
- effective read access succeeded;
- target is on an externally mounted filesystem;
- exact symlinked movie path appears in `/sources`;
- one-byte HTTP Range through port 8000 succeeded;
- response status 206 with Content-Range.

Classification:
`D5_VOD_SYMLINK_HOST_RANGE_PATH_HEALTHY`.

## Interpretation

The current onn playback failure is not explained by:
- external disk readability;
- symlink traversal;
- catalog discovery/path generation;
- host-side HTTP Range serving.

The next diagnostic boundary is whether the onn sends the exact VOD request to
port 8000 during the failure.
