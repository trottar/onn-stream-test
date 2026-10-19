#!/usr/bin/env python3
"""G8-S5 record: each cell's heartbeat figures over the first 235.4 s of its window (cell A's first client pause at
14:53:52.378Z), by tools/e1_suite.py's own heartbeat_figures (the same reading as the window's figures; read-only).
Writes split_heartbeat.json next to this script."""
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
spec = importlib.util.spec_from_file_location("e1_suite", REPO / "tools/e1_suite.py")
E1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E1)
rr = json.loads((HERE / "record_read.json").read_text())
span = rr["split_s"]
out = {"split_s": span}
for k, v in rr["cells"].items():
    w0 = v["window"]["from"]
    t0 = datetime.strptime(w0, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    t1 = (t0 + timedelta(seconds=span)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    out[k] = {"from": w0, "to": t1, "first_split": E1.heartbeat_figures(w0, t1),
              "window_check": E1.heartbeat_figures(w0, v["window"]["to"])}
(HERE / "split_heartbeat.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
