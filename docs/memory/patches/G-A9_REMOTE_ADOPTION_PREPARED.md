---
memory_schema: 1
as_of: 2026-10-28
status: PREPARED (session B, B28; nothing applied). Applies only on the user's say-so after CL-B16, in G-A7's applied form; A applies it
---

# G-A9 — `PRIVYHUB_REMOTE=1`, the thirteenth adopted line, for the trip (PREPARED)

Built in B28 (`evidence/B28_REMOTE_UMBRELLA_2026-10-28.md`); to be measured in CL-B16
(`handoffs/SESSION_B_DONE_2026-10-28K.md`). **The user's question, after CL-B16:** "Adopt `PRIVYHUB_REMOTE=1` as the
thirteenth line? Away from home it turns on the four settings G4-S4 used (start at 4000 and climb, the remote ladder,
the 7000 cap, the WAN telemetry) by itself; at home nothing changes."

**What the line does on the host:**
- at each stream start it reads the session's class from the onn's address (G3's overlay test) and the overlay's path
  (direct / relayed / unknown);
- **remote** (any overlay address): G4-S4's four lines exactly, i.e. `PRIVYHUB_REMOTE_LADDER=1`,
  `PRIVYHUB_START_RUNG=floor`, `PRIVYHUB_REMOTE_RUNG_CAP=7000` and `PRIVYHUB_WAN_TELEMETRY=1`. The stream starts at
  4000 and climbs one rung every ~3 min; `logs/wan_sessions.jsonl` rows; `wan` in `/status`;
- **LAN:** none of the four, today's behaviour byte for byte (the start at 7000, the ladder rows without
  `path_class`, no telemetry rows);
- one `remote_config` row per session in the recovery log, and `remote_umbrella_config` at the companion's start;
- an explicit individual line still wins.

**What this changes:**
- `tools/e1_suite.py` defines `REMOTE` and puts it in `ADOPTED` (thirteen). The preflight reads `drop_in_remote` and
  requires it in `ok`.
- `tools/e3_state.py`, `tools/e1_remote.py`, `tools/test_e1_remote.py`: wording only.
- `ADOPTED_E3` (`tools/d7_regression.py`, `tools/c3_l4_nft_night.py`) is left as it is, as at G-A2 … G-A7.
- Replace `<date>` in the comment with the adoption's date when applying.
- If G-A8 (`PRIVYHUB_LOSS_GUARD=1`, held) is ever applied as well, the second one applied counts fourteen. Its
  comment and wording then need "fourteen", and its hunks rebase by one line.

**The drop-in** (written separately, not by this diff):
`~/.config/systemd/user/privyhub-companion.service.d/remote.conf`

```
[Service]
Environment=PRIVYHUB_REMOTE=1
```

Then `systemctl --user daemon-reload` and `systemctl --user restart privyhub-companion` (outside the watch's
04:30-05:30Z while `privyhub-link-n1` runs; it ends 2026-10-31T06:00Z). `e3_state.py --check` then reads ok on
thirteen.

**Off:** delete `remote.conf`, run `systemctl --user daemon-reload` and `systemctl --user restart
privyhub-companion`, and reverse this diff (`e3_state.py` then reads ok on twelve). Remote sessions then start at
7000 with no remote ladder, as on the twelve lines (G4-S4 sessions 1-7).

**Predecessor sha256** (HEAD `42a2ab6`, the tree clean):

```
7258fdd1fa8de4c818b6ff6a983458555dfe40a56f85eb24324baccddb80e5c6  tools/e1_remote.py
979fb28f28ef18af8e720cf0c5b2abc563ae6aeb1f7dea86589681cecff0c7b9  tools/e1_suite.py
6d0c306c1dc98382434b63a4a353eee371965233b569f3cc9b5632089d877df1  tools/e3_state.py
197e4822ba66675780632deaf99b9212c9f8dfaca7d487144a674f55c1e8dd0f  tools/test_e1_remote.py
```

**Checked (in /tmp only, never against the tree):**
- `git apply --check -p1` clean on copies of the four files, then applied there;
- `e1_suite.py --self-test` `E1_SUITE_SELF_TEST_OK`; `ADOPTED` 13 including `PRIVYHUB_REMOTE=1`;
- `test_e1_remote.py` the same as unpatched: 21 run, Gate3's one error from fixtures absent in the copy, as at every
  baseline.

The diff is also kept at `evidence/b28_2026-10-28/g_a9_prepared.diff`.

**The diff** (`git apply -p1`):

