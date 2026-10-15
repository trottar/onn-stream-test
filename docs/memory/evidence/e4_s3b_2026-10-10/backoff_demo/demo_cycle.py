#!/usr/bin/env python3
"""E4-S3B -- the runner's refresh-loop back-off shown: one 60-s EpgCycle (tools/e1_suite.py's, or the predecessor
copy beside this file) against the companion as it is (running, or stopped), its rows counted by kind.

    demo_cycle.py <new|predecessor> <out.jsonl> [seconds]
"""
import collections
import json
import sys
import threading
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
which, out = sys.argv[1], Path(sys.argv[2])
secs = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0
src = HERE / "e1_suite_predecessor.py" if which == "predecessor" else REPO / "tools/e1_suite.py"
mod = types.ModuleType("e1_suite_" + which)
mod.__file__ = str(REPO / "tools/e1_suite.py")          # the module derives REPO from its own path
exec(compile(src.read_text(), str(src), "exec"), mod.__dict__)

stop = threading.Event()
t0 = mod.utc()
cyc = mod.EpgCycle(out, stop)
cyc.start()
time.sleep(secs)
stop.set()
cyc.join(timeout=160)
t1 = mod.utc()
rows = [json.loads(l) for l in out.read_text().splitlines()]
res = {"code": which, "source": str(src.relative_to(REPO)), "from": t0, "to": t1, "rows": len(rows),
       "by_kind": dict(collections.Counter(r["kind"] for r in rows)),
       "grab_http": dict(collections.Counter(str(r.get("http")) for r in rows if r["kind"] == "grab")),
       "epg_figures": mod.epg_figures(out, t0, t1)}
print(json.dumps(res))
