---
memory_schema: 1
as_of: 2026-09-10
---

# PrivyHub repository and evidence policy

## Commit to Git

- production source and configuration;
- durable `docs/memory/` state;
- architecture, decisions, investigations, roadmap, handoff and patch history;
- reusable diagnostic/regression tools;
- small curated evidence;
- sanitized immutable checkpoint evidence snapshots.

## Keep local / out of Git

- ROMs, ISOs and other game/media content;
- saves, savestates and user profiles/runtime state;
- emulator/runtime installations and generated core options;
- ordinary logs, packet captures and large diagnostics;
- APK/build output, caches, archives and patch ZIPs;
- private ADB target cache, addresses, credentials and secrets;
- live `docs/memory/evidence/raw/`.

## Raw evidence snapshots

`docs/memory/evidence/raw/` is the authoritative local working-evidence store.
It is ignored by Git.

At a major checkpoint, a deterministic sanitized ZIP may be generated under
`docs/memory/evidence/snapshots/`. Each snapshot contains a manifest with the
relative path, byte size and SHA-256 of every included raw file.

Snapshot generation fails closed if:
- a raw file is too large for the checkpoint evidence policy;
- total uncompressed snapshot input exceeds the checkpoint policy;
- a network/device identifier or likely secret is detected.

The committed snapshot is historical checkpoint evidence. Continue writing new
working evidence to the ignored raw directory.
