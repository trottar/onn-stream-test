---
memory_schema: 1
as_of: 2026-10-28
baseline_commit: 42a2ab6
---

# B28 — `PRIVYHUB_REMOTE=1`: the four WAN lines, only on a remote-class session

**Result: SETTLED + BUILT; `tests/remote_umbrella` 10 green, every `tests/` suite green, 2 mutations caught; the replay
G4-S4 13 / 13 the same, the home LAN 16 / 16 today's; absent = today PROVEN; G-A9 PREPARED; no live run.** Record:
`evidence/B28_REMOTE_UMBRELLA_2026-10-28.md`. Diff: `evidence/b28_2026-10-28/b28.diff`. Nothing committed.

- **Settled:** as written, the four are not LAN-neutral:
  - `PRIVYHUB_START_RUNG=floor` starts a LAN session at **5000** (the LAN list's floor);
  - the ladder adds `path_class` to every row; the cap writes a config row;
  - the telemetry writes `wan_sessions` rows and the `wan` field.
- **Built:** `companion/remote_umbrella.py`.
  - At each stream start, before it, the class comes from B23's readers (the overlay address, then the provider's
    path).
  - **Remote** (direct / relayed / unknown): the umbrella's ladder, cap 7000, start rung `floor` and telemetry go
    into today's module globals: G4-S4's four.
  - **LAN:** the globals None (today's code path; the base ladder restored).
  - An explicit line wins; one `remote_config` row per session. `plugins/games.py` +12 (three guarded items).
- **Apply:** `git apply evidence/b28_2026-10-28/b28.diff` (the tree already carries it, uncommitted). It acts only
  with `PRIVYHUB_REMOTE=1` in the service's environment (G-A9, prepared).
- **Rollback:** no `PRIVYHUB_REMOTE` line (today); or revert the three files.
