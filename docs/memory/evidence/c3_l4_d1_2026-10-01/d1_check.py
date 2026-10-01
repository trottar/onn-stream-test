#!/usr/bin/env python3
"""C3-L4-D1: check one fake-sudo harness run against the new end state (live by default).

    python3 d1_check.py <run dir> <fake sudo dir> <harness exit code>

L2B's fault checks (c3_l4_l2_2026-09-29/l2b/l2b_check.py's, restated: the fake's calls are only -v,
-n -v and -n nft; the delete logged; list tables after it shows no privyhub_fault; no rule after the
last delete; the fake table absent), with the teardown's end state changed: flags after are exactly
the drop-in's PRIVYHUB_ADAPTIVE_BITRATE_MODE=live, the baseline mode is live, live came up by
default (no set-environment), and the system now reads the same (manager none, environ the one
name, adaptive_bitrate.mode live)."""
import json, subprocess, sys, urllib.request
from pathlib import Path

LIVE = "PRIVYHUB_ADAPTIVE_BITRATE_MODE=live"
run, fake, rc = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
cmds = [json.loads(l) for l in (run / "nft_commands.jsonl").read_text().splitlines()] \
    if (run / "nft_commands.jsonl").exists() else []
argv = [json.loads(l)["argv"] for l in (fake / "argv.jsonl").read_text().splitlines()]
summ = json.loads((run / "summary.json").read_text())
ev = [json.loads(l) for l in (run / "events.jsonl").read_text().splitlines() if l.strip()]
state = json.loads((fake / "state.json").read_text()) if (fake / "state.json").exists() else {"table": False}
kinds = [c["kind"] for c in cmds]
last_del = max((i for i, k in enumerate(kinds) if k == "delete_table"), default=-1)
after = kinds[last_del + 1:]
final_list = next((c for c in cmds[last_del + 1:] if c["kind"] == "list_tables"), None)
not_nft = [a for a in argv if a not in (["-v"], ["-n", "-v"]) and a[:2] != ["-n", "nft"]]
live_on = [e for e in ev if e.get("event") == "live_on"]
mgr = [l for l in subprocess.run(["systemctl", "--user", "show-environment"], capture_output=True,
                                 text=True).stdout.splitlines() if l.startswith("PRIVYHUB_")]
mp = subprocess.run(["systemctl", "--user", "show", "-p", "MainPID", "--value", "privyhub-companion"],
                    capture_output=True, text=True).stdout.strip()
envp = sorted(e.decode() for e in Path(f"/proc/{mp}/environ").read_bytes().split(b"\0") if e.startswith(b"PRIVYHUB_"))
st = json.load(urllib.request.urlopen("http://localhost:8765/plugins/games/native-stream-status", timeout=10))
aborted = "error" in summ or "aborted_by" in summ
checks = {
    "every fake-sudo call is -v, -n -v or -n nft": not not_nft,
    "the delete-table call is logged": last_del >= 0,
    "list tables after the last delete, rc 0, no privyhub_fault":
        bool(final_list) and final_list["rc"] == 0 and "privyhub_fault" not in final_list["output"],
    "no rule added after the last delete": not any(k.endswith("_rule") or k in ("add_table", "add_chain") for k in after),
    "summary no_fault_table_at_end": summ.get("no_fault_table_at_end") is True,
    "fake table absent at the end": state.get("table") is False,
    "live came up by default (live_on by_default, no set-environment)":
        len(live_on) == 1 and live_on[0].get("by_default") is True and live_on[0].get("flags") == [LIVE],
    "teardown clean against the baseline": summ.get("teardown_clean") is True,
    "baseline recorded: live, environ the one name":
        summ.get("baseline_mode") == "live" and summ.get("baseline_environ") == [LIVE],
    "flags after are exactly the drop-in's name": summ.get("flags_after") == [LIVE],
    "now: manager PRIVYHUB_* none": mgr == [],
    "now: companion environ exactly the one name": envp == [LIVE],
    "now: adaptive_bitrate.mode live, configured live, acts true":
        (st.get("adaptive_bitrate") or {}).get("mode") == "live"
        and (st.get("adaptive_bitrate") or {}).get("configured_mode") == "live"
        and (st.get("adaptive_bitrate") or {}).get("acts") is True,
    "now: stream 7000, any_override false": st.get("bitrate_kbps") == 7000
        and (st.get("encoder_overrides") or {}).get("any_override") is False,
    "exit code: 0 for the full run, 4 (error) for the forced exception": rc == (4 if aborted else 0),
}
if not aborted:
    checks["every expected file present"] = summ.get("complete") is True
print(f"run {run.name}: aborted_by {summ.get('aborted_by')} error {summ.get('error')}; sessions {list(summ.get('sessions', {}))}")
for k, v in checks.items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
print(f"  => D1 {'PASS' if all(checks.values()) else 'FAIL'}")
sys.exit(0 if all(checks.values()) else 1)
