# B5 incident: the first gradle run in the copy built the TREE's project (build outputs only; restored)

- **What happened (05:3xZ):**
  - `sh ./gradlew --offline :app:testDebugUnitTest --rerun :app:assembleDebug` was run in `/tmp/b_q22c/PrivyHub`.
  - Gradle reported "Configuration cache entry reused". The configuration cache under `PrivyHub/.gradle/`, copied
    with the project, carries the tree's absolute paths.
  - So the build compiled and tested **the tree's** `PrivyHub/app` sources. The compiler warning cites the tree's
    `NativeStreamActivity.kt:3586`, the predecessor's line (`incident_first_build_console.txt`).
- **What it changed in the tree:** only gitignored build outputs.
  - 312 files under `PrivyHub/app/build/` and `PrivyHub/.gradle/file-system.probe`.
  - `PrivyHub/app/build/outputs/apk/debug/app-debug.apk` went from `043891e1…1607` (CL-B5's build, also kept at
    `app/build/cl_b7_preserved/`) to `583e0f52…` (HEAD's source rebuilt).
  - **No source changed** (`git status PrivyHub` empty). Nothing was installed; there was no adb.
  - `cl_b7_preserved/` (`043891e1…`) and `cl_b7_installed/` (`93d29b4a…`) were not touched.
- **Restored:**
  - The copy was taken (`cp -a`) just before the build, so it held the pre-build bytes.
  - **All 289 overwritten files were copied back, each verified byte-equal (`cmp`).** The tree's APK reads
    `043891e1…` again.
  - **24 files the build newly created** (dex / class / test-report files for B3's and CL-B7P's classes, which the
    stale build dir had never compiled) **are left in place**, because nothing is deleted. They are listed in
    `incident_tree_new_files.txt`. All are gitignored build intermediates, and Gradle re-validates them on the
    tree's next build.
- **The rule this touched:** "the `/tmp/b_*` copy holds companion/, tools/, tests/, PrivyHub/ only". No rule on
  units was touched: only the companion was active (`build_started_at.txt`).
- **The fix for every later build in the copy:** `--no-configuration-cache`. After each build, a `find` over the
  tree's `PrivyHub/` for files newer than a marker must be empty, and the copy's outputs must show the copy's sources
  (the new test class in the copy's results).
