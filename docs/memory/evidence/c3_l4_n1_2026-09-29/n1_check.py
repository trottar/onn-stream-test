#!/usr/bin/env python3
"""C3-L4-N1: check one `--only F1,F3` fake-sudo run.

    python3 n1_check.py <run dir> <fake sudo dir> <harness exit code>

L2B's checks (the fault removed and confirmed absent, no rule after the last
delete, teardown clean, flags absent; c3_l4_l2_2026-09-29/l2b/l2b_check.py,
run unchanged) plus the subset's: only F1 and F3 ran, in that order; F2 and K
never started; the pre-registration hashed is night 2's.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
run, fake, rc = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
base = subprocess.run([sys.executable, str(HERE.parent / "c3_l4_l2_2026-09-29" / "l2b" / "l2b_check.py"),
                       str(run), str(fake)], capture_output=True, text=True)
print(base.stdout.rstrip())
summ = json.loads((run / "summary.json").read_text())
ev = [json.loads(l) for l in (run / "events.jsonl").read_text().splitlines() if l.strip()]
log = (run / "harness.log").read_text()
played = [e["session"] for e in ev if e.get("event") == "playing"]
n2 = hashlib.sha256((HERE / "c3_l4_nft_night2_preregistration.txt").read_bytes()).hexdigest()
aborted = "error" in summ or "aborted_by" in summ
checks = {
    "L2B's checks": base.returncode == 0,
    "sessions in the summary are F1, F3": list(summ.get("sessions", {})) == ["F1", "F3"],
    "PLAYING only for F1 then F3": played == ["F1", "F3"],
    "no F2 or K banner": "F2 --" not in log and "K --" not in log,
    "the pre-registration hashed is night 2's": summ.get("preregistration_sha256") == n2,
    "exit code: 0 for the full run, 4 (error) for the forced exception": rc == (4 if aborted else 0),
}
if not aborted:
    checks["every expected file present"] = summ.get("complete") is True
for k, v in checks.items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
print(f"  => N1 {'PASS' if all(checks.values()) else 'FAIL'}")
sys.exit(0 if all(checks.values()) else 1)
