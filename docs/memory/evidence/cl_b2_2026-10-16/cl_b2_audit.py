#!/usr/bin/env python3
"""CL-B2: the session audit (logs/session_audit.jsonl, gitignored) reduced for the record, and the client's identity log.
Read-only. Each kept row: t, event, reason, routing_evidence, host_local, path, permission, permissions, client_id as
'dev-' + its first 4 hex + '...' (or legacy-lan / host-local), expires_in_s. token_ref and anything else are dropped.

    cl_b2_audit.py <label> <since_utc> [<until_utc>]   -> audit_<label>.jsonl + audit_<label>_counts.json
    cl_b2_audit.py --logcat <label> <since 'MM-DD HH:MM:SS.000' UTC>  -> logcat_<label>.txt (PrivyHubIdentity lines,
                    any IPv4-like or long-hex run replaced before writing)
"""
import collections
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
AUDIT = os.path.join(REPO, "logs/session_audit.jsonl")
KEEP = ("t", "event", "reason", "routing_evidence", "host_local", "path", "permission", "permissions", "expires_in_s")
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
HEX = re.compile(r"\b[0-9a-f]{16,}\b")


def cid(c):
    return (c[:8] + "...") if isinstance(c, str) and c.startswith("dev-") else c


def audit(label, since, until=None):
    rows = []
    if os.path.exists(AUDIT):
        for l in open(AUDIT):
            try:
                r = json.loads(l)
            except ValueError:
                continue
            if r.get("t", "") >= since and (until is None or r.get("t", "") <= until):
                x = {k: r[k] for k in KEEP if k in r}
                if "client_id" in r:
                    x["client_id"] = cid(r["client_id"])
                rows.append(x)
    with open(os.path.join(HERE, f"audit_{label}.jsonl"), "w") as fh:
        for x in rows:
            fh.write(json.dumps(x, sort_keys=True) + "\n")
    c = collections.Counter((x["event"], x.get("client_id"), x.get("reason")) for x in rows)
    counts = {"label": label, "since": since, "until": until, "audit_exists": os.path.exists(AUDIT), "rows": len(rows),
              "by_event_client_reason": [{"event": e, "client_id": k, "reason": r, "n": n} for (e, k, r), n in sorted(c.items(), key=str)]}
    json.dump(counts, open(os.path.join(HERE, f"audit_{label}_counts.json"), "w"), indent=1)
    print(json.dumps(counts))


def logcat(label, since):
    out = subprocess.run(["adb", "logcat", "-d", "-v", "UTC", "-T", since, "-s", "PrivyHubIdentity:*"],
                         capture_output=True, text=True, timeout=60).stdout
    out = HEX.sub("<hex>", IPV4.sub("<addr>", out))
    open(os.path.join(HERE, f"logcat_{label}.txt"), "w").write(out)
    print(out[-3000:])


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "--logcat":
        logcat(a[1], a[2])
    else:
        audit(a[0], a[1], a[2] if len(a) > 2 else None)
