# D-104R2 — D5.3 EPG GZIP source support

**Date:** 2026-09-16
**Type:** Android production compatibility patch + diagnostic update
**Durable memory updated:** yes

## Purpose

Repair the first D-103 EPG divergence without broadening D5 scope.

Installer history:
- D-104 rolled back before build/commit/push/APK install because its deterministic
  Kotlin validator searched for literal escaped newline characters;
- D-104R1 corrected that validator, then rolled back before commit/push/APK
  install because `PrivyHub/gradlew` is tracked as non-executable mode `100644`;
- D-104R2 preserves that mode and invokes the wrapper through `sh ./gradlew`.

The intended Android EPG compatibility change is unchanged across revisions.

The first D-104 installer attempt rolled back before build, commit, push, or
APK installation because a deterministic post-patch token assertion searched
for literal `\\n` characters instead of a real Kotlin line break. D-104R2
fixes that installer-only defect. The intended Kotlin change is unchanged.

## Production changes

`TvEpgRepository`:
- prefer valid `XML` guide sources;
- otherwise accept valid `GZIP` guide sources;
- detect gzip by the `1f 8b` byte signature;
- decompress compressed XML before the existing XMLTV parser;
- store mapping-source parser version `2` in EPG meta;
- require the current parser version before honoring the 24-hour mapping cache.

This means the existing 2-row cache refreshes automatically after the upgraded
app first requests a guide.

## Diagnostic changes

D-103 is updated to reproduce the post-D-104 XML/GZIP mapping rules and report:
- selected XML entries;
- selected GZIP entries;
- supported mapping count;
- subsequent catalog/programme boundary classification.

## Intentionally unchanged

- JSON guide parsing;
- exact `channelId` / `siteId` programme matching;
- TV catalog/provider logic;
- favorites/history/hidden state;
- Linux TV-state sync implementation;
- companion IPTV adapter;
- VOD/Games/controller/video/audio paths.

## Validation contract

D-104R2 additionally shares one structural Kotlin validator between installer
self-test and post-write validation so this class of assertion drift is tested
before delivery.

Installer must:
- verify exact D-103 predecessor commit/blob state;
- preserve unrelated untracked `_patches/` and `_probes/`;
- back up every touched tracked file;
- apply each Kotlin replacement exactly once;
- install the updated D-103 probe;
- compile/self-test the Python probe;
- run `git diff --check`;
- run `./gradlew :app:assembleDebug --no-daemon`;
- verify the debug APK exists;
- roll back exact tracked bytes/new files on any post-write failure.

Runtime acceptance is separate:
install APK on onn, open Program Guide once, then rerun D-103.
