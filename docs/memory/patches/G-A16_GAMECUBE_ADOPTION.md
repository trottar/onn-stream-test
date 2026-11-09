---
memory_schema: 1
as_of: 2026-11-09
status: APPLIED (session A, HOME-9+GC; the user's word at the close, verbatim: "Yes keep"). Written by A in G-A13's applied form, as handoffs/HOME-9_GC_TASK.md writes it
---

# G-A16 — `PRIVYHUB_GAMECUBE=1`, the eighteenth adopted line

Task: `handoffs/HOME-9_GC_TASK.md`. Measured in `evidence/HOME_9_GC_2026-11-09.md`: C34 (the first GameCube title from
the onn: launch → picture 10.2 s, P1 / P2 by the hold, Dolphin's log `Added device: evdev/0/PrivyHub Virtual Gamepad
P1` … `P4`, the layout "All as expected"), C35 (SAVE slot 1 file stable 0.3 s; LOAD picture ok 0.9 s, also into a
relaunched Dolphin; the Home hold's slot 9 verdict ok; "Save and load worked", "Home worked") and C36 (two pads, the bar
0.0 vs PS1 0.0, Dolphin's counters 60 / 60 / 60 with VIs 60.11 / s; "Feels pretty good") met. Built in B69
(`evidence/B69_GAMECUBE_LAUNCH_KIND_2026-11-09.md`); Dolphin 2609b fetched in H2-P1 (the upstream AppImage, gitignored).

**What it changes:**
- `tools/e1_suite.py` defines `GAMECUBE` (the comment `G-A16 (adopted 2026-11-09, the user)`) and puts it in
  `ADOPTED`, making eighteen. The preflight reads `drop_in_gamecube` and requires it in `ok`.
- `tools/e3_state.py`, `tools/e1_remote.py`, `tools/test_e1_remote.py`: wording only.
- `ADOPTED_E3` (`tools/d7_regression.py`, `tools/c3_l4_nft_night.py`) is left as it is, as at G-A2..G-A15.

**What the line does on the hub:** the games list shows "GameCube" (the titles in the folder `GAMECUBE_DIR=` names in
the gitignored paths file, read in place, `.rvz` first); a launch starts Dolphin (`-b -u data/games/gamecube/user -e
<title>`) with its config written whole, four native ports, hold-to-join, the F10 pause and the state hotkeys (SAVE /
LOAD as PS1; the hold's return and the stall resume on slot 9); the exit by SIGTERM. Nothing is written to the drive.

**The drop-in** (written separately, not by this diff; it replaces the bench drop-in `b69-gamecube.conf`):
`~/.config/systemd/user/privyhub-companion.service.d/gamecube.conf`

```
[Service]
Environment=PRIVYHUB_GAMECUBE=1
```

**Off:**
1. Delete `gamecube.conf`.
2. `systemctl --user daemon-reload`, then `systemctl --user restart privyhub-companion`.
3. Reverse this diff; `e3_state.py` then reads ok on seventeen.

The games list then has no "GameCube" entry; the other systems are unchanged.

**Predecessor sha256 (HEAD 1bf0a76c + the HOME-9 pin):**

```
38f43dd2691fb70533681b255759352fbc0d645d702d4126ef192c3d1050c4ac  tools/e1_remote.py
ff58007909a259711f99798a84a71cb2d1a5bf510763ffd928a68eb28594cbbf  tools/e1_suite.py
9811862b1648229dd3a3507e905ebb3e98242764b4b0749ce63b1a7720087edf  tools/e3_state.py
bd865e21635e725ae4af495d698392b370bd919204ca9f5cac663ed59599d13e  tools/test_e1_remote.py
```

**After:**

```
eb5d3174ace232af01f1c68f5e03843911f2d876f6a90166b3ce7e2ac88cc33f  tools/e1_remote.py
d0077fc9992b8cdcfd7c51d86cf249c6593d1506121e2272da77f88119d172c7  tools/e1_suite.py
8052a7ef6682b6b411126a343717bcd9527cd29b046ca147f9461175330fb9db  tools/e3_state.py
ff54c3a920c7696bced4635056742ad7f5f8a1ac47ee9df3c66130050bf486ab  tools/test_e1_remote.py
```

**Gates** (`evidence/home9_2026-11-09/ga16/tests.txt`): `git apply --check` ok on the predecessors and `-R` on the tree,
applied, `git diff --check` clean; `e1_suite --self-test` OK; `test_e1_remote` 21 OK; `test_c3_l4_nft_night` 33 OK;
`tests/ps2_session` 93, `tests/n64_session` 28, `tests/gamecube_session` 54 passed. `--check` ok on eighteen (APK
CONFIRMED); `flags_absent` true.

**The diff** (`evidence/home9_2026-11-09/ga16/g_a16_applied.diff`):

```diff
--- a/tools/e1_remote.py	2026-11-09 01:54:11.366832264 -0500
+++ b/tools/e1_remote.py	2026-11-09 01:54:11.390832814 -0500
@@ -165,7 +165,7 @@
 
 def preflight_remote(environ_has: Callable[[str], bool], adb_devices: Callable[[], str],
                      adopted: tuple[str, ...] | list[str] = ()) -> dict[str, Any]:
-    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, seventeen lines since G-A15); each must be read back too
+    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, eighteen lines since G-A16); each must be read back too
     need = list(REQUIRED_FLAGS) + [kv for kv in adopted if kv not in REQUIRED_FLAGS]
     d = {
         "flags": {kv: environ_has(kv) for kv in need},
--- a/tools/e1_suite.py	2026-11-09 01:54:11.366832264 -0500
+++ b/tools/e1_suite.py	2026-11-09 01:54:11.390832814 -0500
@@ -158,8 +158,14 @@
 # and a title's mapping open (B61) -- through its own drop-in (n64.conf); the adopted environ is exactly these
 # seventeen names
 N64 = "PRIVYHUB_N64=1"
+# G-A16 (adopted 2026-11-09, the user): the GameCube launch kind -- Dolphin 2609b (the upstream AppImage), its config
+# written whole per launch, four native ports with hold-to-join, the F10 pause and the state hotkeys (SAVE / LOAD as
+# PS1, the hold's slot 9), the "GameCube" entry from the drive's GameCube folder (read in place) (B69; HOME-9 C34-C36)
+# -- the user's "Yes keep" -- through its own drop-in (gamecube.conf); the adopted environ is exactly these eighteen
+# names
+GAMECUBE = "PRIVYHUB_GAMECUBE=1"
 ADOPTED = sorted([LIVE, INDEX, SNES_CORE, RECOVERY, SNES_CAPTURE, OVERLAY, IDENTITY, AUDIO_CODEC, LINK_REPORT,
-                  LINK_RECOVERY, RESTART_FAST, RESTART_FAST_UNLOCK, REMOTE, STEP_IN_PLACE, VOD_LOG, PS2, N64])
+                  LINK_RECOVERY, RESTART_FAST, RESTART_FAST_UNLOCK, REMOTE, STEP_IN_PLACE, VOD_LOG, PS2, N64, GAMECUBE])
 FLAG_NAMES = ["PRIVYHUB_ADAPTIVE_BITRATE_INJECT", "PRIVYHUB_ADAPTIVE_BITRATE_TOP", "PRIVYHUB_PS1_LOOK",
               "PRIVYHUB_NATIVE_PROFILE_ID", "PRIVYHUB_FEC_SCHEME"]
 RA_CFG = Path.home() / ".config/retroarch/config"
