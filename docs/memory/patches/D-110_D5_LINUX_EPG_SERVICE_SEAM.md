# D-110 — D5 Linux EPG service seam

**Date:** 2026-09-16

**Type:** production-seam development patch / Linux runtime validation required

## Purpose

Move from D-109 viability proof to a persistent rebuildable Linux EPG
acquisition/cache service without changing Android yet.

## Production changes

- add `companion/plugins/epg.py`;
- register `EpgPlugin` in `companion/plugins/__init__.py`.

## Diagnostic changes

- add `tools/probes/d110_epg_plugin_runtime_probe.py`.

## Durable memory

Records:

- D-109 multi-site success;
- measured 77.42 second setup and 445,831,397 byte disposable tree;
- D-110 Linux EPG ownership/cache decision;
- D5.3 remains active until endpoint/cache runtime validation.

## Intentionally unchanged

- Android `TvEpgRepository`;
- Android TV UI/catalog/provider logic;
- TV state synchronization;
- companion control-server routing implementation;
- media/VOD;
- Games/controllers/video/audio;
- host package installation.

## Runtime outputs

- `logs/tv/d110_epg_plugin_runtime_probe.json`
- `logs/tv/d110_epg_plugin_runtime_probe.txt`
