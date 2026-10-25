#!/usr/bin/env python3
"""B20: `PRIVYHUB_LINK_RECOVERY=1` = exactly the six stack lines; an explicit individual flag wins; absent = today.

    python3 -m unittest discover -s tests/link_recovery -v

Every reader of the six, under the umbrella alone (after `apply`) and under the six set by hand: each module's own
parse, and in fresh processes the modules `plugins/games.py` (loaded alone, constructing nothing) and
`games/emulator_manager.py` import.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import hold_ownership as ho  # noqa: E402
import hold_rewind as hr  # noqa: E402
import hold_tuning as ht  # noqa: E402
import input_hold as ih  # noqa: E402
import link_recovery as lr  # noqa: E402
import rewind_cores as rc  # noqa: E402
import stall_owner as so  # noqa: E402
import stall_signal as ss  # noqa: E402

SIX = {k: "1" for k in lr.STACK}
UMBRELLA = {"PRIVYHUB_LINK_RECOVERY": "1"}
MODULES = ("input_hold", "hold_rewind", "hold_tuning", "stall_signal", "hold_ownership", "stall_owner", "rewind_cores",
           "link_recovery")


def readers(env):
    """Each module's own reading of the six (what each wire acts on)."""
    return {
        "input_hold": ih.parse(env.get(ih.FLAG_ENV)),
        "hold_tuning": ht.enabled(env),
        "hold_ownership": ho.enabled(env),
        "hold_rewind": hr.parse(env),
        "rewind_cores": rc.mode(env),
        "stall_signal": ss.parse(env.get(ss.FLAG_ENV)),
        "stall_owner": so.enabled(env),
    }


CHILD = """
import sys, json, importlib.util
sys.path.insert(0, 'companion')
spec = importlib.util.spec_from_file_location('b20_games', 'companion/plugins/games.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
from games import emulator_manager as em
names = ('_input_hold', '_hold_rewind', '_hold_tuning', '_stall_signal', '_hold_ownership', '_stall_owner')
print(json.dumps({'mods': sorted(x for x in MODULES if x in sys.modules), 'em_hold_rewind': em._hold_rewind is not None,
                  'plugin': {k: getattr(m, k) is not None for k in names}}))
"""


def imported(env_extra):
    """A fresh process: plugins/games.py loaded alone + emulator_manager; which stack modules came in."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
    env.update(env_extra)
    code = CHILD.replace("MODULES", repr(list(MODULES)))
    out = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, env=env, capture_output=True, text=True,
                         timeout=300)
    assert out.returncode == 0, out.stderr[-800:]
    return json.loads(out.stdout.strip().splitlines()[-1])


class TheUmbrellaIsTheSix(unittest.TestCase):
    def test_every_modules_reader_reads_the_same(self):
        env = dict(UMBRELLA)
        done = lr.apply(env)
        self.assertEqual(done["implied"], sorted(lr.STACK))
        self.assertEqual({k: env[k] for k in lr.STACK}, SIX)
        self.assertEqual(readers(env), readers(dict(SIX)))
        self.assertEqual(sorted(set(env) - set(UMBRELLA)), sorted(lr.STACK))      # nothing more

    def test_in_fresh_processes_the_same_modules_come_in(self):
        a = imported(UMBRELLA)
        b = imported(SIX)
        self.assertEqual(a["plugin"], b["plugin"])
        self.assertTrue(all(a["plugin"].values()))
        self.assertEqual(a["em_hold_rewind"], b["em_hold_rewind"])
        self.assertTrue(a["em_hold_rewind"])
        self.assertEqual([m for m in a["mods"] if m != "link_recovery"], b["mods"])
        self.assertIn("link_recovery", a["mods"])

    def test_an_explicit_flag_wins(self):
        env = dict(UMBRELLA, PRIVYHUB_STALL_RESUME="0")
        done = lr.apply(env)
        self.assertEqual(done["explicit"], {"PRIVYHUB_STALL_RESUME": "0"})
        self.assertEqual(env["PRIVYHUB_STALL_RESUME"], "0")
        got, by_hand = readers(env), readers(dict(SIX, PRIVYHUB_STALL_RESUME="0"))
        self.assertEqual(got, by_hand)
        self.assertFalse(got["stall_owner"][0])                                    # that part off
        self.assertTrue(got["hold_ownership"][0] and got["hold_tuning"][0] and got["hold_rewind"][0])

    def test_not_one_implies_nothing(self):
        for v in ("0", "yes", "", " 2 "):
            env = {"PRIVYHUB_LINK_RECOVERY": v}
            self.assertEqual(lr.apply(env)["implied"], [], v)
            self.assertEqual(set(env), {"PRIVYHUB_LINK_RECOVERY"})

    def test_apply_is_idempotent(self):
        env = dict(UMBRELLA)
        lr.apply(env)
        again = lr.apply(env)
        self.assertEqual(again["implied"], [])
        self.assertEqual({k: env[k] for k in lr.STACK}, SIX)


class Absent(unittest.TestCase):
    def test_absent_nothing_read_nothing_imported(self):
        a = imported({})
        self.assertEqual(a["mods"], [])
        self.assertFalse(any(a["plugin"].values()))
        self.assertFalse(a["em_hold_rewind"])


class TheReader(unittest.TestCase):
    def test_describe(self):
        self.assertIsNone(lr.describe(["PRIVYHUB_LINK_REPORT=1"]))
        d = lr.describe(["PRIVYHUB_LINK_RECOVERY=1", "PRIVYHUB_STALL_RESUME=0", "PRIVYHUB_LINK_REPORT=1"])
        self.assertTrue(d["on"])
        self.assertEqual(d["stack"]["PRIVYHUB_STALL_RESUME"], "explicit 0")
        self.assertEqual([k for k, v in d["stack"].items() if v == "implied 1"], [k for k in lr.STACK if k != "PRIVYHUB_STALL_RESUME"])
        self.assertFalse(lr.describe(["PRIVYHUB_LINK_RECOVERY=0"])["on"])


if __name__ == "__main__":
    unittest.main()