```diff
diff --git a/tools/e1_remote.py b/tools/e1_remote.py
--- a/tools/e1_remote.py
+++ b/tools/e1_remote.py
@@ -165,7 +165,7 @@
 
 def preflight_remote(environ_has: Callable[[str], bool], adb_devices: Callable[[], str],
                      adopted: tuple[str, ...] | list[str] = ()) -> dict[str, Any]:
-    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, twelve lines since G-A7); each must be read back too
+    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, thirteen lines since G-A9); each must be read back too
     need = list(REQUIRED_FLAGS) + [kv for kv in adopted if kv not in REQUIRED_FLAGS]
     d = {
         "flags": {kv: environ_has(kv) for kv in need},
diff --git a/tools/e1_suite.py b/tools/e1_suite.py
--- a/tools/e1_suite.py
+++ b/tools/e1_suite.py
@@ -110,8 +110,13 @@
 # (B24; acts only on a guarded start, inside RESTART_FAST) -- through its own drop-in (restart-fast-unlock.conf); the
 # adopted environ is exactly these twelve names
 RESTART_FAST_UNLOCK = "PRIVYHUB_RESTART_FAST_UNLOCK=1"
+# G-A9 (adopted <date>, the user): the WAN lines for a trip -- PRIVYHUB_REMOTE=1 implies G4-S4's four (the remote ladder,
+# the start rung floor, the remote cap 7000, the WAN telemetry), each acting only on a remote-class session (an overlay
+# address); a LAN session as today, byte for byte (B28) -- through its own drop-in (remote.conf); the adopted environ is
+# exactly these thirteen names
+REMOTE = "PRIVYHUB_REMOTE=1"
 ADOPTED = sorted([LIVE, INDEX, SNES_CORE, RECOVERY, SNES_CAPTURE, OVERLAY, IDENTITY, AUDIO_CODEC, LINK_REPORT,
-                  LINK_RECOVERY, RESTART_FAST, RESTART_FAST_UNLOCK])
+                  LINK_RECOVERY, RESTART_FAST, RESTART_FAST_UNLOCK, REMOTE])
 FLAG_NAMES = ["PRIVYHUB_ADAPTIVE_BITRATE_INJECT", "PRIVYHUB_ADAPTIVE_BITRATE_TOP", "PRIVYHUB_PS1_LOOK",
               "PRIVYHUB_NATIVE_PROFILE_ID", "PRIVYHUB_FEC_SCHEME"]
 RA_CFG = Path.home() / ".config/retroarch/config"
@@ -1015,11 +1020,13 @@
          "drop_in_link_recovery": f"Environment={LINK_RECOVERY}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_restart_fast": f"Environment={RESTART_FAST}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_restart_fast_unlock": f"Environment={RESTART_FAST_UNLOCK}" in sh(["systemctl", "--user", "cat", UNIT]),
+         "drop_in_remote": f"Environment={REMOTE}" in sh(["systemctl", "--user", "cat", UNIT]),
          "e3_dropin_absent": not DROPIN.exists(), "e4_constraint_absent": not E4_DROPIN.exists()}
     d["ok"] = (d["manager"] == [] and d["environ"] == ADOPTED and d["adb"] and d["drop_in_live"] and d["drop_in_index"]
                and d["drop_in_snes_core"] and d["drop_in_recovery"] and d["drop_in_snes_capture"] and d["drop_in_overlay"]
                and d["drop_in_identity"] and d["drop_in_audio_codec"] and d["drop_in_link_report"]
                and d["drop_in_link_recovery"] and d["drop_in_restart_fast"] and d["drop_in_restart_fast_unlock"]
+               and d["drop_in_remote"]
                and d["e3_dropin_absent"] and d["e4_constraint_absent"])
     return d
 
diff --git a/tools/e3_state.py b/tools/e3_state.py
--- a/tools/e3_state.py
+++ b/tools/e3_state.py
@@ -1,5 +1,5 @@
 #!/usr/bin/env python3
-"""E3: the adopted state (since G-A7, twelve: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report, the link-recovery stack, the fast restart, the fast restart unlocked; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
+"""E3: the adopted state (since G-A9, thirteen: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report, the link-recovery stack, the fast restart, the fast restart unlocked, the WAN lines on a remote session; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
 import sys, json, importlib.util
 spec=importlib.util.spec_from_file_location('s','/home/privyhub/Projects/onn-stream-test/tools/e1_suite.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
 mp=m.mainpid()
diff --git a/tools/test_e1_remote.py b/tools/test_e1_remote.py
--- a/tools/test_e1_remote.py
+++ b/tools/test_e1_remote.py
@@ -133,7 +133,7 @@
         self.assertTrue(pf["adb_device"])
 
     def test_the_adopted_set_is_required_too(self):
-        # G-A2: the callers pass e1_suite.ADOPTED (twelve lines since G-A7); one missing refuses, naming it
+        # G-A2: the callers pass e1_suite.ADOPTED (thirteen lines since G-A9); one missing refuses, naming it
         adopted = ("PRIVYHUB_AUDIO_CODEC=opus", R.REQUIRED_FLAGS[0])
         pf = R.preflight_remote(lambda kv: kv in R.REQUIRED_FLAGS, lambda: "", adopted)
         self.assertFalse(pf["ok"])
```
