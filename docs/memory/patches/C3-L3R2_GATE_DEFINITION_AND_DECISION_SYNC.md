---
memory_schema: 1
as_of: 2026-09-19
baseline_commit: d7f8cd823b315899bad19cea4f395ea92593b64e
durable_memory_updated: true
---

# C3-L3R2 — gate definition and decision sync

## Purpose

`C3-L3R1` corrected the `C3.L3` data and wrote "`C3.L4` is BLOCKED; gate is a
focused gameplay acceptance" into six files **without opening
`decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`, the record that defines
that gate.** The next session read the phrase, proposed a manual-cycle
subjective read, and had to be told that `C3.L2` reason 3 already rejected
exactly that observation on 2026-09-18.

This patch fixes the gate, the decision record it lives in, and the two
workflow rules that let the drift happen. It also records the failure, per the
project's negative-result policy.

Durable memory only. No source, tool or probe change.

## Expected predecessor

`d7f8cd823b315899bad19cea4f395ea92593b64e`

Per-file SHA-256 is enforced by the installer.

## What the sweep found

A grep of `docs/memory/` for the falsified 287-318 ms figure and for
pre-`ANDROID-FLAT` Kotlin paths turned up four stale items, all in the same
two directories — `decisions/` and `investigations/` — and all traceable to
patches that updated status and evidence files and skipped those two.

1. **The decision record had not been touched since it was written**
   (2026-09-18 05:11). Its reason 1 still argues that the actuator inserts a
   ~290 ms discontinuity "nearly two orders of magnitude above the stream's
   own settled continuity". `C3.L2a` E2 falsified that the same day: 27 ms
   first IDR, complete, unrepaired, **nothing registered at the cycle**. The
   E2 patch's changed scope covered nine files and not `decisions/`.
2. **The gate was named and never defined.** Reason 3 says a single
   operator-initiated transition is not acceptance of an unannounced
   policy-initiated one — correct, and it never said what would be. Sessions
   have proposed the rejected observation twice.
3. **`investigations/ACTIVE.md` contradicted itself.** Its body recorded
   `C3.L2a` open and `C3.L2b` as code-installed-only; a section appended to
   the bottom recorded `C3.L2a` CLOSED. Append without curate.
4. **Two records named pre-flatten Kotlin paths** —
   `decisions/C3-L2_...:140` and `C3_LINUX_ACTUATOR_BOUNDARY.md:70-71` — which
   `ANDROID-FLAT` should have caught.

## Changed scope

Replaced:

- `docs/memory/decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md` — reason 1
  struck in place and marked falsified; reason 2 restated without a magnitude;
  "what this does not say" sharpened; stale Kotlin path corrected; consequences
  table superseded by a current one; new sections "Correction: reason 1's
  premise is falsified" and "The `C3.L4` gate, stated so it can be satisfied";
- `docs/memory/investigations/ACTIVE.md` — rewritten current; `C3.L3a`
  registered with its scope; superseded state compressed to a history note;
- `docs/memory/investigations/C3_LINUX_ACTUATOR_BOUNDARY.md` — stale Kotlin
  paths only; the 32 KB of history is otherwise untouched;
- `docs/memory/MEMORY.md` — the `C3.L2` durable block's falsified magnitude
  claim corrected; the gate definition added as a durable rule;
- `docs/memory/CURRENT.md` — work item becomes `C3.L3a`; "no perceptual
  quantity has been measured anywhere in Phase C" added to the incomplete list;
- `docs/memory/roadmap/STATUS.md` — `C3.L3a` row and active item; correction
  section;
- `docs/memory/PHASE_C_CONTEXT.md` — sub-phase row; new section 6b carrying the
  gate so the brief stays self-sufficient;
- `docs/memory/handoffs/CURRENT_HANDOFF.md` — next item is `C3.L3a`, with both
  non-satisfying proposals named; 2026-09-18 history compressed to keep the
  file inside its size budget;
- `docs/memory/AGENTS.md` — two rule corrections, below;
- `docs/memory/LEARNINGS.md` — two lessons;
- `docs/memory/2026-09-19.md` — dated record.

Added: this record. Generated: `docs/memory/patches/PATCH_INDEX.md`.

Unchanged: all source, all tools, all probe scripts, every evidence file, the
`C3.L2` classification itself, and every roadmap state except `C3.L4`'s gate
pointer.

## The classification is not reopened

`video_only_restart` stands. Manual, start-time, fallback and characterization
use authorized; automatic in-game adaptation not authorized. Reason 1 falling
does not weaken the block — a cheaper actuator than believed is not an argument
for firing it automatically, and reasons 2, 3 and 4 were never about cost.

## Two workflow rules corrected in `AGENTS.md`

- **The ZIP delivery step was written out of the rules.** `AGENTS.md` said
  "there is no ZIP-and-send-and-unzip step to describe — the response just
  gives the run command against the files already in place." That contradicts
  the user's twice-stated preference: the user runs the zip, the install and
  the push, deliberately. That line is the most likely reason an earlier
  session delivered off-pattern. Replaced with the ZIP-installer delivery as
  the standard, described as the control boundary it is.
- **The staging allowlist rule was right but underspecified.** "Never use broad
  `git add .`" is correct and stays. What was missing: an allowlist written
  from what the current patch touches leaves earlier uncommitted work behind.
  A memory-scoped allowlist left the runtime-validated `C3.L3` source changes
  uncommitted; the user found them in `git status`. The rule now says to derive
  the allowlist from `git status --short`, account for every path it prints,
  and end a checkpoint block with `git status --short` printing nothing.

## Negative results

- **The failure this patch fixes is the one `C3-L3R1` warned about, committed
  by `C3-L3R1`.** That record's own negative-results section says "Memory
  written from a session's own narrative rather than from the files on disk
  inverted a conclusion." It then wrote a gate definition from a summary. The
  rule was correctly identified and applied to numbers only.
- **Skipping `decisions/` is a repeat.** The `C3.L2a` E2 patch did it first, a
  day earlier, from the same session. Two occurrences, same directory, same
  cause: evidence and status files feel like the changed scope; decision files
  do not, and they are exactly where falsified premises survive.
- **The gate is defined, not satisfied.** Nothing here observes anything.
  `C3.L3a` is registered and unauthorized; its design has not been written.
- **The finalize matching defect is still not root-caused**, and the 385 ms
  gap in a spike-free session is still unexplained. Neither is touched here.
- **No evidence file is rewritten.** The measurements were never wrong; the
  conclusions drawn from them in `decisions/` were.

## Validation performed

- installer Python compile;
- payload and installed SHA-256 verification per file;
- predecessor SHA-256 enforced per file, with wrong-state rejection before any
  modification;
- generated index regenerated and verified against a fresh generation after
  writing, with both expected new records asserted present;
- LF line endings and trailing newline asserted on every written file;
- `tools/check_memory_health.py` as a post-write gate, with exact-byte rollback
  on failure;
- `CURRENT.md` re-measured against both soft limits, and
  `CURRENT_HANDOFF.md` brought back under its 8 KB soft limit by compressing
  superseded history that survives in `2026-09-18.md`;
- every remaining `com/safeiot/privyhub` reference in `docs/memory/` checked
  and confirmed to be historical description of the flattening, not a live
  path;
- ZIP integrity.

**Deliberately not performed:** no self-test, no synthetic fixture, no sandbox
install. Tier 1 per `patches/PATCH_PROTOCOL.md`.

No runtime validation applies; this patch changes no executable behavior.

## Privacy

No network addresses appear in this patch or in any file it writes.

## Result

Recorded on install.
