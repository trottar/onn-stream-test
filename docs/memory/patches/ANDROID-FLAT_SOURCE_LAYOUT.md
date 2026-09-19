---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 986490b46f701b1131e88897a56a0c667f22b361
durable_memory_updated: true
---

# ANDROID-FLAT — flatten the Android source directory layout

## Purpose

Remove the reversed-domain package directories from the Android source tree.
Every Kotlin file moves from `PrivyHub/app/src/main/java/com/safeiot/privyhub/`
up into `PrivyHub/app/src/main/java/`, keeping the `diagnostics/` and
`streaming/` subdirectories.

The chain is inherited Java convention. This app has no Java sources, Kotlin
does not require directory/package agreement, and the three levels cost
something on every interaction with the client code.

File locations only. No Kotlin content is edited and no package declaration
changes.

## Expected predecessor

`986490b46f701b1131e88897a56a0c667f22b361`

Memory files are verified by per-file SHA-256. The move plan is verified
structurally at install time: every expected source must exist, be `.kt`, and
have an unoccupied destination.

## Changed scope

Moved, 19 files:

- `PrivyHub/app/src/main/java/com/safeiot/privyhub/*.kt` → `.../java/*.kt`
  (7 files, including `MainActivity.kt`, `TvRepository.kt`, `TvEpgRepository.kt`);
- `.../privyhub/diagnostics/*.kt` → `.../java/diagnostics/*.kt` (4 files);
- `.../privyhub/streaming/*.kt` → `.../java/streaming/*.kt` (6 files);
- the two example test sources under `app/src/androidTest/java/` and
  `app/src/test/java/`.

Removed: the emptied `com/safeiot/privyhub`, `com/safeiot` and `com`
directories in all three source sets.

Replaced:

- `docs/memory/TOOLS.md` — Android source layout section;
- `docs/memory/MEMORY.md` — durable layout fact;
- `docs/memory/2026-09-18.md` — dated record;
- `docs/memory/investigations/C3_LINUX_ACTUATOR_BOUNDARY.md` — the only two live
  references to the old paths.

Added: this record. Generated: `docs/memory/patches/PATCH_INDEX.md`.

## Intentionally unchanged scope

All Kotlin file content and package declarations. All companion and tool source.
`app/build.gradle.kts`, `AndroidManifest.xml`, `settings.gradle.kts`,
`.gitignore`. `CURRENT.md`, `PHASE_C_CONTEXT.md`, `roadmap/STATUS.md`, the
handoff notes, every decision and evidence record. The roadmap does not move:
`C3.L2b` remains the next item and becomes ordinarily reachable once this lands.

## Why this is safe, and where it fails closed

- **Java would break; the installer refuses it.** Java requires
  package-matching directories. The installer scans all three source sets and
  returns `FAILED BEFORE MODIFICATION` if it finds any `.java` file. Today there
  are none.
- **Kotlin does not require the match.** Package declarations are left exactly
  as they are, so no source content changes and no import anywhere else needs
  touching.
- **Gradle still finds the files.** `app/build.gradle.kts` declares no custom
  `sourceSets`, so `src/main/java` remains the source root and the files are
  still inside it.
- **Identity is independent of layout.** `namespace` and `applicationId` are
  `com.safeiot.privyhub` in `build.gradle.kts`; `AndroidManifest.xml` names
  activities by fully-qualified class name. Neither reads the directory tree.
- **A dirty tree is refused.** Rollback restores paths, so the installer returns
  `FAILED BEFORE MODIFICATION` if `git status` shows uncommitted tracked changes
  under `PrivyHub/`.
- **The real build is the gate.** `sh ./gradlew :app:assembleDebug --no-daemon`
  runs after the moves. On failure every file is moved back to its exact
  original path, the directories are restored, and the result is `ROLLED BACK`.
- **History is preserved.** Moves use `git mv` where the file is tracked, so
  `git log --follow` continues to work.

## Known consequences

- Android Studio will show a "package directive does not match file location"
  inspection on these files, with a quick-fix that moves them back. Declining it
  is recorded in `TOOLS.md` and `MEMORY.md`.
- Patch `git add` allowlists and any probe that names a source path must use the
  flat paths from now on. The installer scans `companion/`, `tools/` and
  `scripts/` for scripts still naming `com/safeiot/privyhub` and prints them as
  a warning rather than failing, since a match may be a historical string.
- Records written before 2026-09-18 keep the old paths. They are history and are
  not rewritten.

## Negative results

- No attempt was made to flatten `app/src/main/java` itself into something
  shorter; that would need a custom `sourceSets` entry and buys one level for
  added configuration.
- Test sources are moved for consistency even though they are two example files;
  leaving them nested would have preserved the exact inconsistency this patch
  exists to remove.
- The installer cannot prove the build in advance. Gradle runs on the target
  machine, and its failure path is exercised in the self-test with a stub
  `gradlew` that exits non-zero.

## Validation performed

- installer Python compile;
- installer self-test against synthetic git fixtures: Java refusal, dirty-tree
  refusal and wrong memory pre-state each returning `FAILED BEFORE MODIFICATION`
  with a byte-identical snapshot before and after; clean install; sources
  verified flattened with the package chain removed; every relocated source
  asserted at most 7 folders deep; package declarations asserted untouched;
  backups written; idempotent reinstall changing nothing; forced validation
  failure and a failing Gradle build each returning `ROLLED BACK` with every
  source restored to its original path; stale-reference scan detecting a seeded
  probe;
- memory payload and installed SHA-256 verification;
- generated index correctness;
- LF line endings and trailing newline preserved;
- ZIP integrity.

The Gradle build itself runs on the target machine as an installer gate. No
runtime validation of the app is claimed by this patch; a normal Games launch
after install is the confirmation.

## Result

Recorded on install.
