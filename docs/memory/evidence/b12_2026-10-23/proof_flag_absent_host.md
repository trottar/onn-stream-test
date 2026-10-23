# B12 (host) — against HEAD 3eb900c (predecessors/)

| file | B12 items removed | tuples set back | whole module vs predecessor |
| --- | --- | ---: | --- |
| `companion/games/link_drop_recovery.py` | 2: `_stall_owner: Any = None`; `if self._stall_owner is not None and self._stall_owner.holds_v2(self, now):` | 0 | **identical** |
| `companion/stall_signal.py` | 2: `if getattr(self.recovery, '_stall_owner', None) is not None and self.recovery._stall_owner`; `if getattr(self.recovery, '_stall_owner', None) is not None and self.recovery._stall_owner` | 0 | **identical** |
| `companion/plugins/games.py` | 4: `_stall_owner = None`; `if (os.environ.get('PRIVYHUB_STALL_RESUME') or '').strip() and _stall_signal is not None:`; `if _stall_owner is not None:`; `if _stall_owner is not None and self._recovery._stall_owner is not None:` | 0 | **identical** |
| `companion/hold_rewind.py` | 1: `if raw == 'rewind':` | 2 | **identical** |

Result: **ALL IDENTICAL** (beyond the stated tuples).

`companion/rewind_cores.py` (B9's module; not imported without PRIVYHUB_INPUT_HOLD_REWIND): 24 changed lines, all listed:

```
-- `1`: RetroArch's rewind **only for the allow-list** (snes9x, bsnes). Another core gets no rewind keys in its launch
-  config (Beetle PSX HW: no 1-GB buffer, no +16.6 points) and a `rewind_skipped` row at the release;
+- `1` (B12): `state` for every core (BENCH-R3: the rewind method read PAUSED after on snes9x and PS1; `state` played);
+- `rewind` (B9's `1`): RetroArch's rewind **only for the allow-list** (snes9x, bsnes). Another core gets no rewind keys
+  in its launch config (Beetle PSX HW: no 1-GB buffer, no +16.6 points) and a `rewind_skipped` row at the release;
+STALL_MATCH_S = 0.10        # B12: a stall save and the stall pause estimate the same client frame (receive - age)
-    return {"1": "allow", "all": "all", "state": "state"}.get(raw)
+    return {"1": "state", "rewind": "allow", "all": "all", "state": "state"}.get(raw)   # B12: `1` = state
-    def request_save(self, silence_start: float, now: float) -> None:
-        self._q.put((silence_start, now))
+    def request_save(self, silence_start: float, now: float, kind: str = "silence") -> None:
+        self._q.put((silence_start, now, kind))
-    def save(self, silence_start: float, mark_at: float) -> None:
+    def save(self, silence_start: float, mark_at: float, kind: str = "silence") -> None:
-            self.last_save = {"onset": silence_start, "sent_at": sent_at, "wall": wall, "ack": ack, "ok": ok}
+            self.last_save = {"onset": silence_start, "sent_at": sent_at, "wall": wall, "ack": ack, "ok": ok,
+                              "kind": kind}
-        self.recovery._log("state_saved" if ok else "state_save_failed", slot=SLOT, core=self.core(),
+        self.recovery._log("state_saved" if ok else "state_save_failed", slot=SLOT, core=self.core(), kind=kind,
+        # B12: a save taken at the client's stall matches the stall pause's own onset within 100 ms
+        if s is not None and s.get("kind") == "stall" and abs(s["onset"] - onset) <= STALL_MATCH_S:
+            onset = s["onset"]
-        if det is not None:
+        if det is not None and hasattr(det, "on_quiet"):
```
