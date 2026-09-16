# D-110 — D5 Linux EPG acquisition/cache service seam

**Status:** development patch / runtime validation next

## Purpose

Convert the D-109 local-grabber proof into the smallest Linux production seam
without changing Android yet.

## Scope

D-110 adds a companion `epg` plugin. It uses the companion's existing generic
plugin routing rather than adding another HTTP server or protocol.

Endpoints:

- `GET /plugins/epg/status`
- `GET /plugins/epg/guide?channel_id=<canonical-id>`
- `POST /plugins/epg/bootstrap`
- `POST /plugins/epg/refresh?channel_id=<canonical-id>`

## Runtime ownership

Rebuildable runtime state lives under ignored:

`data/epg/`

The plugin does not install Node/npm system-wide.

Toolchain contract:

- official portable Node 24.21.0;
- pinned official Linux x64/arm64 SHA-256;
- pinned upstream `iptv-org/epg` commit
  `78e94adb76841a63d94a53e80dbd0d52bb7c2c5c`;
- 1.25 GB free-space bootstrap preflight;
- staging setup followed by replacement of the active toolchain only after
  verification;
- upstream `.git` history and npm download cache removed after successful setup;
- final toolchain footprint recorded in the runtime manifest/status.

## Startup behavior

Plugin construction is side-effect free.

Companion startup therefore does not wait for EPG setup.

Bootstrap can be:

- explicit through `POST /plugins/epg/bootstrap`; or
- started in a daemon thread after an uncached guide request finds the toolchain
  not ready.

An unready guide request fails soft and reports `toolchain_preparing`.

## Identity and mapping

D-110 preserves the exact D-107 feed-aware identity contract:

- channel only -> `channel`;
- feed present -> `channel@feed`.

No fuzzy matching is introduced.

Guide metadata is cached for 24 hours.

Candidate rows must:

- exactly match the canonical channel ID;
- contain nonblank `site` and `site_id`;
- have a corresponding configured upstream site grabber in the pinned toolchain.

English rows and the higher-coverage D-107/D-109 sites are preferred.

Up to three configured sources may be attempted for one channel.

## Programme cache

Positive guide results are cached for 6 hours.

Negative results are cached for 30 minutes.

Cached data remains available as stale fallback when refresh fails.

Programme output keeps the D5 window:

- 2 hours past;
- 48 hours future;
- maximum 120 programmes per channel.

## D-110 runtime acceptance

After companion restart:

1. `/plugins/epg/status` exposes the expected schema;
2. bootstrap succeeds or an existing matching toolchain is recognized;
3. two D-109 representative channels return nonempty programmes;
4. a second request for the first channel returns from cache;
5. runtime status reports the resulting persistent toolchain footprint.

Android EPG integration is intentionally deferred to D-111 after this Linux
boundary is runtime validated.
