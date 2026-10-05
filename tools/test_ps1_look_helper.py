#!/usr/bin/env python3
"""C5-M5B: tools/ps1_look.sh fake-run (pre-registered, c5_m5b_preregistration.txt section 5). systemctl,
curl and adb are stubs on PATH that record every call and keep a tiny state (the user manager's
environment, the companion's environ, PLAYING, the rung); the helper is run for each look with Enter on
stdin, and the order of its calls and its final verification are checked. Nothing real is touched."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HELPER = REPO / "tools" / "ps1_look.sh"

STUB_SYSTEMCTL = r'''#!/usr/bin/env python3
import json, os, sys
d = os.environ["FAKE_DIR"]; st = json.load(open(d + "/state.json"))
a = sys.argv[1:]
open(d + "/calls.log", "a").write("systemctl " + " ".join(a) + "\n")
if a[:2] == ["--user", "show-environment"]:
    print("HOME=/home/x"); [print(k + "=" + v) for k, v in sorted(st["mgr"].items())]
elif a[:2] == ["--user", "set-environment"]:
    for kv in a[2:]:
        k, v = kv.split("=", 1); st["mgr"][k] = v
elif a[:2] == ["--user", "unset-environment"]:
    for k in a[2:]: st["mgr"].pop(k, None)
elif a[:2] == ["--user", "restart"]:
    env = dict(st["mgr"]); env["PRIVYHUB_ADAPTIVE_BITRATE_MODE"] = "live"
    os.makedirs(d + "/proc/4242", exist_ok=True)
    open(d + "/proc/4242/environ", "w").write("\0".join(k + "=" + v for k, v in sorted(env.items())) + "\0")
    st.update(comp=env, rung=False, active=False, polls=st["polls_to_playing"])
elif a[:2] == ["--user", "show"]:
    print("4242")
json.dump(st, open(d + "/state.json", "w"))
'''
STUB_CURL = r'''#!/usr/bin/env python3
import json, os, sys
d = os.environ["FAKE_DIR"]; st = json.load(open(d + "/state.json"))
a = sys.argv[1:]
url = next(x for x in a if "localhost:8765" in x); post = "POST" in a
open(d + "/calls.log", "a").write("curl " + ("POST " if post else "") + url.split("8765", 1)[1] + "\n")
out = None
if url.endswith("/plugins/games/status"):
    if st.get("active") or st["user_starts"]:
        st["polls"] -= 1
    out = {"active": st.get("active"), "recovery": {"state": "PLAYING" if st["polls"] <= 0 else "IDLE"}}
elif "native-stream-status" in url:
    r = st.get("rung")
    out = {"bitrate_kbps": 12600 if r else 7000, "width": 1920 if r else 1280, "height": 1080 if r else 720,
           "adaptive_bitrate": {"mode": "live"}, "encoder_overrides": {"any_override": False}}
elif "inject?class=INCREASE_1080P" in url:
    st["rung"] = st["comp"].get("PRIVYHUB_ADAPTIVE_BITRATE_INJECT") == "1" and \
                 st["comp"].get("PRIVYHUB_ADAPTIVE_BITRATE_TOP") == "1080p"
    out = {"ok": st["rung"]}
elif url.endswith("/plugins/games/stop"):
    st.update(active=False, rung=False, polls=10**6)
    out = {"ok": True}
elif "/plugins/games/launch" in url:
    st["active"] = True; out = {"ok": True}
json.dump(st, open(d + "/state.json", "w"))
if out is not None and "/dev/null" not in a:
    print(json.dumps(out))
'''
STUB_ADB = r'''#!/bin/sh
echo "adb $*" >> "$FAKE_DIR/calls.log"
'''


class FakeRun(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        (self.d / "bin").mkdir()
        for name, body in (("systemctl", STUB_SYSTEMCTL), ("curl", STUB_CURL), ("adb", STUB_ADB)):
            p = self.d / "bin" / name
            p.write_text(body)
            p.chmod(0o755)
        (self.d / "opt").mkdir()
        (self.d / "opt" / "Beetle PSX HW.opt").write_text('beetle_psx_hw_internal_resolution = "4x"\n')
        (self.d / "opt" / "Beetle PSX HW.cfg").write_text('video_fullscreen = "true"\n')

    def run_helper(self, look, *, extra=(), offered="4x remaster", at_rung="1", user_starts=True,
                   polls=3, wait_s=20, stdin="\n"):
        (self.d / "state.json").write_text(json.dumps({"mgr": {}, "comp": {}, "rung": False, "active": False,
                                                       "polls": polls, "polls_to_playing": polls,
                                                       "user_starts": user_starts}))
        (self.d / "calls.log").write_text("")
        env = dict(os.environ, PATH=f"{self.d / 'bin'}:{os.environ['PATH']}", FAKE_DIR=str(self.d),
                   PS1_LOOK_PROC=str(self.d / "proc"), PS1_LOOK_OPT_DIR=str(self.d / "opt"),
                   PS1_LOOK_WAIT_S=str(wait_s), PS1_LOOK_SETTLE_S="0", PS1_LOOK_STEP_S="0")
        if offered is not None:
            env["PS1_LOOK_TEST_OFFERED"] = offered
            env["PS1_LOOK_TEST_AT_RUNG"] = at_rung
        r = subprocess.run(["bash", str(HELPER), look, *extra], input=stdin, capture_output=True, text=True,
                           env=env, timeout=60)
        calls = (self.d / "calls.log").read_text().splitlines()
        st = json.loads((self.d / "state.json").read_text())
        return r, calls, st

    def order(self, calls, *needles):
        idx = []
        for n in needles:
            start = idx[-1] + 1 if idx else 0
            hit = next((i for i in range(start, len(calls)) if n in calls[i]), None)
            self.assertIsNotNone(hit, f"{n!r} not found in order after {needles[:len(idx)]}:\n" + "\n".join(calls))
            idx.append(hit)
        return idx

    def assert_restored(self, r, st):
        self.assertIn("ADOPTED STATE VERIFIED", r.stdout, r.stdout)
        self.assertEqual(st["mgr"], {})
        self.assertEqual(st["comp"], {"PRIVYHUB_ADAPTIVE_BITRATE_MODE": "live"})

    def test_4x_sets_no_flag_and_restores(self):
        r, calls, st = self.run_helper("4x")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse([c for c in calls if "--user set-environment" in c])
        self.order(calls, "--user restart", "games/status", "POST /plugins/games/stop",
                   "unset-environment PRIVYHUB_PS1_LOOK PRIVYHUB_ADAPTIVE_BITRATE_TOP PRIVYHUB_ADAPTIVE_BITRATE_INJECT",
                   "--user restart", "native-stream-status")
        self.assertNotIn("inject", "\n".join(calls))
        self.assert_restored(r, st)

    def test_remaster_sets_the_look_only(self):
        r, calls, st = self.run_helper("remaster")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.order(calls, "set-environment PRIVYHUB_PS1_LOOK=remaster", "--user restart", "games/status",
                   "POST /plugins/games/stop", "unset-environment", "--user restart")
        self.assertFalse([c for c in calls if "ADAPTIVE_BITRATE_TOP=" in c])
        self.assertIn("companion restarted; its environ: 'PRIVYHUB_ADAPTIVE_BITRATE_MODE=live PRIVYHUB_PS1_LOOK=remaster'",
                      r.stdout)
        self.assert_restored(r, st)

    def test_remaster_1080p_injects_the_entry_and_sees_1080p(self):
        r, calls, st = self.run_helper("remaster-1080p")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.order(calls, "set-environment PRIVYHUB_PS1_LOOK=remaster",
                   "set-environment PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p PRIVYHUB_ADAPTIVE_BITRATE_INJECT=1",
                   "--user restart", "games/status", "POST /plugins/games/adaptive-bitrate/inject?class=INCREASE_1080P",
                   "native-stream-status", "POST /plugins/games/stop", "unset-environment", "--user restart")
        self.assertIn("the stream is at the 1080p rung: 12,600 kbps, 1920x1080", r.stdout)
        self.assertIn("IDR pulse every 250 ms", r.stdout)
        self.assert_restored(r, st)

    def test_attract_launches_the_title_and_opens_the_app(self):
        r, calls, st = self.run_helper("4x", extra=("--attract",), user_starts=False)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.order(calls, "--user restart", "POST /plugins/games/launch?id=game_ps1_b0a5986638f61a11",
                   "adb shell am start -n com.safeiot.privyhub/.MainActivity", "games/status", "POST /plugins/games/stop")
        self.assert_restored(r, st)

    def test_playing_never_reached_still_restores(self):
        r, calls, st = self.run_helper("remaster", user_starts=False, wait_s=0)
        self.assertEqual(r.returncode, 5, r.stdout)
        self.assertIn("PLAYING not reached", r.stdout)
        self.assert_restored(r, st)

    def test_not_offered_changes_nothing(self):
        r, calls, st = self.run_helper("remaster", offered="4x", at_rung="0")
        self.assertEqual(r.returncode, 3)
        self.assertFalse([c for c in calls if "--user set-environment" in c or "restart" in c])
        r, calls, st = self.run_helper("remaster-1080p", offered="4x remaster", at_rung="0")
        self.assertEqual(r.returncode, 3)
        self.assertFalse([c for c in calls if "--user set-environment" in c or "restart" in c])

    def test_offered_list_comes_from_the_module_when_not_overridden(self):
        r, calls, st = self.run_helper("remaster-1080p", offered=None)
        from importlib import import_module
        import sys
        sys.path.insert(0, str(REPO / "companion"))
        look = import_module("games.ps1_look")
        if "remaster" not in look.PRESETS or not look.REMASTER_AT_RUNG_OFFERED:
            self.assertEqual(r.returncode, 3)
            self.assertFalse([c for c in calls if "--user set-environment" in c])
        else:
            self.assertEqual(r.returncode, 0, r.stdout)

    def test_a_flag_already_set_refuses(self):
        (self.d / "state.json").write_text("{}")
        r, calls, st = self.run_helper("4x")
        # pre-set a flag, then run again
        st_path = self.d / "state.json"
        s = json.loads(st_path.read_text()); s["mgr"] = {"PRIVYHUB_FEC_SCHEME": "x"}; st_path.write_text(json.dumps(s))
        env = dict(os.environ, PATH=f"{self.d / 'bin'}:{os.environ['PATH']}", FAKE_DIR=str(self.d),
                   PS1_LOOK_PROC=str(self.d / "proc"), PS1_LOOK_OPT_DIR=str(self.d / "opt"),
                   PS1_LOOK_TEST_OFFERED="4x remaster", PS1_LOOK_TEST_AT_RUNG="1")
        r = subprocess.run(["bash", str(HELPER), "4x"], input="\n", capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(r.returncode, 4, r.stdout)


if __name__ == "__main__":
    unittest.main()
