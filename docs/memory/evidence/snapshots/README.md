# Checkpoint evidence snapshots

This directory contains sanitized, immutable compressed snapshots of the local
working evidence stored under `docs/memory/evidence/raw/`.

The live `raw/` directory is intentionally ignored by Git. Each snapshot has a
sidecar manifest with per-file SHA-256 and byte size. Snapshot creation is
fail-closed on privacy or size-policy violations.
