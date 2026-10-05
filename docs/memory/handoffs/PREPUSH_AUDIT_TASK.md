---
memory_schema: 1
as_of: 2026-10-05
status: TASK HANDOFF — PREPUSH: read-only audit of everything committed since the remote's main, before the user's push — the commit list, the redactor over every tracked file those commits touched, a check that no ignored-category file is tracked, the push size, one report. No code change, no session, no git write (no fetch, no push)
---

# PREPUSH — audit before the user's push

**Why.** The user is pushing after many local commits (C3.L4 close
through C5-CLOSE-A). "Push only after local state is proven"
(`docs/ROADMAP.md`, Checkpoint discipline). Code reads; the user pushes.

**Read-only git only**: `git log`, `git diff`, `git ls-files`,
`git show`, `git rev-parse`, `git status`. **No `git fetch`, no `git
push`, no `git add`, no commit.** If `origin/main` is unknown locally,
say so and audit from the last pushed ref the reflog shows, or from the
first commit after `824c9d9` if nothing better is recorded; name the
range used.

## 1. The report — `logs/prepush_audit_<date>.txt` and `evidence/PREPUSH_AUDIT_<date>.md`

- **The range**: `origin/main..HEAD` (or the substitute), the commit
  count, each commit's hash and subject, and the working tree's
  `git status --short` (expected: only `_cowork_prompt.txt` after this
  task is read, or clean).
- **Files**: `git diff --stat origin/main..HEAD`; the count of files
  added, modified, deleted; the total size of added/modified tracked
  files; the five largest.
- **The redactor** (`docs/memory/evidence/h2_prep_2026-09-22/h2_prep_redact.py
  --check`) over **every tracked text file in the range** (added or
  modified), plus a separate grep over the same set for private IPv4
  ranges, MAC addresses, the SSID pattern, the ADB `connect` form with an
  address, `serial`, `password`, `token`, `secret`, `BEGIN ... KEY`. List
  every hit with file and line; classify each as the known false
  positives (loopback, the any-address bind, the core version string,
  the RFC 5737 documentation address in the live suite's route tests)
  or as a finding. **A finding stops the report with STOP and the exact
  file and line**, so the user can fix it before pushing.
- **Ignored categories**: `git ls-files` filtered for `*.apk`, `*.pem`,
  `*.key`, keystores, `.env*`, `*.state*`, `*.srm`, `*.sav`, anything
  under `logs/`, `runtime/`, `data/`, `games/`, `media/`, `cache/`, any
  file > 20 MB, any `*.mkv` / `*.mp4` / `*.png` over 1 MB. Expected
  none; list any.
- **Memory health**: `python3 tools/check_memory_health.py` output.
- **The verdict line**: `READY TO PUSH` or `STOP: <reason>`.

## 2. Memory

The daily file: one line. `CURRENT.md`: Next Action 1 becomes the
user's push (`git push`), 2 the user's go for Phase E. Nothing else
changes. `git status --short` to the report's end.

No addresses, MACs, SSIDs, ADB endpoints, serials or credentials in the
report itself (hits are cited by file and line, redacted). Nothing
adopted. Nothing committed. Nothing pushed.
