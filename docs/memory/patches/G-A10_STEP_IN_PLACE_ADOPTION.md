---
memory_schema: 1
as_of: 2026-11-02
status: APPLIED (session A, G-A10; the user's decision 2026-11-02 "Adopt", after HOME-1 C2). Written by A in G-A7's applied form (no patch was prepared by B)
---

# G-A10 — `PRIVYHUB_STEP_IN_PLACE=1`, the fourteenth adopted line

Task: `handoffs/G-A10_STEP_IN_PLACE_ADOPTION_TASK.md`. Measured in
`evidence/HOME_1_TRIP_CLOSE_AND_QUEUE_L_CELLS_2026-11-02.md` C2: both steps `in_place: true`, `ssrc_unchanged: true`,
splice 0.9 / 6.1 ms, no SSRC change and no stall at the client, against today's 235 / 428-ms gaps for the same steps
(C3). Built in B32's host half (`evidence/B32_SURFACE_HOLD_AND_STEP_IN_PLACE_2026-10-31.md`, `companion/step_in_place.py`).
Record: `evidence/G_A10_STEP_IN_PLACE_ADOPTION_2026-11-02.md`.

**What it changes:**
- `tools/e1_suite.py` defines `STEP_IN_PLACE` and puts it in `ADOPTED`, making fourteen. The preflight reads
  `drop_in_step_in_place` and requires it in `ok`.
- `tools/e3_state.py`, `tools/e1_remote.py`, `tools/test_e1_remote.py`: wording only.
- `ADOPTED_E3` (`tools/d7_regression.py`, `tools/c3_l4_nft_night.py`) is left as it is, as at G-A2..G-A9.

**The drop-in** (written separately, not by this diff):
`~/.config/systemd/user/privyhub-companion.service.d/step-in-place.conf`

```
[Service]
Environment=PRIVYHUB_STEP_IN_PLACE=1
```

**Off:**
1. Delete `step-in-place.conf`.
2. `systemctl --user daemon-reload`, then `systemctl --user restart privyhub-companion`.
3. Reverse this diff; `e3_state.py` then reads ok on thirteen.

Each ladder step then restarts the encoder as before: a new SSRC and a ~0.2-0.4-s gap. No client change.

**Predecessor sha256 (HEAD e0155d1c):**

```
792d4864590135efeca42d6e359fc9b676ab84895578d839c35065a7c78ab648  tools/e1_remote.py
7462073637e889eaa8cab7186066df681c180445855fc6870b5259b6f06f1232  tools/e1_suite.py
7051133607441c5f8760da30bca14b17d39b6e4832b0d235c3c52cf0f9cb6516  tools/e3_state.py
2c357cb5edc5b38087adfd51be23a4cedabd466be26f93f89fc061c041cd33d0  tools/test_e1_remote.py
```

**The diff** (`git apply -p1`):

```diff
diff --git a/tools/e1_remote.py b/tools/e1_remote.py
--- a/tools/e1_remote.py
+++ b/tools/e1_remote.py
@@ -165,7 +165,7 @@ def read_control_peers() -> dict[str, Any]:
 
 def preflight_remote(environ_has: Callable[[str], bool], adb_devices: Callable[[], str],
                      adopted: tuple[str, ...] | list[str] = ()) -> dict[str, Any]:
-    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, thirteen lines since G-A9); each must be read back too
+    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, fourteen lines since G-A10); each must be read back too
     need = list(REQUIRED_FLAGS) + [kv for kv in adopted if kv not in REQUIRED_FLAGS]
     d = {
         "flags": {kv: environ_has(kv) for kv in need},
diff --git a/tools/e1_suite.py b/tools/e1_suite.py
--- a/tools/e1_suite.py
+++ b/tools/e1_suite.py
@@ -121,8 +121,13 @@ RESTART_FAST_UNLOCK = "PRIVYHUB_RESTART_FAST_UNLOCK=1"
 # address); a LAN session as today, byte for byte (B28) -- through its own drop-in (remote.conf); the adopted environ is
 # exactly these thirteen names
 REMOTE = "PRIVYHUB_REMOTE=1"
+# G-A10 (adopted 2026-11-02, the user): the step in place -- each ladder step keeps the same stream (the new encoder
+# spliced onto the old one's RTP sequence and SSRC at one IDR; no new SSRC, no ~0.4-s gap), with a 2-s fallback to
+# today's encoder restart (B32's host half; HOME-1 C2) -- through its own drop-in (step-in-place.conf); the adopted
+# environ is exactly these fourteen names
+STEP_IN_PLACE = "PRIVYHUB_STEP_IN_PLACE=1"
 ADOPTED = sorted([LIVE, INDEX, SNES_CORE, RECOVERY, SNES_CAPTURE, OVERLAY, IDENTITY, AUDIO_CODEC, LINK_REPORT,
-                  LINK_RECOVERY, RESTART_FAST, RESTART_FAST_UNLOCK, REMOTE])
+                  LINK_RECOVERY, RESTART_FAST, RESTART_FAST_UNLOCK, REMOTE, STEP_IN_PLACE])
 FLAG_NAMES = ["PRIVYHUB_ADAPTIVE_BITRATE_INJECT", "PRIVYHUB_ADAPTIVE_BITRATE_TOP", "PRIVYHUB_PS1_LOOK",
               "PRIVYHUB_NATIVE_PROFILE_ID", "PRIVYHUB_FEC_SCHEME"]
 RA_CFG = Path.home() / ".config/retroarch/config"
@@ -1027,12 +1032,13 @@ def preflight() -> dict:
          "drop_in_restart_fast": f"Environment={RESTART_FAST}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_restart_fast_unlock": f"Environment={RESTART_FAST_UNLOCK}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_remote": f"Environment={REMOTE}" in sh(["systemctl", "--user", "cat", UNIT]),
+         "drop_in_step_in_place": f"Environment={STEP_IN_PLACE}" in sh(["systemctl", "--user", "cat", UNIT]),
          "e3_dropin_absent": not DROPIN.exists(), "e4_constraint_absent": not E4_DROPIN.exists()}
     d["ok"] = (d["manager"] == [] and d["environ"] == ADOPTED and d["adb"] and d["drop_in_live"] and d["drop_in_index"]
                and d["drop_in_snes_core"] and d["drop_in_recovery"] and d["drop_in_snes_capture"] and d["drop_in_overlay"]
                and d["drop_in_identity"] and d["drop_in_audio_codec"] and d["drop_in_link_report"]
                and d["drop_in_link_recovery"] and d["drop_in_restart_fast"] and d["drop_in_restart_fast_unlock"]
-               and d["drop_in_remote"]
+               and d["drop_in_remote"] and d["drop_in_step_in_place"]
                and d["e3_dropin_absent"] and d["e4_constraint_absent"])
     return d
 
diff --git a/tools/e3_state.py b/tools/e3_state.py
--- a/tools/e3_state.py
+++ b/tools/e3_state.py
@@ -1,5 +1,5 @@
 #!/usr/bin/env python3
-"""E3: the adopted state (since G-A9, thirteen: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report, the link-recovery stack, the fast restart, the fast restart unlocked, the WAN lines on a remote session; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
+"""E3: the adopted state (since G-A10, fourteen: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report, the link-recovery stack, the fast restart, the fast restart unlocked, the WAN lines on a remote session, the step in place; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
 import sys, json, importlib.util
 spec=importlib.util.spec_from_file_location('s','/home/privyhub/Projects/onn-stream-test/tools/e1_suite.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
 mp=m.mainpid()
diff --git a/tools/test_e1_remote.py b/tools/test_e1_remote.py
--- a/tools/test_e1_remote.py
+++ b/tools/test_e1_remote.py
@@ -133,7 +133,7 @@ class Preflight(unittest.TestCase):
         self.assertTrue(pf["adb_device"])
 
     def test_the_adopted_set_is_required_too(self):
-        # G-A2: the callers pass e1_suite.ADOPTED (thirteen lines since G-A9); one missing refuses, naming it
+        # G-A2: the callers pass e1_suite.ADOPTED (fourteen lines since G-A10); one missing refuses, naming it
         adopted = ("PRIVYHUB_AUDIO_CODEC=opus", R.REQUIRED_FLAGS[0])
         pf = R.preflight_remote(lambda kv: kv in R.REQUIRED_FLAGS, lambda: "", adopted)
         self.assertFalse(pf["ok"])
```
