# D-109 — D5 EPG portable-Node grabber probe

**Date:** 2026-09-16

**Type:** diagnostic-only development patch

## Purpose

Continue the D-108 local EPG acquisition viability test without installing
Node/npm on the Linux appliance.

## Changes

- adds `tools/probes/d109_epg_portable_node_grabber_probe.py`;
- records D-108's environment-only runtime result;
- adds the D-109 investigation;
- updates current/handoff/roadmap/architecture/daily durable memory.

## Portable dependency

Official Node.js v24.21.0 runtime is downloaded only during the probe,
verified against pinned SHA-256, and deleted afterward.

## Intentionally unchanged

- host package installation;
- shell profiles/environment outside the probe subprocess;
- Android production code;
- companion production code;
- TV playback/catalog behavior;
- TV-state synchronization;
- VOD;
- Games/controllers/video/audio.

## Runtime output

- `logs/tv/d109_epg_portable_node_grabber_probe.json`
- `logs/tv/d109_epg_portable_node_grabber_probe.txt`

D-108 output is also refreshed by the subprobe when the portable runtime is
usable.
