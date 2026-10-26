# B25 proof: `0` is today's absent

- 1. `streaming/NativeStreamActivity.kt` identical to the predecessor: **True** (sha256 e20f30e8b73a…)
- 1. `diagnostics/DiagnosticsActivity.kt` identical to the predecessor: **True** (sha256 4bd94f60004c…)
- 2. `LinkNotice.kt`: 11 changed lines, 7 of them comments; the 4 code lines:
  - `-    fun parse(value: String?): Boolean = value?.trim() == "1"`
  - `+    fun parse(value: String?): Boolean = value?.trim() != "0"`
  - `-            false`
  - `+            parse(null)`
  all inside `object LinkNoticeFlag` (the parse and the catch): **True**
  (`object LinkNoticeFlag` spans lines 17-31 of the new file)
  everything after the flag object (the text, the status, the rule, the query) identical: **True**

- 3. The parse table (Kotlin's `trim()` = Python's `strip()` on these values):

| value | B14 | B25 |
| --- | --- | --- |
| None | off | on |
| '' | off | on |
| ' ' | off | on |
| '1' | on | on |
| ' 1 ' | on | on |
| '0' | off | off |
| ' 0 ' | off | off |
| 'on' | off | on |
| 'true' | off | on |
| '2' | off | on |

  new(`0`) = B14's absent (off), `1` and `0` unchanged: **True**; a failed read: B14 off, B25 `parse(null)` = on

- 4. The flag's uses in the main sources (unchanged lines; with `0` each takes B14's absent branch):
  - `diagnostics/DiagnosticsActivity.kt:291` `if (LinkNoticeFlag.fromSystem()) {`
  - `streaming/NativeStreamActivity.kt:2436` `private val linkNotice: LinkNotice? by lazy { if (LinkNoticeFlag.fromSystem()) LinkNotice() else null }`
  `linkNotice` null → no view, no tick, no `&link_notice=` fragment (`linkNotice?.query() ?: ""`), no report keys; the diagnostics line not added.

**PROVEN**
