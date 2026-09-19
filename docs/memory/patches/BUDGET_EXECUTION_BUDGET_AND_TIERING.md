---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 288c656df8137c3dc272600470a84a89532e7fa1
durable_memory_updated: true
---

# BUDGET — execution budget and patch tiering

## Purpose

Stop sessions from spending 20-25 minutes and a large share of the user's
budget building sandbox validation for patches whose real gates run on the
user's machine anyway.

## Expected predecessor

`288c656df8137c3dc272600470a84a89532e7fa1`

## Changed scope

Replaced:

- `docs/memory/AGENTS.md` — execution budget section;
- `docs/memory/patches/PATCH_PROTOCOL.md` — two-tier rule, and an explicit
  instruction not to re-prove the installer's gates;
- `docs/memory/2026-09-18.md` — dated record.

Added: this record. Generated: `docs/memory/patches/PATCH_INDEX.md`.

Unchanged: all source, all other memory, the roadmap. `C3.L2c` remains the next
work item.

## The rule

Plan in three lines. Stop and ask beyond 10 file reads, 15 commands or one
deliverable. Never build installer self-tests, synthetic fixtures, stub
compilers or mock frameworks to pre-validate. "Memory" means `docs/memory/`,
not assistant memory.

Tier 1 — an ordinary change the build or the health checker validates: payload,
per-file predecessor SHA-256, a plain installer, the copy/paste block. Default;
covers almost everything.

Tier 2 — a structural change with no compile-time check, where a mistake is
silent. `ANDROID-FLAT` and `STREAMLINE` are the only two in this repository.

## The precedent problem, stated plainly

The patch records written on 2026-09-18 — `C3-L2`, `C3-L2A-E1`, `C3-HO`,
`ANDROID-FLAT`, `STREAMLINE`, `C3-L2A-E2` — list synthetic fixtures, stub
compilation and 17-to-21-check self-tests under "Validation performed". A
session told to match the recent records reproduces that cost on work that does
not need it.

Both edited files now say those records are not the model. This is a correction
to the repository's own example, not to any individual session's judgement.

## Negative results

- The rule was proposed twice in conversation and never written down, so two
  sessions had no way to know it. A rule that lives only in a chat message does
  not exist.
- One session answered a question about limits by reading assistant memory
  instead of `docs/memory/`. The repository never stated which one it meant.
- No earlier patch is rewritten. The records stay accurate about what they did;
  only their status as an example changes.

## Validation performed

- installer Python compile;
- payload and installed SHA-256 verification;
- generated index correctness;
- LF line endings and trailing newline on every written file;
- `tools/check_memory_health.py` as a post-write gate, with exact-byte rollback
  on failure.

**Deliberately not performed:** no self-test, no synthetic fixture, no sandbox
install. This patch is Tier 1 and follows its own rule. The predecessor hashes
and the health gate decide it on the user's machine.

No runtime validation applies; this patch changes no executable behavior.

## Result

Recorded on install.
