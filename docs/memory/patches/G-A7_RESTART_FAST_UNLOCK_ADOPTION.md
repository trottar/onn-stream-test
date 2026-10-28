---
memory_schema: 1
as_of: 2026-10-27
status: APPLIED (session A, G-A7; the user's decision 2026-10-27 "Go", after CL-B14). Written by A in G-A5's applied form (no patch was prepared by B)
---

# G-A7 — `PRIVYHUB_RESTART_FAST_UNLOCK=1`, the twelfth adopted line

Task: `handoffs/G-A7_RESTART_FAST_UNLOCK_ADOPTION_TASK.md`. Measured in
`evidence/CL_B14_RESTART_UNLOCK_AND_NOTICE_DEFAULT_2026-10-26.md` (every row R1-R7 met at four Home returns; the picture
back 1.15-1.86 s; CL-B13 with G-A5 alone 1.74-3.12 s). Built in B24 (`evidence/B24_RESTART_FAST_UNLOCK_2026-10-26.md`).
Record: `evidence/G_A7_RESTART_FAST_UNLOCK_ADOPTION_2026-10-27.md`.

**What it changes:** `tools/e1_suite.py` defines `RESTART_FAST_UNLOCK` and puts it in `ADOPTED` (twelve); the preflight
reads `drop_in_restart_fast_unlock` and requires it in `ok`. `tools/e3_state.py`, `tools/e1_remote.py`,
`tools/test_e1_remote.py`: wording only. `ADOPTED_E3` (`tools/d7_regression.py`, `tools/c3_l4_nft_night.py`) is left as
it is, as at G-A2..G-A5.

**The drop-in** (written separately, not by this diff):
`~/.config/systemd/user/privyhub-companion.service.d/restart-fast-unlock.conf`

```
[Service]
Environment=PRIVYHUB_RESTART_FAST_UNLOCK=1
```

**Off:** delete `restart-fast-unlock.conf`, `systemctl --user daemon-reload`, `systemctl --user restart
privyhub-companion`, and reverse this diff (`e3_state.py` then reads ok on eleven). The host then runs G-A5's worker
(CL-B13 cell 1). The flag acts only inside the adopted `PRIVYHUB_RESTART_FAST=1`, on a guarded start; no client change.

**Predecessor sha256 (HEAD 2cd392c):**

```
79c588f207ed7734bc8fd8d13a900b3372771227e09f98795dd9d5ebe829d65a  tools/e1_remote.py
5928cad1ae4251ca528b99f0881f65104b9164a1a107ef08668a20f5622ed156  tools/e1_suite.py
0b2c33b665a0ab8667a6323a3833e1b503600985926afe8b27148d9294ba27ca  tools/e3_state.py
36dd4b85f519bcdae8678669980e0e11f7517c624b26c75884c2808bda6e420c  tools/test_e1_remote.py
```

**The diff** (`git apply -p1`):

```diff
diff --git a/tools/e1_remote.py b/tools/e1_remote.py
--- a/tools/e1_remote.py
+++ b/tools/e1_remote.py
@@ -165,7 +165,7 @@
 
 def preflight_remote(environ_has: Callable[[str], bool], adb_devices: Callable[[], str],
                      adopted: tuple[str, ...] | list[str] = ()) -> dict[str, Any]:
-    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, eleven lines since G-A5); each must be read back too
+    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, twelve lines since G-A7); each must be read back too
     need = list(REQUIRED_FLAGS) + [kv for kv in adopted if kv not in REQUIRED_FLAGS]
     d = {
         "flags": {kv: environ_has(kv) for kv in need},
diff --git a/tools/e1_suite.py b/tools/e1_suite.py
--- a/tools/e1_suite.py
+++ b/tools/e1_suite.py
@@ -103,8 +103,13 @@
 # the client released at the new stream's first fresh frame (B22; acts only on a guarded start) -- through its own
 # drop-in (restart-fast.conf); the adopted environ is exactly these eleven names
 RESTART_FAST = "PRIVYHUB_RESTART_FAST=1"
+# G-A7 (adopted 2026-10-27, the user): the fast restart unlocked -- the ready at the new encoder's check, the old audio's
+# stop after it outside the lock (the capture SIGKILLed at 300 ms), the relay stopped before the old encoder's kill
+# (B24; acts only on a guarded start, inside RESTART_FAST) -- through its own drop-in (restart-fast-unlock.conf); the
+# adopted environ is exactly these twelve names
+RESTART_FAST_UNLOCK = "PRIVYHUB_RESTART_FAST_UNLOCK=1"
 ADOPTED = sorted([LIVE, INDEX, SNES_CORE, RECOVERY, SNES_CAPTURE, OVERLAY, IDENTITY, AUDIO_CODEC, LINK_REPORT,
-                  LINK_RECOVERY, RESTART_FAST])
+                  LINK_RECOVERY, RESTART_FAST, RESTART_FAST_UNLOCK])
 FLAG_NAMES = ["PRIVYHUB_ADAPTIVE_BITRATE_INJECT", "PRIVYHUB_ADAPTIVE_BITRATE_TOP", "PRIVYHUB_PS1_LOOK",
               "PRIVYHUB_NATIVE_PROFILE_ID", "PRIVYHUB_FEC_SCHEME"]
 RA_CFG = Path.home() / ".config/retroarch/config"
@@ -1007,11 +1012,12 @@
          "drop_in_link_report": f"Environment={LINK_REPORT}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_link_recovery": f"Environment={LINK_RECOVERY}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_restart_fast": f"Environment={RESTART_FAST}" in sh(["systemctl", "--user", "cat", UNIT]),
+         "drop_in_restart_fast_unlock": f"Environment={RESTART_FAST_UNLOCK}" in sh(["systemctl", "--user", "cat", UNIT]),
          "e3_dropin_absent": not DROPIN.exists(), "e4_constraint_absent": not E4_DROPIN.exists()}
     d["ok"] = (d["manager"] == [] and d["environ"] == ADOPTED and d["adb"] and d["drop_in_live"] and d["drop_in_index"]
                and d["drop_in_snes_core"] and d["drop_in_recovery"] and d["drop_in_snes_capture"] and d["drop_in_overlay"]
                and d["drop_in_identity"] and d["drop_in_audio_codec"] and d["drop_in_link_report"]
-               and d["drop_in_link_recovery"] and d["drop_in_restart_fast"]
+               and d["drop_in_link_recovery"] and d["drop_in_restart_fast"] and d["drop_in_restart_fast_unlock"]
                and d["e3_dropin_absent"] and d["e4_constraint_absent"])
     return d
 
diff --git a/tools/e3_state.py b/tools/e3_state.py
--- a/tools/e3_state.py
+++ b/tools/e3_state.py
@@ -1,5 +1,5 @@
 #!/usr/bin/env python3
-"""E3: the adopted state (since G-A5, eleven: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report, the link-recovery stack, the fast restart; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
+"""E3: the adopted state (since G-A7, twelve: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report, the link-recovery stack, the fast restart, the fast restart unlocked; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
 import sys, json, importlib.util
 spec=importlib.util.spec_from_file_location('s','/home/privyhub/Projects/onn-stream-test/tools/e1_suite.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
 mp=m.mainpid()
diff --git a/tools/test_e1_remote.py b/tools/test_e1_remote.py
--- a/tools/test_e1_remote.py
+++ b/tools/test_e1_remote.py
@@ -133,7 +133,7 @@
         self.assertTrue(pf["adb_device"])
 
     def test_the_adopted_set_is_required_too(self):
-        # G-A2: the callers pass e1_suite.ADOPTED (eleven lines since G-A5); one missing refuses, naming it
+        # G-A2: the callers pass e1_suite.ADOPTED (twelve lines since G-A7); one missing refuses, naming it
         adopted = ("PRIVYHUB_AUDIO_CODEC=opus", R.REQUIRED_FLAGS[0])
         pf = R.preflight_remote(lambda kv: kv in R.REQUIRED_FLAGS, lambda: "", adopted)
         self.assertFalse(pf["ok"])
```
