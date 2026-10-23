# B13 (client) — what changed in LinkReport.kt (vs HEAD 3eb900c)

The intended change, stated: the property's default. `parse`: `== "1"` became `!= "0"`; `fromSystem`'s failure path: `false` became `parse(null)` (on). The doc comment says so. Nothing else in the client changed for B13 (the activity's `linkSampler` already follows `fromSystem()`; NativeStreamActivity.kt untouched by B13).

```
- * property `debug.privyhub.link_report=1` (CL-B7P's convention; a reboot
- * clears it). Absent = today: no Wi-Fi read, no new key.
+ * property `debug.privyhub.link_report` (CL-B7P's convention; a reboot
+ * clears it). B13: absent (or anything but `0`) = ON; `0` turns it off.
-    fun parse(value: String?): Boolean = value?.trim() == "1"
+    fun parse(value: String?): Boolean = value?.trim() != "0"   // B13: on unless `0`
-    /** The property, read through reflection; any failure is off. */
+    /** The property, read through reflection; a failed read is absent, so on (B13). */
-            false
+            parse(null)
- * B3: the Wi-Fi link report. The flag (absent = off), the validity rules, the
+ * B3: the Wi-Fi link report. The flag (B13: absent = on, `0` = off), the validity rules, the
-        assertFalse(LinkReportFlag.parse(null))
-        assertFalse(LinkReportFlag.parse(""))
+        // B13: on by default; only `0` turns it off
+        assertTrue(LinkReportFlag.parse(null))
+        assertTrue(LinkReportFlag.parse(""))
-        assertFalse(LinkReportFlag.parse("true"))
+        assertFalse(LinkReportFlag.parse(" 0 "))
+        assertTrue(LinkReportFlag.parse("true"))
-    fun noAndroidPropertyIsOff() {
-        assertFalse(LinkReportFlag.fromSystem())
+    fun noAndroidPropertyIsOn() {
+        assertTrue(LinkReportFlag.fromSystem())                   // B13: a failed read is absent, so on
```
