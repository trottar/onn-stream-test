---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: 7f3f71d
---

# G-A4 — `PRIVYHUB_LINK_RECOVERY=1` as the tenth adopted line: PREPARED, NOT APPLIED

**Status: PREPARED by session B (B20); nothing applied.**
- No drop-in was written, the tree's adoption lists are unchanged, and the companion was not restarted.
- **Adopting it is the user's say-so, after CL-B12.** Session A applies it as G-A4 (§3).
- Record: `evidence/B20_LINK_RECOVERY_UMBRELLA_2026-10-24.md`.

**What it adopts:** the link-recovery stack, as one line. `PRIVYHUB_LINK_RECOVERY=1` implies exactly:
- `PRIVYHUB_INPUT_HOLD=1`, `PRIVYHUB_INPUT_HOLD_B6=1`, `PRIVYHUB_INPUT_HOLD_B8=1`;
- `PRIVYHUB_INPUT_HOLD_REWIND=1`, `PRIVYHUB_STALL_SIGNAL=1`, `PRIVYHUB_STALL_RESUME=1`.

That is the input hold (B2 / B6), the hold's ownership at the return (B8), the `state` path (B9 / B12) and no save at
the session's end (B18), the client's stall signal (B7) and the stall resume with the fast ready (B12 / B16).
- An explicit individual line still wins (`…=0` turns one part off).
- The client half is on by default from APK `20e3e339…` (B19). Nothing needs setting on the onn.
- **The measured cost (CL-B11):**
  - a 4-s drop holds the picture 4.13-4.47 s and restores 24-26 frames;
  - one save per real stall;
  - (B18) no save at a session's end.

## 1. The drop-in (NOT written)

`~/.config/systemd/user/privyhub-companion.service.d/link-recovery.conf`:

```
[Service]
Environment=PRIVYHUB_LINK_RECOVERY=1
```

## 2. The tools (NOT applied to the tree; the diff made and tested on a scratch copy)

| # | file | edit |
| --- | --- | --- |
| 1 | `tools/e1_suite.py` | `LINK_RECOVERY` defined and in `ADOPTED` (**ten**); the preflight's `drop_in_link_recovery` and its `ok` term |
| 2 | `tools/e3_state.py` | the docstring ("since G-A4, ten"); its logic is e1_suite's. B20 already prints `link_recovery` (the six as they will act) whenever the service's environ carries the line |
| 3 | `tools/e1_remote.py` | the comment ("ten lines since G-A4"); `preflight_remote` already requires every adopted line it is passed |
| 4 | `tools/test_e1_remote.py` | the comment |

- **Not edited, as with G-A1 to G-A3:** `tools/d7_regression.py` and `tools/c3_l4_nft_night.py` keep their older
  `ADOPTED_E3` lists of three names. The G-A1 to G-A3 lines never entered them either.
- **The six implied lines are not adoption lines.** They live in the companion process's own environment, not in its
  `/proc` environ. So the preflight's `environ == ADOPTED` stays exact, with ten names.

**Tested on the scratch copy, before / after** (`evidence/b20_2026-10-24/ga4_tests_before_after.txt`):
- `e1_suite --self-test` OK on both sides;
- `len(ADOPTED)` 9 → 10;
- `test_e1_remote` 21 and `test_c3_l4_nft_night` 33, with the same one error / failure on both sides (their fixtures
  live under `docs/`, absent from a tools-only copy; CL-B11 recorded 21 OK / 33 OK from the tree);
- `git apply --check -p1` OK against the tree.

