#!/usr/bin/env python3
"""C3-L4-L2B: check one fake-sudo harness run: the fault removed, confirmed absent, teardown clean.

    python3 l2b_check.py <run dir> <fake sudo dir>
"""
import json
import sys
from pathlib import Path

run, fake = Path(sys.argv[1]), Path(sys.argv[2])
cmds = [json.loads(l) for l in (run / "nft_commands.jsonl").read_text().splitlines()] \
    if (run / "nft_commands.jsonl").exists() else []
argv = [json.loads(l)["argv"] for l in (fake / "argv.jsonl").read_text().splitlines()]
summ = json.loads((run / "summary.json").read_text())
state = json.loads((fake / "state.json").read_text()) if (fake / "state.json").exists() else {"table": False}
kinds = [c["kind"] for c in cmds]
last_del = max((i for i, k in enumerate(kinds) if k == "delete_table"), default=-1)
after = kinds[last_del + 1:]
final_list = next((c for c in cmds[last_del + 1:] if c["kind"] == "list_tables"), None)
not_nft = [a for a in argv if a not in (["-v"], ["-n", "-v"]) and a[:2] != ["-n", "nft"]]
checks = {
    "every fake-sudo call is -v, -n -v or -n nft": not not_nft,
    "the delete-table call is logged": last_del >= 0,
    "list tables after the last delete, rc 0, no privyhub_fault":
        bool(final_list) and final_list["rc"] == 0 and "privyhub_fault" not in final_list["output"],
    "no rule added after the last delete": not any(k.endswith("_rule") or k in ("add_table", "add_chain") for k in after),
    "summary no_fault_table_at_end": summ.get("no_fault_table_at_end") is True,
    "teardown clean (flag absent, stream 7000, game inactive, mode off)": summ.get("teardown_clean") is True,
    "flags after": summ.get("flags_after") == [],
    "fake table absent at the end": state.get("table") is False,
}
print(f"run {run.name}: aborted_by {summ.get('aborted_by')} stopped {summ.get('stopped')} error {summ.get('error')}")
print(f"  nft/sudo calls {len(cmds)}; kinds after the last delete {after}")
for k, v in checks.items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
print(f"  => {'PASS' if all(checks.values()) else 'FAIL'}")
sys.exit(0 if all(checks.values()) else 1)
