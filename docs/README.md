# PrivyHub documentation

This directory records architectural decisions, known limitations, experiments, and acceptance criteria that should survive individual development chats and temporary patch packages.

## Documents

- **PROJECT_STATUS.md** — current prototype architecture and stable/deferred areas.
- **KNOWN_ISSUES.md** — issues that should remain visible without blocking unrelated work.
- **DIAGNOSTICS.md** — diagnostic inventory and the repeatable transport acceptance suite.
- **REPOSITORY_AUDIT_2026-09-07.md** — source/reproducibility audit for this checkpoint.
- **investigations/2026-09-07-udp-transport.md** — detailed evidence from the game-audio UDP investigation.

## Documentation rule

When an experiment is deliberately deferred, record:

1. the symptom;
2. what was actually measured;
3. what was ruled out;
4. what remains unresolved;
5. the exact condition that should cause the investigation to resume;
6. the diagnostic tools needed to resume without repeating old work.

Avoid documenting private network addresses, MAC addresses, device GUIDs, credentials, ROM filenames, or other environment-specific secrets.