```diff
diff -ru before/tools/e1_remote.py after/tools/e1_remote.py
--- before/tools/e1_remote.py	2026-10-23 14:23:18.318133201 -0400
+++ after/tools/e1_remote.py	2026-10-24 12:11:22.187571988 -0400
@@ -165,7 +165,7 @@
 
 def preflight_remote(environ_has: Callable[[str], bool], adb_devices: Callable[[], str],
                      adopted: tuple[str, ...] | list[str] = ()) -> dict[str, Any]:
-    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, nine lines since G-A3); each must be read back too
+    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, ten lines since G-A4); each must be read back too
     need = list(REQUIRED_FLAGS) + [kv for kv in adopted if kv not in REQUIRED_FLAGS]
     d = {
         "flags": {kv: environ_has(kv) for kv in need},
diff -ru before/tools/e1_suite.py after/tools/e1_suite.py
--- before/tools/e1_suite.py	2026-10-24 11:36:21.381685456 -0400
+++ after/tools/e1_suite.py	2026-10-24 12:11:22.187571988 -0400
@@ -88,7 +88,12 @@
 # G-A3 (adopted 2026-10-23, the user): the client's Wi-Fi link fields recorded in the heartbeat (B3; diagnostics only, no
 # behaviour) through its own drop-in (link-report.conf); the adopted environ is exactly these nine names
 LINK_REPORT = "PRIVYHUB_LINK_REPORT=1"
-ADOPTED = sorted([LIVE, INDEX, SNES_CORE, RECOVERY, SNES_CAPTURE, OVERLAY, IDENTITY, AUDIO_CODEC, LINK_REPORT])
+# G-A4 (adopted <date>, the user): the link-recovery stack -- PRIVYHUB_LINK_RECOVERY=1 implies its six lines (B20: the
+# input hold, B6, B8, the state path, the stall signal, the stall resume) -- through its own drop-in
+# (link-recovery.conf); the adopted environ is exactly these ten names
+LINK_RECOVERY = "PRIVYHUB_LINK_RECOVERY=1"
+ADOPTED = sorted([LIVE, INDEX, SNES_CORE, RECOVERY, SNES_CAPTURE, OVERLAY, IDENTITY, AUDIO_CODEC, LINK_REPORT,
+                  LINK_RECOVERY])
 FLAG_NAMES = ["PRIVYHUB_ADAPTIVE_BITRATE_INJECT", "PRIVYHUB_ADAPTIVE_BITRATE_TOP", "PRIVYHUB_PS1_LOOK",
               "PRIVYHUB_NATIVE_PROFILE_ID", "PRIVYHUB_FEC_SCHEME"]
 RA_CFG = Path.home() / ".config/retroarch/config"
@@ -989,10 +994,12 @@
          "drop_in_identity": f"Environment={IDENTITY}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_audio_codec": f"Environment={AUDIO_CODEC}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_link_report": f"Environment={LINK_REPORT}" in sh(["systemctl", "--user", "cat", UNIT]),
+         "drop_in_link_recovery": f"Environment={LINK_RECOVERY}" in sh(["systemctl", "--user", "cat", UNIT]),
          "e3_dropin_absent": not DROPIN.exists(), "e4_constraint_absent": not E4_DROPIN.exists()}
     d["ok"] = (d["manager"] == [] and d["environ"] == ADOPTED and d["adb"] and d["drop_in_live"] and d["drop_in_index"]
                and d["drop_in_snes_core"] and d["drop_in_recovery"] and d["drop_in_snes_capture"] and d["drop_in_overlay"]
                and d["drop_in_identity"] and d["drop_in_audio_codec"] and d["drop_in_link_report"]
+               and d["drop_in_link_recovery"]
                and d["e3_dropin_absent"] and d["e4_constraint_absent"])
     return d
 
diff -ru before/tools/e3_state.py after/tools/e3_state.py
--- before/tools/e3_state.py	2026-10-24 12:09:58.585740339 -0400
+++ after/tools/e3_state.py	2026-10-24 12:11:22.187571988 -0400
@@ -1,5 +1,5 @@
 #!/usr/bin/env python3
-"""E3: the adopted state (since G-A3, nine: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
+"""E3: the adopted state (since G-A4, ten: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report, the link-recovery stack; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
 import sys, json, importlib.util
 spec=importlib.util.spec_from_file_location('s','/home/privyhub/Projects/onn-stream-test/tools/e1_suite.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
 mp=m.mainpid()
diff -ru before/tools/test_e1_remote.py after/tools/test_e1_remote.py
--- before/tools/test_e1_remote.py	2026-10-23 14:23:18.318133201 -0400
+++ after/tools/test_e1_remote.py	2026-10-24 12:11:22.187571988 -0400
@@ -133,7 +133,7 @@
         self.assertTrue(pf["adb_device"])
 
     def test_the_adopted_set_is_required_too(self):
-        # G-A2: the callers pass e1_suite.ADOPTED (nine lines since G-A3); one missing refuses, naming it
+        # G-A2: the callers pass e1_suite.ADOPTED (ten lines since G-A4); one missing refuses, naming it
         adopted = ("PRIVYHUB_AUDIO_CODEC=opus", R.REQUIRED_FLAGS[0])
         pf = R.preflight_remote(lambda kv: kv in R.REQUIRED_FLAGS, lambda: "", adopted)
         self.assertFalse(pf["ok"])
```

## 3. G-A4 for session A (only on the user's say-so, after CL-B12 meets its rows)

1. `e3_state.py` ok on nine; `git apply -p1` the diff above; `e1_suite --self-test`, `test_e1_remote`,
   `test_c3_l4_nft_night` from the tree.
2. Write `link-recovery.conf` (§1). Then `systemctl --user daemon-reload` and restart the companion **outside
   04:30-05:30Z** (the nightly watch).
3. `e3_state.py` ok on **ten**, with its `link_recovery` key showing the six as `implied 1`. The recovery log's
   `link_recovery_config` row (`implied`: the six) appears at the first stream.
4. One 10-min E1 SNES confirmation window with every client property empty. Expect:
   - the six modules' config rows;
   - `stall_resume_config` `fast_ready` true;
   - zero `state_saved` outside a drop;
   - at the window's end, `session_end_bye` → `state_save_skipped` client_bye.
5. **Rollback:** remove `link-recovery.conf`, daemon-reload, restart, and `e3_state.py` ok on nine.
