---
memory_schema: 1
as_of: 2026-11-08
status: APPLIED (session A, HOME-7+N64; the user's word at stage 10, verbatim: "Yes keep on but we should try to  resolve the issues too"). Written by A in G-A13's applied form, as SESSION_B_DONE_2026-11-08V.md §A writes it
---

# G-A15 — `PRIVYHUB_N64=1`, the seventeenth adopted line

Task: `handoffs/HOME-7_JOIN_PS2_N64_TASK.md`. Measured in `evidence/HOME_7_HOLD_TO_JOIN_N64_2026-11-08.md`: C21 (the
first N64 title from the onn, four ports, two pads by the hold, "Felt good to play, no issues") and C22 (SAVE / LOAD
with RetroArch's buttons, "All worked as expected") met; **C23 not met** (the Home hold froze the game — RetroArch's
network commands timed out — and a second title's buttons did not work). The user adopted it with the issues open
(B61). Built in B59 (`evidence/B59_N64_LAUNCH_2026-11-08.md`); the core `mupen64plus_next_libretro.so` fetched on the
user's "go N64" (`runtime/emulators/retroarch/cores-linux/`, gitignored; sha256 `26f2b4ec…775e`).

**What it changes:**
- `tools/e1_suite.py` defines `N64` (the comment `G-A15 (adopted 2026-11-08, the user)`) and puts it in `ADOPTED`,
  making seventeen. The preflight reads `drop_in_n64` and requires it in `ok`.
- `tools/e3_state.py`, `tools/e1_remote.py`, `tools/test_e1_remote.py`: wording only.
- `ADOPTED_E3` (`tools/d7_regression.py`, `tools/c3_l4_nft_night.py`) is left as it is, as at G-A2..G-A14.

**What the line does on the hub:** the games list shows "Nintendo 64" (the titles in the folder `N64_DIR=` names in the
gitignored paths file, read in place); a launch starts RetroArch with mupen64plus_next, four ports from the start, the
core options B59 writes (12 keys), hold-to-join; SAVE / LOAD through RetroArch as PS1. Nothing is written to the drive.

**The drop-in** (written separately, not by this diff; it replaces the bench drop-in `b59-n64.conf`):
`~/.config/systemd/user/privyhub-companion.service.d/n64.conf`

```
[Service]
Environment=PRIVYHUB_N64=1
```

**Off:**
1. Delete `n64.conf`.
2. `systemctl --user daemon-reload`, then `systemctl --user restart privyhub-companion`.
3. Reverse this diff; `e3_state.py` then reads ok on sixteen.

The games list then has no "Nintendo 64" entry; the other systems are unchanged.

**Predecessor sha256 (HEAD 32abb425):**

```
54bc618df22d4f0e243a8150397059f4967caa25d744756646a3ea14c26a4c59  tools/e1_remote.py
7042286096722317d69abbbfa9093f20edb9b80f530eee70ba047fcae39995cf  tools/e1_suite.py
9f4873325d091b92ecbb42fe6982fe181d4c119527f6fdff6076f3694e2660f8  tools/e3_state.py
de2c3d934fadf6f61e272d3c75e7ab247b9c56530d616c4490054ae07eaf0424  tools/test_e1_remote.py
```

**After:**

```
38f43dd2691fb70533681b255759352fbc0d645d702d4126ef192c3d1050c4ac  tools/e1_remote.py
c3cd1fb1bc10189c1a01674039ce59d0d5469d76c6bc3c1dd0b7627eba0c69d7  tools/e1_suite.py
9811862b1648229dd3a3507e905ebb3e98242764b4b0749ce63b1a7720087edf  tools/e3_state.py
bd865e21635e725ae4af495d698392b370bd919204ca9f5cac663ed59599d13e  tools/test_e1_remote.py
```

**Gates** (`evidence/home7_2026-11-08/ga15/tests.txt`): `git apply --check` ok, applied, `git diff --check` clean;
`e1_suite --self-test` OK; `test_e1_remote` 21 OK; `test_c3_l4_nft_night` 33 OK; `tests/ps2_session` 93 passed;
`tests/n64_session` 28 passed. `--check` ok on seventeen; `flags_absent` true.

**The diff** (`evidence/home7_2026-11-08/ga15/g_a15_applied.diff`):

```diff
diff -ru a/tools/e1_remote.py b/tools/e1_remote.py
--- a/tools/e1_remote.py	2026-11-08 17:39:41.986304086 -0500
+++ b/tools/e1_remote.py	2026-11-08 17:39:42.006304516 -0500
@@ -165,7 +165,7 @@
 
 def preflight_remote(environ_has: Callable[[str], bool], adb_devices: Callable[[], str],
                      adopted: tuple[str, ...] | list[str] = ()) -> dict[str, Any]:
-    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, sixteen lines since G-A14); each must be read back too
+    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, seventeen lines since G-A15); each must be read back too
     need = list(REQUIRED_FLAGS) + [kv for kv in adopted if kv not in REQUIRED_FLAGS]
     d = {
         "flags": {kv: environ_has(kv) for kv in need},
diff -ru a/tools/e1_suite.py b/tools/e1_suite.py
--- a/tools/e1_suite.py	2026-11-08 17:39:41.982304000 -0500
+++ b/tools/e1_suite.py	2026-11-08 17:39:42.006304516 -0500
@@ -146,8 +146,14 @@
 # 2" entry in the games list -- the user's "PS2 always on -- yes" -- through its own drop-in (ps2.conf); the adopted
 # environ is exactly these sixteen names
 PS2 = "PRIVYHUB_PS2=1"
+# G-A15 (adopted 2026-11-08, the user): the N64 launch kind -- RetroArch with mupen64plus_next (the core fetched on the
+# user's go), four ports from the start, hold-to-join, the "Nintendo 64" entry from the drive's N64 folder (read in
+# place), SAVE / LOAD through RetroArch (B59; HOME-7 C21 / C22) -- the user's "Yes keep on" with C23's Home-hold freeze
+# and a title's mapping open (B61) -- through its own drop-in (n64.conf); the adopted environ is exactly these
+# seventeen names
+N64 = "PRIVYHUB_N64=1"
 ADOPTED = sorted([LIVE, INDEX, SNES_CORE, RECOVERY, SNES_CAPTURE, OVERLAY, IDENTITY, AUDIO_CODEC, LINK_REPORT,
-                  LINK_RECOVERY, RESTART_FAST, RESTART_FAST_UNLOCK, REMOTE, STEP_IN_PLACE, VOD_LOG, PS2])
+                  LINK_RECOVERY, RESTART_FAST, RESTART_FAST_UNLOCK, REMOTE, STEP_IN_PLACE, VOD_LOG, PS2, N64])
 FLAG_NAMES = ["PRIVYHUB_ADAPTIVE_BITRATE_INJECT", "PRIVYHUB_ADAPTIVE_BITRATE_TOP", "PRIVYHUB_PS1_LOOK",
               "PRIVYHUB_NATIVE_PROFILE_ID", "PRIVYHUB_FEC_SCHEME"]
 RA_CFG = Path.home() / ".config/retroarch/config"
@@ -1055,12 +1061,13 @@
          "drop_in_step_in_place": f"Environment={STEP_IN_PLACE}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_vod_log": f"Environment={VOD_LOG}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_ps2": f"Environment={PS2}" in sh(["systemctl", "--user", "cat", UNIT]),
+         "drop_in_n64": f"Environment={N64}" in sh(["systemctl", "--user", "cat", UNIT]),
          "e3_dropin_absent": not DROPIN.exists(), "e4_constraint_absent": not E4_DROPIN.exists()}
     d["ok"] = (d["manager"] == [] and d["environ"] == ADOPTED and d["adb"] and d["drop_in_live"] and d["drop_in_index"]
                and d["drop_in_snes_core"] and d["drop_in_recovery"] and d["drop_in_snes_capture"] and d["drop_in_overlay"]
                and d["drop_in_identity"] and d["drop_in_audio_codec"] and d["drop_in_link_report"]
                and d["drop_in_link_recovery"] and d["drop_in_restart_fast"] and d["drop_in_restart_fast_unlock"]
-               and d["drop_in_remote"] and d["drop_in_step_in_place"] and d["drop_in_vod_log"] and d["drop_in_ps2"]
+               and d["drop_in_remote"] and d["drop_in_step_in_place"] and d["drop_in_vod_log"] and d["drop_in_ps2"] and d["drop_in_n64"]
                and d["e3_dropin_absent"] and d["e4_constraint_absent"])
     return d
 
diff -ru a/tools/e3_state.py b/tools/e3_state.py
--- a/tools/e3_state.py	2026-11-08 17:39:41.982304000 -0500
+++ b/tools/e3_state.py	2026-11-08 17:39:42.006304516 -0500
@@ -1,5 +1,5 @@
 #!/usr/bin/env python3
-"""E3: the adopted state (since G-A14, sixteen: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report, the link-recovery stack, the fast restart, the fast restart unlocked, the WAN lines on a remote session, the step in place, the movie range log, the PS2 launch kind; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
+"""E3: the adopted state (since G-A15, seventeen: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report, the link-recovery stack, the fast restart, the fast restart unlocked, the WAN lines on a remote session, the step in place, the movie range log, the PS2 launch kind, the N64 launch kind; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
 import sys, json, importlib.util
 spec=importlib.util.spec_from_file_location('s','/home/privyhub/Projects/onn-stream-test/tools/e1_suite.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
 mp=m.mainpid()
diff -ru a/tools/test_e1_remote.py b/tools/test_e1_remote.py
--- a/tools/test_e1_remote.py	2026-11-08 17:39:41.990304173 -0500
+++ b/tools/test_e1_remote.py	2026-11-08 17:39:42.006304516 -0500
@@ -133,7 +133,7 @@
         self.assertTrue(pf["adb_device"])
 
     def test_the_adopted_set_is_required_too(self):
-        # G-A2: the callers pass e1_suite.ADOPTED (sixteen lines since G-A14); one missing refuses, naming it
+        # G-A2: the callers pass e1_suite.ADOPTED (seventeen lines since G-A15); one missing refuses, naming it
         adopted = ("PRIVYHUB_AUDIO_CODEC=opus", R.REQUIRED_FLAGS[0])
         pf = R.preflight_remote(lambda kv: kv in R.REQUIRED_FLAGS, lambda: "", adopted)
         self.assertFalse(pf["ok"])
```
