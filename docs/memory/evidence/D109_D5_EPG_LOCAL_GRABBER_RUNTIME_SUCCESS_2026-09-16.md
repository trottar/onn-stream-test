# D-109 — D5 EPG local-grabber runtime success — 2026-09-16

**Status:** runtime validated diagnostic result

D-109 successfully supplied a temporary official Node runtime and reran the
D-108 local-grabber test without installing Node/npm on the Linux appliance.

## Portable runtime

- host architecture: x86_64;
- Node: 24.21.0;
- npm: 11.19.0;
- official archive download: successful;
- pinned SHA-256 verification: successful;
- extraction: successful;
- runtime cleanup after test: successful.

## Upstream EPG toolchain

Pinned upstream commit:

`78e94adb76841a63d94a53e80dbd0d52bb7c2c5c`

Measured refreshed D-108 setup:

- exact built-in English guide rows: 3,920;
- usable metadata rows: 3,920;
- configured candidate sites: 91;
- dependency/toolchain setup: 77.42 seconds;
- disposable upstream tree after setup: 445,831,397 bytes.

## Multi-site programme acquisition

All three representative source grabs succeeded:

- `i.mjh.nz` / `10Bold.au@Sydney`
  - 8.351 seconds;
  - 33 programmes;
  - 33 within the current/upcoming 48-hour window.
- `pluto.tv` / `5Cops.us@UK`
  - 6.987 seconds;
  - 32 programmes;
  - 29 within the current/upcoming 48-hour window.
- `plex.tv` / `24HourFreeMovies.us@SD`
  - 7.01 seconds;
  - 1 programme;
  - 1 within the current/upcoming 48-hour window.

Classification:

`D109_PORTABLE_NODE_LOCAL_GRABBER_VIABLE_MULTI_SITE`

## Architectural conclusion

Linux-local EPG acquisition is technically viable across multiple independent
guide sites.

The reference grabber is too expensive to clone/install afresh for each guide
request: setup is approximately 77 seconds and the disposable dependency tree
is approximately 446 MB.

For Prototype-1 the next coherent seam is therefore:

- persistent but rebuildable EPG tooling under ignored `data/`;
- no system Node/npm dependency;
- lazy/explicit bootstrap rather than companion-startup blocking;
- positive programme caching;
- companion plugin API as the client boundary.

This conclusion does not yet accept Android EPG integration. D-110 first
runtime-validates the Linux service/cache seam.
