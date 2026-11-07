---
memory_schema: 1
as_of: 2026-11-07
status: APPLIED (session A, G-A13 host half; the user's decision 2026-11-06 "Reconnect by default yes"; 2026-11-07 the host half adopted now, the client default in B's queue O). Written by A in G-A10's applied form (no patch was prepared by B)
---

# G-A13 (host) — `PRIVYHUB_VOD_LOG=1`, the fifteenth adopted line

Task: `handoffs/G9-CHECKPOINT_AND_G-A13_TASK.md`. Measured in `evidence/HOME_3_DEFAULTS_PROMPT_VOD_2026-11-06.md`
C5'': with the line set (in the bench drop-in), a `drop 45` reconnected and resumed at the position, and a companion
restart with the movie open resumed in 3.6 s after a token refetch; the rows this line writes were the evidence. Built
in B35 (`evidence/B35_VOD_RETRY_2026-10-31.md`, `companion/vod_log.py`) and widened in B43 (`reason`, `kind`,
`token_refetched` whitelisted). Record: `evidence/G_A13_VOD_LOG_ADOPTION_2026-11-07.md`.

**What it changes:**
- `tools/e1_suite.py` defines `VOD_LOG` (the comment `G-A13 (adopted 2026-11-07, the user)`) and puts it in
  `ADOPTED`, making fifteen. The preflight reads `drop_in_vod_log` and requires it in `ok`.
- `tools/e3_state.py`, `tools/e1_remote.py`, `tools/test_e1_remote.py`: wording only.
- `ADOPTED_E3` (`tools/d7_regression.py`, `tools/c3_l4_nft_night.py`) is left as it is, as at G-A2..G-A10.

**What the line does on the hub:** one redacted JSON row per VOD range request in `logs/vod_range.jsonl` (rotating,
5 MB × 3); the client's movie-retry rows in `logs/vod_client.jsonl` when a client with the retry posts them (the
`/diagnostics/vod-client` path, whitelisted fields; 400 for anything else). No title, path or token in a row.
`PRIVYHUB_VOD_DROP_TEST` is never a line.

**The drop-in** (written separately, not by this diff):
`~/.config/systemd/user/privyhub-companion.service.d/vod-log.conf`

```
[Service]
Environment=PRIVYHUB_VOD_LOG=1
```

**Off:**
1. Delete `vod-log.conf`.
2. `systemctl --user daemon-reload`, then `systemctl --user restart privyhub-companion`.
3. Reverse this diff; `e3_state.py` then reads ok on fourteen.

