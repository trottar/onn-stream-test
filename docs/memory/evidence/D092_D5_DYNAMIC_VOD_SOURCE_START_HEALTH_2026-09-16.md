---
memory_schema: 1
as_of: 2026-09-16
status: diagnosed
classification: D5_DYNAMIC_VOD_SOURCE_START_HEALTH_REJECTS_EXTERNAL_SYMLINK
---

# D5 dynamic VOD source-start health diagnosis

Checkpoint:
`c7fe53a613d55f9d38b37b16609c590118465efd`

Prior host evidence:
- representative external movie readable;
- exact catalog path present;
- port-8000 one-byte Range request returned HTTP 206.

D-091 onn request-boundary result:
`D5_VOD_ONN_NO_MEDIA_REQUEST`.

Android logcat supplied the missing preceding event:
- `Failed to start source ...`;
- HTTP 503 from companion;
- error `VOD source is unavailable`;
- active source remained null.

Source root cause:
`_vod_is_healthy()` uses scanner `_filesystem_path`, resolves it, and applies
blanket resolved containment under project `MEDIA_ROOT`. Symlinked external VOD
therefore fails health despite being validly scanner-discovered and HTTP-served.

D-092 expected correction:
dynamic scanner sources validate the safe lexical catalog path and exact
scanner-recorded resolved target, while static VOD preserves resolved-root
containment.