@@ -1068,12 +1074,14 @@
          "drop_in_vod_log": f"Environment={VOD_LOG}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_ps2": f"Environment={PS2}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_n64": f"Environment={N64}" in sh(["systemctl", "--user", "cat", UNIT]),
+         "drop_in_gamecube": f"Environment={GAMECUBE}" in sh(["systemctl", "--user", "cat", UNIT]),
          "e3_dropin_absent": not DROPIN.exists(), "e4_constraint_absent": not E4_DROPIN.exists()}
     d["ok"] = (d["manager"] == [] and d["environ"] == ADOPTED and d["adb"] and d["drop_in_live"] and d["drop_in_index"]
                and d["drop_in_snes_core"] and d["drop_in_recovery"] and d["drop_in_snes_capture"] and d["drop_in_overlay"]
                and d["drop_in_identity"] and d["drop_in_audio_codec"] and d["drop_in_link_report"]
                and d["drop_in_link_recovery"] and d["drop_in_restart_fast"] and d["drop_in_restart_fast_unlock"]
                and d["drop_in_remote"] and d["drop_in_step_in_place"] and d["drop_in_vod_log"] and d["drop_in_ps2"] and d["drop_in_n64"]
+               and d["drop_in_gamecube"]
                and d["e3_dropin_absent"] and d["e4_constraint_absent"])
     return d
 
--- a/tools/e3_state.py	2026-11-09 01:54:11.366832264 -0500
+++ b/tools/e3_state.py	2026-11-09 01:54:11.390832814 -0500
@@ -1,5 +1,5 @@
 #!/usr/bin/env python3
-"""E3: the adopted state (since G-A15, seventeen: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report, the link-recovery stack, the fast restart, the fast restart unlocked, the WAN lines on a remote session, the step in place, the movie range log, the PS2 launch kind, the N64 launch kind; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
+"""E3: the adopted state (since G-A16, eighteen: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report, the link-recovery stack, the fast restart, the fast restart unlocked, the WAN lines on a remote session, the step in place, the movie range log, the PS2 launch kind, the N64 launch kind, the GameCube launch kind; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
 import sys, json, importlib.util
 spec=importlib.util.spec_from_file_location('s','/home/privyhub/Projects/onn-stream-test/tools/e1_suite.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
 mp=m.mainpid()
--- a/tools/test_e1_remote.py	2026-11-09 01:54:11.366832264 -0500
+++ b/tools/test_e1_remote.py	2026-11-09 01:54:11.390832814 -0500
@@ -133,7 +133,7 @@
         self.assertTrue(pf["adb_device"])
 
     def test_the_adopted_set_is_required_too(self):
-        # G-A2: the callers pass e1_suite.ADOPTED (seventeen lines since G-A15); one missing refuses, naming it
+        # G-A2: the callers pass e1_suite.ADOPTED (eighteen lines since G-A16); one missing refuses, naming it
         adopted = ("PRIVYHUB_AUDIO_CODEC=opus", R.REQUIRED_FLAGS[0])
         pf = R.preflight_remote(lambda kv: kv in R.REQUIRED_FLAGS, lambda: "", adopted)
         self.assertFalse(pf["ok"])
```
