---
memory_schema: 1
as_of: 2026-10-27
status: PREPARED (session B, B27; nothing applied). Applies only on the user's say-so after CL-B15, in G-A7's applied form; A applies it
---

# G-A8 — `PRIVYHUB_LOSS_GUARD=1`, the thirteenth adopted line (PREPARED)

Built in B10 (`evidence/B10_CLIENT_LOSS_GUARD_2026-10-22.md`); measured in BENCH-R3 E
(`evidence/BENCH_R3_SNES_STACK_AND_LOSS_GUARD_2026-10-23.md` §5: 3,010 / 3,010 corrupted frames held at 1 % post-FEC
loss, 0 timeouts, max wait 501 ms). The client's guard is on by default since B27
(`evidence/B27_LOSS_GUARD_DEFAULT_ON_2026-10-27.md`, APK `8b0fbb74…3f4e`). To be measured in CL-B15
(`handoffs/SESSION_B_DONE_2026-10-27J.md`). **The user's question, after CL-B15:** "Adopt `PRIVYHUB_LOSS_GUARD=1` as
the thirteenth line?"

**What the line does on the host** (and what it does not):
- the client's keyframe request (`PHK1`, 24 B, one per freeze) is parsed, counted and rate-limited (at most one per
  500 ms acted on) instead of being counted as a bad controller packet;
- `loss_guard_config` at the start, a per-minute `keyframe_requests` row (received / acted / rate_limited / forced /
  unforced, the reason), the heartbeat's three loss-guard fields in `native_stream_heartbeat.log`;
- **it forces no keyframe:** there is no runtime IDR path (B10 §0.3; `NoRuntimeIdr`). The picture is the same with or
  without the line. The freeze on the last good frame is the client's own, on by default since B27.

**What this changes:**
- `tools/e1_suite.py` defines `LOSS_GUARD` and puts it in `ADOPTED` (thirteen). The preflight reads
  `drop_in_loss_guard` and requires it in `ok`.
- `tools/e3_state.py`, `tools/e1_remote.py`, `tools/test_e1_remote.py`: wording only.
- `ADOPTED_E3` (`tools/d7_regression.py`, `tools/c3_l4_nft_night.py`) is left as it is, as at G-A2 … G-A7.
- Replace `<date>` in the comment with the adoption's date when applying.

**The drop-in** (written separately, not by this diff):
`~/.config/systemd/user/privyhub-companion.service.d/loss-guard.conf`

```
[Service]
Environment=PRIVYHUB_LOSS_GUARD=1
```

Then `systemctl --user daemon-reload` and `systemctl --user restart privyhub-companion` (outside the watch's
04:30-05:30Z). `e3_state.py --check` then reads ok on thirteen.

**Off:** delete `loss-guard.conf`, run `systemctl --user daemon-reload` and `systemctl --user restart
privyhub-companion`, and reverse this diff (`e3_state.py` then reads ok on twelve). The client keeps its guard, since
that is its default. Each `PHK1` is then one `bad_packets` on the host again; nothing else changes. To turn the
client's guard off as well: `setprop debug.privyhub.loss_guard 0` (a reboot clears it), or B27's rollback.

