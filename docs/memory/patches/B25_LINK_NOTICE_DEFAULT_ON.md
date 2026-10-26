---
memory_schema: 1
as_of: 2026-10-26
baseline_commit: da48629
---

# B25 — the client's `link_notice` on by default (`0` off); APK `fcd924c2…` pinned, NOT installed

**Result: BUILT; JVM 4 new (150 / 150); `0` = today PROVEN; the replay MET (3 / 3 sessions on 2.4 GHz shown, 0 / 42
on 5 GHz); NOT ADOPTED; no live run.** Record: `evidence/B25_LINK_NOTICE_DEFAULT_ON_2026-10-26.md`. Nothing committed.

- **Built:** `LinkNoticeFlag.parse`: on unless `0` (absent / empty / junk → on); a failed read → on. B14's
  conditions, wording, once-a-session rule and 30-s clear are unchanged. The activity and the diagnostics page are
  byte-identical (they already follow the flag).
- **Host:** no change. `PRIVYHUB_LINK_REPORT=1` (G-A3, adopted) already records the key and the
  `link_notice_shown` / `_cleared` rows.
- **APK** (B5 + B7 + B10 + B11 + B13 + B14 + B15 + B16 + B17 + B18 + B19 + B22 + B25)
  `fcd924c28cbf70a85bb9a886caabcb07873eee2d028b6538284fce5a7ae39b96`, 9,638,234 B. Same signer as `6bddafc0…`; only
  `classes3.dex` differs.
- **Files:** `LinkNotice.kt` (the flag object only); `LinkNoticeDefaultOnTest.kt` (new); the flag lines in
  `LinkNoticeTest.flagTable` and `ClientDefaultsTest.absentIsOnAndZeroIsOff` moved.
- **Apply:** `git apply evidence/b25_2026-10-26/b25.diff` (the tree already carries it, uncommitted).
- **Rollback:** `setprop debug.privyhub.link_notice 0`; or revert the flag object (two lines).
