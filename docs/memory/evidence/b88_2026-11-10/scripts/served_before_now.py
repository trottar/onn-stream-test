#!/usr/bin/env python3
"""B88: every call in calls.json against the companion's own HTTP server, HEAD's code vs B88's (test_contract.serve_all
and ps2_round_trip from the B88 copy's tests, the companion/ from each copy). Prints the table: call, method, served
before / now (served = not 404, not 405, no "Unknown … action"), the status codes.
usage: served_before_now.py <HEAD copy> <B88 copy>"""
import sys
from pathlib import Path
head, b88 = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
sys.path.insert(0, str(b88 / "tests/client_contract")); sys.path.insert(0, str(b88 / "tests/art_systems"))
import test_contract as t  # noqa: E402
before, now = t.serve_all(head), t.serve_all(b88)
served = lambda r: r["status"] not in (404, 405, -1) and not r["unknown"]
print("| call | method | served before (HEAD) | served now (B88) |")
print("| --- | --- | --- | --- |")
n_before = n_now = 0
for b, n in zip(before, now):
    assert (b["path"], b["method"]) == (n["path"], n["method"])
    n_before += served(b); n_now += served(n)
    mark = lambda r: ("yes" if served(r) else "**NO**") + f" ({r['status']}{', unknown action' if r['unknown'] else ''})"
    print(f"| `{b['path']}` | {b['method']} | {mark(b)} | {mark(n)} |")
print(f"\nserved: before {n_before} / {len(before)}, now {n_now} / {len(now)}")
for label, code in (("HEAD", head), ("B88", b88)):
    save, details = t.ps2_round_trip(code)
    print(f"{label}: the onn's Save (POST ps2-patches ws=1) -> {save['status']}"
          f"{' (unknown action)' if save['unknown'] else ''}; details' ps2_patches.on after it -> "
          f"{__import__('json').loads(details['body']).get('ps2_patches', {}).get('on') if details['status'] == 200 else details['status']}")
