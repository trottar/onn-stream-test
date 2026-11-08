# Queue T's APK — B5 … B25 + B32 + B34 + B35 + B38 + B39 + B41 + B42 + B43 + B46 + B47 + **B54**; B27 / B29 out

**`9aa00ba2afe19a7f36b869454d7d5e683185dc97fc116cc6f8f75878bc5fe73f`**, 9,702,680 B, 945 entries. Pinned at
`PrivyHub/app/build/queue_t_built/app-debug.apk`. **NOT installed.** `cfe0211c…` stays CONFIRMED.

- **How it was built:**
  1. the baseline's sources with queue T's combined diff applied (`/tmp/b_q12t_all`);
  2. `b29.diff` and `b27.diff` reversed on the client paths (`git apply -R --include='PrivyHub/*'`), as queue O;
  3. offline, `--rerun-tasks --no-configuration-cache`.
- **Its client sources vs `cfe0211c…`'s:** the same tree without queue T (HEAD's client, B29 / B27 reversed) differs
  in exactly B54's six client files (`apk_source_diff.txt`).
- **That tree rebuilds `cfe0211c…` byte for byte** (`cfe0211ca360…a65f`, the pinned queue O file), so this build
  reproduces the CONFIRMED APK; the new APK's only source change is B54.
- **A second build of the new APK gives the same bytes** (`9aa00ba2…`, twice).
- `apksigner verify`: Verifies (v2); the signer's certificate SHA-256 is the same as `cfe0211c…`'s.
- JVM in the APK copy: **217 / 217** (B27 / B29's tests out, as queue O's 217).
