# D-122 — D5.4 focused TV/media regression gate

**Status:** diagnostic/manual regression active

## Purpose

D-121 completes the sync-specific runtime acceptance work.

D-122 is the final D5.4 closure gate. It verifies that the mature media paths
remain healthy after the TV-state synchronization work.

## Scope

Automated/read-only:

- companion `/status`;
- companion `/sources`;
- EPG plugin ready;
- Linux TV-state authority initialized;
- exact Linux/onn durable-state parity;
- last successful pull metadata current;
- D-121 conflict diagnostics retained.

Manual onn smoke test:

1. top-level TV opens normally and normal categories/navigation are present;
2. one known-good Live TV channel produces video and audio;
3. Program Guide opens on a channel with guide data and shows real schedule rows;
4. one existing VOD item opens and plays normally;
5. returning/back navigation remains normal;
6. TV Settings -> Catalog / EPG Status still displays TV-state revision,
   last sync, and conflict information.

## Excluded

Do not reopen:

- browser/camera runner work;
- external-VOD architecture;
- stream-identity heuristic work;
- Games/controller/video/audio architecture.

Those are outside this focused regression unless a new regression is actually
observed.
