#!/usr/bin/env python3
"""B90: PRIVYHUB_CHEAT_STAGED=0 = today, byte for byte. The same fixture launches through the companion's real HTTP
server (tests/b90_cheat_staged's child), once on HEAD's code and once on B90's with the knob 0: the whole launch answer,
the session config RetroArch reads, the staged cheat file, the fake RetroArch's counts, the status read, the recovery
rows — compared after removing what differs run to run (times, pids, temp paths, the log's timestamped name, the free command port).
    python3 -I -B proof_absent.py <head_copy> <b90_copy>
"""
import json, re, sys, importlib.util
from pathlib import Path

def load(root):
    sys.path[:0] = [str(Path(root) / "tests/art_systems"), str(Path(root) / "tests/b87_cheat_ready")]
    for m in [k for k in sys.modules if k.startswith("test_b8") or k == "_tmp_cleanup"]:
        del sys.modules[m]
    spec = importlib.util.spec_from_file_location("tb90_" + str(abs(hash(root))), Path(root) / "tests/b90_cheat_staged/test_b90.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    mod.CHILD = mod.CHILD.replace("    out[\"status\"], out[\"error\"] = status, body.get(\"error\")",
        "    out[\"status\"], out[\"error\"] = status, body.get(\"error\")\n    out[\"body\"] = body")
    mod.CHILD = mod.CHILD.replace("httpd.shutdown()", "out['config'] = (root / 'data/games/retroarch/config/privyhub-session.cfg').read_text()\nhttpd.shutdown()")
    return mod

def norm(x, root):
    s = json.dumps(x, sort_keys=True).replace(str(root), "<root>")
    s = re.sub(r'"(elapsed|elapsed_seconds|time_unix|started_at[a-z_]*|seconds|pid|at_utc|launched_at[a-z_]*|last_played[a-z_]*)": [^,}]+', r'"\1": "<t>"', s)
    s = re.sub(r"\d{8}[T-]\d{6}Z?", "<stamp>", s)
    s = re.sub(r'network_cmd_port = \\"\d+\\"', "network_cmd_port = <port>", s)     # a free port, per run
    s = re.sub(r'"(port|network_cmd_port)": \d+', r'"\1": "<port>"', s)
    s = re.sub(r"b82_[A-Za-z0-9_]+", "<tmp>", s)
    return s

head, b90 = sys.argv[1], sys.argv[2]
cases = [("n64, 40 entries, a pick + its must-be-on code", "n64", 40, "30", dict(load_at=0.05, run_at=0.0)),
         ("n64 slow core (lost pulses first)", "n64", 40, "5,11", dict(load_at=0.05, run_at=0.6)),
         ("ps1", "ps1", 40, "2", dict(load_at=0.0, run_at=0.0)),
         ("snes (under bsnes today)", "snes", 20, "1", dict(load_at=0.05, run_at=0.0)),
         ("a client that hangs up", "n64", 40, "30", dict(load_at=0.05, run_at=1.5, hang_up_after=0.3))]
same = 0
for name, system, n, picks, fake in cases:
    outs = []
    for code in (head, b90):
        mod = load(code)
        root, ids = mod.tree(n)
        key = {"n64": mod.b85.N64_TITLE, "ps1": mod.b85.PS1_TITLE, "snes": mod.SNES_TITLE}[system]
        out = mod.launch(root, mod.OFF, ids[key], picks, **fake)
        outs.append(norm(out, root))
    eq = outs[0] == outs[1]
    same += eq
    print(("SAME " if eq else "DIFF ") + name + f"  ({len(outs[0])} chars compared)")
    if not eq:
        import difflib
        print("\n".join(list(difflib.unified_diff(outs[0].split(", "), outs[1].split(", "), lineterm=""))[:40]))
print(f"{same} / {len(cases)} SAME")
