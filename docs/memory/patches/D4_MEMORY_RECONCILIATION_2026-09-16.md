---
memory_schema: 1
as_of: 2026-09-16
patch: D4_MEMORY_RECONCILIATION_2026-09-16
durable_memory_updated: true
---

# D4 memory reconciliation — 2026-09-16

Purpose: reconcile durable memory with the newer D4 Linux debug session,
Repo Audit Outline findings, and the temporary Windows/ExpressVPN routing
follow-up before the next source checkpoint.

Changed memory scope:

- `docs/memory/CURRENT.md`
- `docs/memory/MEMORY.md`
- `docs/memory/handoffs/CURRENT_HANDOFF.md`
- `docs/memory/investigations/ACTIVE.md`
- `docs/memory/investigations/DEFERRED.md`
- `docs/memory/2026-09-16.md`
- `docs/memory/evidence/D4_LINUX_RUNTIME_RECONCILIATION_2026-09-16.md`
- `docs/memory/investigations/EXPRESSVPN_WINDOWS_BRIDGE_2026-09-16.md`
- this patch record

Intentional non-scope:

- no production source changes;
- no Android/Kotlin changes;
- no Python runtime changes;
- no network configuration changes;
- no roadmap rewrite in this checkpoint.

Installer policy:

- structural preflight against the live local memory tree;
- exact live pre-write SHA-256 values captured to the backup receipt;
- byte-for-byte backups before modification;
- marked-block idempotence for existing memory files;
- exact-content validation for new memory files;
- `git diff --check` on the changed memory scope;
- automatic rollback on post-write validation failure.

GitHub was used only as a reference predecessor because the project-local tree
may contain unpushed changes. The installer therefore preserves live local
content and inserts/replaces only uniquely marked reconciliation blocks.
