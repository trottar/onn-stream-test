# B19 — `0` = today

- `StallSignal.kt`: changed only inside `object StallSignalFlag` (and its doc comment): **yes**; +10 −5.
- `RestartGuard.kt`: changed only inside `object RestartGuardFlag` (and its doc comment): **yes**; +5 −3.

| flag | old `parse(absent)` | new `parse("0")` |
| --- | --- | --- |
| `StallSignalFlag` | null | null |
| `RestartGuardFlag` | false | false |

The values are asserted by `StallSignalTest.flagTable`, `RestartGuardTest.flagTable` and `ClientDefaultsTest` (`tests_jvm.txt`).

**The tests' moved lines (absent = off → absent = on, `0` = off):**
```diff
--- a/StallSignalTest.kt
+++ b/StallSignalTest.kt
@@ -30,2 +30,3 @@
-        for (bad in listOf(null, "", "0", "120", "2001", "on", "-5", "150ms")) {
-            assertNull(bad, StallSignalFlag.parse(bad))
+        // B19: absent / empty / junk = on at 150; only `0` turns it off
+        for (on in listOf(null, "", "120", "2001", "on", "-5", "150ms")) {
+            assertEquals(on, 150L, StallSignalFlag.parse(on))
@@ -32,0 +34,2 @@
+        assertNull(StallSignalFlag.parse("0"))
+        assertNull(StallSignalFlag.parse(" 0 "))
@@ -36,2 +39,2 @@
-    fun noAndroidPropertyIsOff() {
-        assertNull(StallSignalFlag.fromSystem())
+    fun noAndroidPropertyIsOn() {
+        assertEquals(150L, StallSignalFlag.fromSystem())        // B19: a failed read is absent, so on
--- a/RestartGuardTest.kt
+++ b/RestartGuardTest.kt
@@ -29,2 +29,3 @@
-        for (bad in listOf(null, "", "0", "on", "2")) {
-            assertFalse(bad, RestartGuardFlag.parse(bad))
+        // B19: on unless `0`
+        for (on in listOf(null, "", "on", "2")) {
+            assertTrue(on, RestartGuardFlag.parse(on))
@@ -32 +33,2 @@
-        assertFalse(RestartGuardFlag.fromSystem())
+        assertFalse(RestartGuardFlag.parse("0"))
+        assertTrue(RestartGuardFlag.fromSystem())
--- a/RestartGuardAllPathsTest.kt
+++ b/RestartGuardAllPathsTest.kt
@@ -280 +280 @@
-        assertFalse(RestartGuardFlag.fromSystem())
+        assertFalse(RestartGuardFlag.parse("0"))                 // B19: `0` is today's off
--- a/RestartGuardAudioOrderTest.kt
+++ b/RestartGuardAudioOrderTest.kt
@@ -156 +156 @@
-        assertFalse(RestartGuardFlag.parse(null))
+        assertFalse(RestartGuardFlag.parse("0"))                 // B19: `0` is today's off
```

Result: **PROVEN**.
