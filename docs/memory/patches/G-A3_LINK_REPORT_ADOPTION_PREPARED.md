---
memory_schema: 1
as_of: 2026-10-23
baseline_commit: 3eb900c
---

# G-A3 — `PRIVYHUB_LINK_REPORT=1` as the ninth adopted line: PREPARED, NOT APPLIED

**Status: PREPARED by session B (B13), nothing applied.** No drop-in was written, the tree's `tools/` are unchanged,
the companion was not restarted. Adopting it is the user's say-so; session A applies it as G-A3 (below). Record:
`evidence/B13_LINK_REPORT_DEFAULT_ON_2026-10-23.md`.

**What it adopts:** the host records the client's Wi-Fi link fields (RSSI, tx / rx link Mbps, frequency, Wi-Fi
standard) in each heartbeat row (B3; `games/native_stream_heartbeat.py` `LINK_FIELDS`, `plugins/games.py`'s parse).
**Diagnostics only:** no stream, recovery or ladder behaviour reads them. With the B13 APK the client sends them by
default (`debug.privyhub.link_report` absent = on; `0` off), so the `adb shell setprop … 1` after each onn boot is no
longer needed.

## 1. The drop-in (NOT written)

`~/.config/systemd/user/privyhub-companion.service.d/link-report.conf`:

```
[Service]
Environment=PRIVYHUB_LINK_REPORT=1
```

## 2. The tools (NOT applied to the tree; the diff, made and tested in a scratch copy)

| # | file | edit |
| --- | --- | --- |
| 1 | `tools/e1_suite.py` | `LINK_REPORT` defined and in `ADOPTED` (nine); the preflight's `drop_in_link_report` and its `ok` term |
| 2 | `tools/e3_state.py` | the docstring ("since G-A3, nine"); the logic is e1_suite's |
| 3 | `tools/e1_remote.py` | the comment ("nine lines since G-A3"); `preflight_remote` already requires every adopted line it is passed |
| 4 | `tools/test_e1_remote.py` | the comment |

Tested on the scratch copy, before / after (`evidence/b13_2026-10-23/ga3_tests_before_after.txt`):
`e1_suite --self-test` OK both; `len(ADOPTED)` 8 → 9; `test_e1_remote` 21 with the same one error on both sides (its
Gate3 fixture lives under `docs/memory`, absent from a tools-only copy; G-A2 recorded 21 OK from the tree; not run from the tree here).

```diff
diff -ru before/tools/e1_remote.py after/tools/e1_remote.py
--- before/tools/e1_remote.py	2026-10-18 21:49:13.000000000 -0400
+++ after/tools/e1_remote.py	2026-10-23 13:28:16.024949383 -0400
@@ -165,7 +165,7 @@
 
 def preflight_remote(environ_has: Callable[[str], bool], adb_devices: Callable[[], str],
                      adopted: tuple[str, ...] | list[str] = ()) -> dict[str, Any]:
-    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, eight lines); each must be read back too
+    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, nine lines since G-A3); each must be read back too
     need = list(REQUIRED_FLAGS) + [kv for kv in adopted if kv not in REQUIRED_FLAGS]
     d = {
         "flags": {kv: environ_has(kv) for kv in need},
diff -ru before/tools/e1_suite.py after/tools/e1_suite.py
--- before/tools/e1_suite.py	2026-10-22 18:45:03.000000000 -0400
+++ after/tools/e1_suite.py	2026-10-23 13:28:16.020949293 -0400
@@ -80,7 +80,10 @@
 # G-A2 (adopted 2026-10-19, the user): the Opus audio path (G4-W2, CL-B4/B5) through its own drop-in (audio-codec.conf);
 # the adopted environ is exactly these eight names
 AUDIO_CODEC = "PRIVYHUB_AUDIO_CODEC=opus"
-ADOPTED = sorted([LIVE, INDEX, SNES_CORE, RECOVERY, SNES_CAPTURE, OVERLAY, IDENTITY, AUDIO_CODEC])
+# G-A3 (adopted <date>, the user): the client's Wi-Fi link fields recorded in the heartbeat (B3; diagnostics only, no
+# behaviour) through its own drop-in (link-report.conf); the adopted environ is exactly these nine names
+LINK_REPORT = "PRIVYHUB_LINK_REPORT=1"
+ADOPTED = sorted([LIVE, INDEX, SNES_CORE, RECOVERY, SNES_CAPTURE, OVERLAY, IDENTITY, AUDIO_CODEC, LINK_REPORT])
 FLAG_NAMES = ["PRIVYHUB_ADAPTIVE_BITRATE_INJECT", "PRIVYHUB_ADAPTIVE_BITRATE_TOP", "PRIVYHUB_PS1_LOOK",
               "PRIVYHUB_NATIVE_PROFILE_ID", "PRIVYHUB_FEC_SCHEME"]
 RA_CFG = Path.home() / ".config/retroarch/config"
@@ -980,10 +983,12 @@
          "drop_in_overlay": f"Environment={OVERLAY}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_identity": f"Environment={IDENTITY}" in sh(["systemctl", "--user", "cat", UNIT]),
          "drop_in_audio_codec": f"Environment={AUDIO_CODEC}" in sh(["systemctl", "--user", "cat", UNIT]),
+         "drop_in_link_report": f"Environment={LINK_REPORT}" in sh(["systemctl", "--user", "cat", UNIT]),
          "e3_dropin_absent": not DROPIN.exists(), "e4_constraint_absent": not E4_DROPIN.exists()}
     d["ok"] = (d["manager"] == [] and d["environ"] == ADOPTED and d["adb"] and d["drop_in_live"] and d["drop_in_index"]
                and d["drop_in_snes_core"] and d["drop_in_recovery"] and d["drop_in_snes_capture"] and d["drop_in_overlay"]
-               and d["drop_in_identity"] and d["drop_in_audio_codec"] and d["e3_dropin_absent"] and d["e4_constraint_absent"])
+               and d["drop_in_identity"] and d["drop_in_audio_codec"] and d["drop_in_link_report"]
+               and d["e3_dropin_absent"] and d["e4_constraint_absent"])
     return d
 
 
diff -ru before/tools/e3_state.py after/tools/e3_state.py
--- before/tools/e3_state.py	2026-10-18 21:48:58.000000000 -0400
+++ after/tools/e3_state.py	2026-10-23 13:28:16.024949383 -0400
@@ -1,5 +1,5 @@
 #!/usr/bin/env python3
-"""E3: the adopted state (since G-A2, eight: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
+"""E3: the adopted state (since G-A3, nine: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
 import sys, json, importlib.util
 spec=importlib.util.spec_from_file_location('s','/home/privyhub/Projects/onn-stream-test/tools/e1_suite.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
 mp=m.mainpid()
diff -ru before/tools/test_e1_remote.py after/tools/test_e1_remote.py
--- before/tools/test_e1_remote.py	2026-10-18 21:49:13.000000000 -0400
+++ after/tools/test_e1_remote.py	2026-10-23 13:28:16.024949383 -0400
@@ -133,7 +133,7 @@
         self.assertTrue(pf["adb_device"])
 
     def test_the_adopted_set_is_required_too(self):
-        # G-A2: the callers pass e1_suite.ADOPTED (eight lines); one missing refuses, naming it
+        # G-A2: the callers pass e1_suite.ADOPTED (nine lines since G-A3); one missing refuses, naming it
         adopted = ("PRIVYHUB_AUDIO_CODEC=opus", R.REQUIRED_FLAGS[0])
         pf = R.preflight_remote(lambda kv: kv in R.REQUIRED_FLAGS, lambda: "", adopted)
         self.assertFalse(pf["ok"])
```

## 3. The readers that count eight — listed, not changed

- `ADOPTED_E3` in `tools/d7_regression.py` and `tools/c3_l4_nft_night.py` (three names, stale since G-A1; their tests
  assert the three): as at G-A2, left.
- Past evidence drivers with "adopted7" / eight-line checks: records under their manifests.
- `docs/memory/evidence/link_n1_2026-10-23/link_n1_watch.py` (session A's running watch): it loads `tools/e1_suite.py`
  once at its start and reads no `ADOPTED`; applying #1 while it runs does not change it. Not touched.

## 4. G-A3, sketched for session A (only on the user's say-so)

1. `--check` ok on eight lines; only the companion (and `privyhub-link-n1`) active; no game.
2. Apply §2's diff to the tree (`git apply`); `e1_suite --self-test`, `test_e1_remote` (21), `test_c3_l4_nft_night`
   (33) from the tree.
3. Write §1's drop-in; `systemctl --user daemon-reload && systemctl --user restart privyhub-companion` (not during the
   watch's 04:30-05:30Z window).
4. `tools/e3_state.py --check`: ok on **nine** lines; the companion's environ carries `PRIVYHUB_LINK_REPORT=1`.
5. A confirmation window (one E1 SNES stream, 10 min): every heartbeat row carries `link_*` keys with the B13 APK and
   no property set; the host gates as before.
6. Record `evidence/G_A3_LINK_REPORT_ADOPTION_<date>.md`; rename this file `G-A3_LINK_REPORT_ADOPTED.md` in the same
   form as G-A2's.

**Revert (written, not applied):** delete `link-report.conf`, daemon-reload and restart, reverse §2's diff.