The range server then writes no rows and `/diagnostics/vod-client` is not served (today's 404); no client change.

**Predecessor sha256 (HEAD 953231d6):**

```
3bac22b80302870100ce02e193eab6c0bf988bb3ffdd3f5a7d3be66a82430cfd  tools/e1_remote.py
accbd32d2ecfc154f165189a5555c12179c88d507fb66d74770723614586c8bb  tools/e1_suite.py
ba844e8964c0c4d154c58d08e6d6dddba5f8d4d1406b801c99c4f20f8969f909  tools/e3_state.py
f8870df2f82ebde30947b218b360730ee2a955ab7d729a73bc865cf0a9936011  tools/test_e1_remote.py
```

**The diff** (`evidence/g_a13_2026-11-07/g_a13_applied.diff`):

```diff
diff --git a/tools/e1_remote.py b/tools/e1_remote.py
--- a/tools/e1_remote.py
+++ b/tools/e1_remote.py
@@ -165,7 +165,7 @@
 
 def preflight_remote(environ_has: Callable[[str], bool], adb_devices: Callable[[], str],
                      adopted: tuple[str, ...] | list[str] = ()) -> dict[str, Any]:
-    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, fourteen lines since G-A10); each must be read back too
+    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, fifteen lines since G-A13); each must be read back too
     need = list(REQUIRED_FLAGS) + [kv for kv in adopted if kv not in REQUIRED_FLAGS]
     d = {
         "flags": {kv: environ_has(kv) for kv in need},
diff --git a/tools/e1_suite.py b/tools/e1_suite.py
--- a/tools/e1_suite.py
+++ b/tools/e1_suite.py
@@ -132,8 +132,14 @@
 # today's encoder restart (B32's host half; HOME-1 C2) -- through its own drop-in (step-in-place.conf); the adopted
 # environ is exactly these fourteen names
 STEP_IN_PLACE = "PRIVYHUB_STEP_IN_PLACE=1"
+# G-A13 (adopted 2026-11-07, the user): the movie range log -- one redacted JSON row per VOD range request to
+# logs/vod_range.jsonl (status, bytes, duration, how it closed; the path hashed, the token dropped; 5 MB x 3), and the
+# client's movie-retry rows to logs/vod_client.jsonl when a client posts them (B35 / B43; HOME-3 C5'') -- the host half
+# of "Reconnect by default yes"; PRIVYHUB_VOD_DROP_TEST is never a line -- through its own drop-in (vod-log.conf); the
+# adopted environ is exactly these fifteen names
+VOD_LOG = "PRIVYHUB_VOD_LOG=1"
 ADOPTED = sorted([LIVE, INDEX, SNES_CORE, RECOVERY, SNES_CAPTURE, OVERLAY, IDENTITY, AUDIO_CODEC, LINK_REPORT,
-                  LINK_RECOVERY, RESTART_FAST, RESTART_FAST_UNLOCK, REMOTE, STEP_IN_PLACE])
+                  LINK_RECOVERY, RESTART_FAST, RESTART_FAST_UNLOCK, REMOTE, STEP_IN_PLACE, VOD_LOG])
 FLAG_NAMES = ["PRIVYHUB_ADAPTIVE_BITRATE_INJECT", "PRIVYHUB_ADAPTIVE_BITRATE_TOP", "PRIVYHUB_PS1_LOOK",
               "PRIVYHUB_NATIVE_PROFILE_ID", "PRIVYHUB_FEC_SCHEME"]
 RA_CFG = Path.home() / ".config/retroarch/config"
@@ -1039,12 +1045,13 @@
          "drop_in_restart_fast_unlock": f"Environment={RESTART_FAST_UNLOCK}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_remote": f"Environment={REMOTE}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_step_in_place": f"Environment={STEP_IN_PLACE}" in sh(["systemctl", "--user", "cat", UNIT]),
+         "drop_in_vod_log": f"Environment={VOD_LOG}" in sh(["systemctl", "--user", "cat", UNIT]),
          "e3_dropin_absent": not DROPIN.exists(), "e4_constraint_absent": not E4_DROPIN.exists()}
     d["ok"] = (d["manager"] == [] and d["environ"] == ADOPTED and d["adb"] and d["drop_in_live"] and d["drop_in_index"]
                and d["drop_in_snes_core"] and d["drop_in_recovery"] and d["drop_in_snes_capture"] and d["drop_in_overlay"]
                and d["drop_in_identity"] and d["drop_in_audio_codec"] and d["drop_in_link_report"]
                and d["drop_in_link_recovery"] and d["drop_in_restart_fast"] and d["drop_in_restart_fast_unlock"]
-               and d["drop_in_remote"] and d["drop_in_step_in_place"]
+               and d["drop_in_remote"] and d["drop_in_step_in_place"] and d["drop_in_vod_log"]
                and d["e3_dropin_absent"] and d["e4_constraint_absent"])
     return d
 
diff --git a/tools/e3_state.py b/tools/e3_state.py
--- a/tools/e3_state.py
+++ b/tools/e3_state.py
@@ -1,5 +1,5 @@
 #!/usr/bin/env python3
-"""E3: the adopted state (since G-A10, fourteen: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report, the link-recovery stack, the fast restart, the fast restart unlocked, the WAN lines on a remote session, the step in place; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
+"""E3: the adopted state (since G-A13, fifteen: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report, the link-recovery stack, the fast restart, the fast restart unlocked, the WAN lines on a remote session, the step in place, the movie range log; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
 import sys, json, importlib.util
 spec=importlib.util.spec_from_file_location('s','/home/privyhub/Projects/onn-stream-test/tools/e1_suite.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
 mp=m.mainpid()
diff --git a/tools/test_e1_remote.py b/tools/test_e1_remote.py
--- a/tools/test_e1_remote.py
+++ b/tools/test_e1_remote.py
@@ -133,7 +133,7 @@
         self.assertTrue(pf["adb_device"])
 
     def test_the_adopted_set_is_required_too(self):
-        # G-A2: the callers pass e1_suite.ADOPTED (fourteen lines since G-A10); one missing refuses, naming it
+        # G-A2: the callers pass e1_suite.ADOPTED (fifteen lines since G-A13); one missing refuses, naming it
         adopted = ("PRIVYHUB_AUDIO_CODEC=opus", R.REQUIRED_FLAGS[0])
         pf = R.preflight_remote(lambda kv: kv in R.REQUIRED_FLAGS, lambda: "", adopted)
         self.assertFalse(pf["ok"])
```
