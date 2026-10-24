# B16 (host) — the flags absent = HEAD efa4240

| file | B16 items removed | the module's AST then = HEAD's |
| --- | --- | --- |
| `companion/plugins/games.py` | 1: `if getattr(self._recovery, '_stall_owner', None) is not None: |     payload['stall_resume'] = self._recovery._stall_owner.client_hint()` | **identical** |

`companion/stall_owner.py` (B12's module, imported only with the flag): +34 −3, listed:

```diff
--- a/companion/stall_owner.py
+++ b/companion/stall_owner.py
@@ -17,0 +18,11 @@
+
+B16 (the same flag; design `docs/memory/evidence/b16_2026-10-24/design_written_before_code.md`, hashed before this
+code). CL-B10 cell 3: the client's gate held the picture 1.3-3.2 s after the downlink's return (four 500-ms gate ticks),
+v2's hold expired first in all 5, and blackout 5's restart acted on a heartbeat built before the return; cell 2 saved
+state at four 150-ms client stalls. Here:
+- the start response tells the client to send its ready as soon as it has a decodable frame (`client_hint`); the host
+  resumes on it through the owners above (B12's `client_ready_stall`, B8's `client_ready_hold`);
+- the stall's save comes only from the stall signal (age >= its threshold, 400 with `1`), synchronously before B7's
+  pause (B9 skips a paused core): no save under the 400-ms signal;
+- v2 takes a stall-owned pause past 5 s only while the newest stall datagram (<= 300 ms old) shows the client still
+  stalled.
@@ -28,0 +40 @@
+NEWEST_S = 0.30             # B16: the newest stall datagram describes the client now (B7's quiet rule: 300 ms)
@@ -50,0 +63,2 @@
+        self._newest: tuple[float, int] = (0.0, 0)   # B16: the newest stall datagram (receive time, output age)
+        self._threshold_ms = 400                 # B16: the stall signal's threshold (B7's, set per datagram)
@@ -70,0 +85,2 @@
+        self._newest = (rx, int(age))           # B16: what the client says now (v2's rule)
+        self._threshold_ms = int(threshold_ms)
@@ -79 +95,2 @@
-        if state == "PLAYING" and not self._saved_episode and not gate:
+        # B16: the save only from the stall signal (age >= its threshold), taken now, before B7's pause below
+        if state == "PLAYING" and not self._saved_episode and not gate and age >= threshold_ms:
@@ -84 +101,4 @@
-                cores.request_save(rx - float(age) / 1000.0, rx, "stall")
+                try:
+                    cores.save(rx - float(age) / 1000.0, rx, "stall")
+                except Exception:
+                    pass                        # the pause must never wait on a failed save
@@ -141,0 +162,5 @@
+    @staticmethod
+    def client_hint() -> dict[str, Any]:
+        """B16: the start response's `stall_resume`: the client's ready as soon as it has a decodable frame."""
+        return {"fast_ready": True}
+
@@ -151,0 +177,5 @@
+            return True
+        # B16: v2 takes it only while the newest stall datagram shows the client still stalled (never on a heartbeat
+        # read before the return; a client with frames sends its ready within ~0.55 s)
+        rx, last_age = self._newest
+        if not (now - rx <= NEWEST_S and last_age >= self._threshold_ms):
@@ -171 +201,2 @@
-                  state_save=bool(getattr(getattr(rw, "b9", None), "mode", None) == "state"))
+                  state_save=bool(getattr(getattr(rw, "b9", None), "mode", None) == "state"),
+                  fast_ready=True, save_from_signal=True, v2_newest_s=NEWEST_S)
```

Result: **PROVEN** (the plugin byte for byte without the flags; the module is not imported without them — `tests/stall_owner` `test_not_imported_absent`).