**Predecessor sha256** (the tree at B27, 2026-10-27: HEAD `2cd392c` with A's G-A7 diff applied, uncommitted):

```
7258fdd1fa8de4c818b6ff6a983458555dfe40a56f85eb24324baccddb80e5c6  tools/e1_remote.py
df93c308d51291c865578c7687eee0bd09a24181a50370164bea15faca10e7dc  tools/e1_suite.py
6d0c306c1dc98382434b63a4a353eee371965233b569f3cc9b5632089d877df1  tools/e3_state.py
197e4822ba66675780632deaf99b9212c9f8dfaca7d487144a674f55c1e8dd0f  tools/test_e1_remote.py
```

If G-A7 is committed first, these files and their hashes stay the same (the commit does not change their content).

**Checked (in /tmp only, never against the tree):**
- `git apply --check -p1` clean on copies of the four files, then applied in that copy;
- `e1_suite.py --self-test` `E1_SUITE_SELF_TEST_OK`, `ADOPTED` 13 including `PRIVYHUB_LOSS_GUARD=1`;
- `test_e1_remote.py` gives the same outcome as unpatched: 21 run, Gate3's one error from fixtures absent in the
  copy, as at every baseline.

The diff is also kept at `evidence/b27_2026-10-27/g_a8_prepared.diff`.

**The diff** (`git apply -p1`):

```diff
diff --git a/tools/e1_remote.py b/tools/e1_remote.py
--- a/tools/e1_remote.py
+++ b/tools/e1_remote.py
@@ -165,7 +165,7 @@
 
 def preflight_remote(environ_has: Callable[[str], bool], adb_devices: Callable[[], str],
                      adopted: tuple[str, ...] | list[str] = ()) -> dict[str, Any]:
-    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, twelve lines since G-A7); each must be read back too
+    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, thirteen lines since G-A8); each must be read back too
     need = list(REQUIRED_FLAGS) + [kv for kv in adopted if kv not in REQUIRED_FLAGS]
     d = {
         "flags": {kv: environ_has(kv) for kv in need},
diff --git a/tools/e1_suite.py b/tools/e1_suite.py
--- a/tools/e1_suite.py
+++ b/tools/e1_suite.py
@@ -108,8 +108,13 @@
 # (B24; acts only on a guarded start, inside RESTART_FAST) -- through its own drop-in (restart-fast-unlock.conf); the
 # adopted environ is exactly these twelve names
 RESTART_FAST_UNLOCK = "PRIVYHUB_RESTART_FAST_UNLOCK=1"
+# G-A8 (adopted <date>, the user): the loss guard's host side -- the client's keyframe requests (PHK1) parsed, counted and
+# rate-limited (no runtime IDR: they force nothing), the per-minute keyframe_requests row, the heartbeat's loss-guard
+# fields recorded (B10; the client's guard is on by default since B27) -- through its own drop-in (loss-guard.conf); the
+# adopted environ is exactly these thirteen names
+LOSS_GUARD = "PRIVYHUB_LOSS_GUARD=1"
 ADOPTED = sorted([LIVE, INDEX, SNES_CORE, RECOVERY, SNES_CAPTURE, OVERLAY, IDENTITY, AUDIO_CODEC, LINK_REPORT,
-                  LINK_RECOVERY, RESTART_FAST, RESTART_FAST_UNLOCK])
+                  LINK_RECOVERY, RESTART_FAST, RESTART_FAST_UNLOCK, LOSS_GUARD])
 FLAG_NAMES = ["PRIVYHUB_ADAPTIVE_BITRATE_INJECT", "PRIVYHUB_ADAPTIVE_BITRATE_TOP", "PRIVYHUB_PS1_LOOK",
               "PRIVYHUB_NATIVE_PROFILE_ID", "PRIVYHUB_FEC_SCHEME"]
 RA_CFG = Path.home() / ".config/retroarch/config"
@@ -1013,11 +1018,13 @@
          "drop_in_link_recovery": f"Environment={LINK_RECOVERY}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_restart_fast": f"Environment={RESTART_FAST}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_restart_fast_unlock": f"Environment={RESTART_FAST_UNLOCK}" in sh(["systemctl", "--user", "cat", UNIT]),
+         "drop_in_loss_guard": f"Environment={LOSS_GUARD}" in sh(["systemctl", "--user", "cat", UNIT]),
          "e3_dropin_absent": not DROPIN.exists(), "e4_constraint_absent": not E4_DROPIN.exists()}
     d["ok"] = (d["manager"] == [] and d["environ"] == ADOPTED and d["adb"] and d["drop_in_live"] and d["drop_in_index"]
                and d["drop_in_snes_core"] and d["drop_in_recovery"] and d["drop_in_snes_capture"] and d["drop_in_overlay"]
                and d["drop_in_identity"] and d["drop_in_audio_codec"] and d["drop_in_link_report"]
                and d["drop_in_link_recovery"] and d["drop_in_restart_fast"] and d["drop_in_restart_fast_unlock"]
+               and d["drop_in_loss_guard"]
                and d["e3_dropin_absent"] and d["e4_constraint_absent"])
     return d
 
diff --git a/tools/e3_state.py b/tools/e3_state.py
--- a/tools/e3_state.py
+++ b/tools/e3_state.py
@@ -1,5 +1,5 @@
 #!/usr/bin/env python3
-"""E3: the adopted state (since G-A7, twelve: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report, the link-recovery stack, the fast restart, the fast restart unlocked; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
+"""E3: the adopted state (since G-A8, thirteen: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report, the link-recovery stack, the fast restart, the fast restart unlocked, the loss guard's host side; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
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
+        # G-A2: the callers pass e1_suite.ADOPTED (thirteen lines since G-A8); one missing refuses, naming it
         adopted = ("PRIVYHUB_AUDIO_CODEC=opus", R.REQUIRED_FLAGS[0])
         pf = R.preflight_remote(lambda kv: kv in R.REQUIRED_FLAGS, lambda: "", adopted)
         self.assertFalse(pf["ok"])
```
