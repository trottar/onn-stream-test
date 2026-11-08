---
memory_schema: 1
as_of: 2026-11-08
status: APPLIED (session A, HOME-6; the user's "PS2 always on — yes", 2026-11-08, conditional on C12'' and C14 met — both met). Written by A in G-A13's applied form, as SESSION_B_DONE_2026-11-08S.md §A stage 4 writes it
---

# G-A14 — `PRIVYHUB_PS2=1`, the sixteenth adopted line

Task: `handoffs/HOME-6_PS2_LOAD_TASK.md`. Measured in `evidence/HOME_6_PS2_LOAD_2026-11-08.md`: with the line set (the
user's bench drop-in), PrivyHub's SAVE wrote slot 1 in 0.5 s, and after Stop and a relaunch its LOAD continued the game
from the save (`picture ok 0.9s`, 0 `TLB Miss`; the user: "game loaded without issue"); a second in-game load the same
(the user: "Yes, back at the save"). Earlier: H3-P2 (PS2 streamed to the onn), HOME-4+ C11 (two pads, two players).
Built in B49 (the launch kind), B50 (cards, vsync, bindings), B51 (SAVE / LOAD through PINE), B52 (MTVU off, load
after boot, the picture check), B53 (PCSX2's log per launch).

**What it changes:**
- `tools/e1_suite.py` defines `PS2` (the comment `G-A14 (adopted 2026-11-08, the user)`) and puts it in `ADOPTED`,
  making sixteen. The preflight reads `drop_in_ps2` and requires it in `ok`.
- `tools/e3_state.py`, `tools/e1_remote.py`, `tools/test_e1_remote.py`: wording only.
- `ADOPTED_E3` (`tools/d7_regression.py`, `tools/c3_l4_nft_night.py`) is left as it is, as at G-A2..G-A13.

**What the line does on the hub:** the games list shows "PlayStation 2" (the titles in the drive's PS2 folder, read
in place); a launch starts PCSX2 2.8.2 (the AppImage under `runtime/emulators/pcsx2/`) with the PrivyHub virtual pads,
the chooser's ports, the hub's memory cards, MTVU off, vsync on, and PINE for pause and for PrivyHub's SAVE / LOAD
(slot files under `data/games/ps2/sstates/`, PCSX2's log per launch under `data/games/ps2/logs/`, 30 days). Nothing is
written to the drive. The hold / stall state loads stay off for PS2 (B51).

**The drop-in** (written separately, not by this diff; it replaces the user's bench drop-in `b49-ps2.conf`):
`~/.config/systemd/user/privyhub-companion.service.d/ps2.conf`

```
[Service]
Environment=PRIVYHUB_PS2=1
```

**Off:**
1. Delete `ps2.conf`.
2. `systemctl --user daemon-reload`, then `systemctl --user restart privyhub-companion`.
3. Reverse this diff; `e3_state.py` then reads ok on fifteen.

The games list then has no "PlayStation 2" entry and a PS2 launch is refused as before B49; no client change.

**Predecessor sha256 (HEAD 4aa08d3d):**

```
ec58211f89ad949d500570555c60a6f9597b9d952223b211512e6d550a79af7d  tools/e1_remote.py
c7824fe0b3a4e08f5560ce5e448af59ed4a8166c1e4194de54f4cde75af4a7ef  tools/e1_suite.py
36a4de2f9f2fbf92856905816aad81fe49c5fece998bd69f29968e1f7f714a4a  tools/e3_state.py
5f5079da84bab04d357189d9b7ec8231e41b461fdd57c56ca4ec1adc3f4f2d63  tools/test_e1_remote.py
```

**After:**

```
54bc618df22d4f0e243a8150397059f4967caa25d744756646a3ea14c26a4c59  tools/e1_remote.py
7042286096722317d69abbbfa9093f20edb9b80f530eee70ba047fcae39995cf  tools/e1_suite.py
9f4873325d091b92ecbb42fe6982fe181d4c119527f6fdff6076f3694e2660f8  tools/e3_state.py
de2c3d934fadf6f61e272d3c75e7ab247b9c56530d616c4490054ae07eaf0424  tools/test_e1_remote.py
```

**Gates** (`evidence/home6_2026-11-08/ga14/tests.txt`): `git apply --check` ok, applied, `git diff --check` clean;
`e1_suite --self-test` OK; `test_e1_remote` 21 OK; `test_c3_l4_nft_night` 33 OK; `tests/ps2_session` 79 passed.

**The diff** (`evidence/home6_2026-11-08/ga14/g_a14_applied.diff`):

```diff
diff -ru a/tools/e1_remote.py b/tools/e1_remote.py
--- a/tools/e1_remote.py	2026-11-08 12:44:56.727194878 -0500
+++ b/tools/e1_remote.py	2026-11-08 12:44:56.747195318 -0500
@@ -165,7 +165,7 @@
 
 def preflight_remote(environ_has: Callable[[str], bool], adb_devices: Callable[[], str],
                      adopted: tuple[str, ...] | list[str] = ()) -> dict[str, Any]:
-    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, fifteen lines since G-A13); each must be read back too
+    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, sixteen lines since G-A14); each must be read back too
     need = list(REQUIRED_FLAGS) + [kv for kv in adopted if kv not in REQUIRED_FLAGS]
     d = {
         "flags": {kv: environ_has(kv) for kv in need},
diff -ru a/tools/e1_suite.py b/tools/e1_suite.py
--- a/tools/e1_suite.py	2026-11-08 12:44:56.723194792 -0500
+++ b/tools/e1_suite.py	2026-11-08 12:44:56.747195318 -0500
@@ -141,8 +141,13 @@
 # of "Reconnect by default yes"; PRIVYHUB_VOD_DROP_TEST is never a line -- through its own drop-in (vod-log.conf); the
 # adopted environ is exactly these fifteen names
 VOD_LOG = "PRIVYHUB_VOD_LOG=1"
+# G-A14 (adopted 2026-11-08, the user): the PS2 launch kind -- PCSX2 from the onn with the pads, the chooser, the hub's
+# memory cards, and PrivyHub's SAVE / LOAD through PINE (B49-B53; H3-P2, HOME-4+ C11, HOME-6 C12'' / C14), the "PlayStation
+# 2" entry in the games list -- the user's "PS2 always on -- yes" -- through its own drop-in (ps2.conf); the adopted
+# environ is exactly these sixteen names
+PS2 = "PRIVYHUB_PS2=1"
 ADOPTED = sorted([LIVE, INDEX, SNES_CORE, RECOVERY, SNES_CAPTURE, OVERLAY, IDENTITY, AUDIO_CODEC, LINK_REPORT,
-                  LINK_RECOVERY, RESTART_FAST, RESTART_FAST_UNLOCK, REMOTE, STEP_IN_PLACE, VOD_LOG])
+                  LINK_RECOVERY, RESTART_FAST, RESTART_FAST_UNLOCK, REMOTE, STEP_IN_PLACE, VOD_LOG, PS2])
 FLAG_NAMES = ["PRIVYHUB_ADAPTIVE_BITRATE_INJECT", "PRIVYHUB_ADAPTIVE_BITRATE_TOP", "PRIVYHUB_PS1_LOOK",
               "PRIVYHUB_NATIVE_PROFILE_ID", "PRIVYHUB_FEC_SCHEME"]
 RA_CFG = Path.home() / ".config/retroarch/config"
@@ -1049,12 +1054,13 @@
          "drop_in_remote": f"Environment={REMOTE}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_step_in_place": f"Environment={STEP_IN_PLACE}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_vod_log": f"Environment={VOD_LOG}" in sh(["systemctl", "--user", "cat", UNIT]),
+         "drop_in_ps2": f"Environment={PS2}" in sh(["systemctl", "--user", "cat", UNIT]),
          "e3_dropin_absent": not DROPIN.exists(), "e4_constraint_absent": not E4_DROPIN.exists()}
     d["ok"] = (d["manager"] == [] and d["environ"] == ADOPTED and d["adb"] and d["drop_in_live"] and d["drop_in_index"]
                and d["drop_in_snes_core"] and d["drop_in_recovery"] and d["drop_in_snes_capture"] and d["drop_in_overlay"]
                and d["drop_in_identity"] and d["drop_in_audio_codec"] and d["drop_in_link_report"]
                and d["drop_in_link_recovery"] and d["drop_in_restart_fast"] and d["drop_in_restart_fast_unlock"]
-               and d["drop_in_remote"] and d["drop_in_step_in_place"] and d["drop_in_vod_log"]
+               and d["drop_in_remote"] and d["drop_in_step_in_place"] and d["drop_in_vod_log"] and d["drop_in_ps2"]
                and d["e3_dropin_absent"] and d["e4_constraint_absent"])
     return d
 
diff -ru a/tools/e3_state.py b/tools/e3_state.py
--- a/tools/e3_state.py	2026-11-08 12:44:56.723194792 -0500
+++ b/tools/e3_state.py	2026-11-08 12:44:56.747195318 -0500
@@ -1,5 +1,5 @@
 #!/usr/bin/env python3
-"""E3: the adopted state (since G-A13, fifteen: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report, the link-recovery stack, the fast restart, the fast restart unlocked, the WAN lines on a remote session, the step in place, the movie range log; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
+"""E3: the adopted state (since G-A14, sixteen: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report, the link-recovery stack, the fast restart, the fast restart unlocked, the WAN lines on a remote session, the step in place, the movie range log, the PS2 launch kind; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
 import sys, json, importlib.util
 spec=importlib.util.spec_from_file_location('s','/home/privyhub/Projects/onn-stream-test/tools/e1_suite.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
 mp=m.mainpid()
diff -ru a/tools/test_e1_remote.py b/tools/test_e1_remote.py
--- a/tools/test_e1_remote.py	2026-11-08 12:44:56.731194966 -0500
+++ b/tools/test_e1_remote.py	2026-11-08 12:44:56.747195318 -0500
@@ -133,7 +133,7 @@
         self.assertTrue(pf["adb_device"])
 
     def test_the_adopted_set_is_required_too(self):
-        # G-A2: the callers pass e1_suite.ADOPTED (fifteen lines since G-A13); one missing refuses, naming it
+        # G-A2: the callers pass e1_suite.ADOPTED (sixteen lines since G-A14); one missing refuses, naming it
         adopted = ("PRIVYHUB_AUDIO_CODEC=opus", R.REQUIRED_FLAGS[0])
         pf = R.preflight_remote(lambda kv: kv in R.REQUIRED_FLAGS, lambda: "", adopted)
         self.assertFalse(pf["ok"])
```
