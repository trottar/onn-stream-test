#!/usr/bin/env python3
"""CL-B3: poll the hub's status documents on loopback every 30 s for N seconds, read-only, and keep reduced fields only.
usage: cl_b3_poll.py <out.jsonl> <seconds> [--wan]
  always: /session/status -> mode, paired_devices, active_sessions, per session {kind, permissions, media_token_live,
          expires_in_s} (client_id dropped); /plugins/games/status -> state / active only.
  --wan:  /status -> `wan` (or absent), /diagnostics/stream-telemetry -> `wan` (or absent); the wan objects are
          written whole after an address / long-hex check (any match is replaced by "<redacted>" and counted)."""
import json, re, sys, time, urllib.request, datetime
B = "http://localhost:8765"
IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b|\b[0-9a-fA-F]{32,}\b")
def get(p):
    try:
        with urllib.request.urlopen(B + p, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"__error__": type(e).__name__}
def scrub(o, n):
    s = json.dumps(o)
    hits = len(IP.findall(s))
    n[0] += hits
    return json.loads(IP.sub("<redacted>", s)) if hits else o
out, secs, wan = sys.argv[1], int(sys.argv[2]), "--wan" in sys.argv
end = time.time() + secs
with open(out, "a") as f:
    while time.time() < end:
        row = {"at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        ss = get("/session/status")
        row["session"] = {k: ss.get(k) for k in ("mode", "paired_devices", "active_sessions", "legacy_unpaired_lan")}
        row["session"]["sessions"] = [{k: s.get(k) for k in ("kind", "permissions", "media_token_live", "expires_in_s")}
                                      for s in ss.get("sessions", [])]
        gs = get("/plugins/games/status")
        row["game"] = {k: gs.get(k) for k in ("active", "state", "playing") if k in gs}
        if wan:
            n = [0]
            st = get("/status"); dt = get("/diagnostics/stream-telemetry")
            row["status_has_wan"] = "wan" in st
            row["status_wan"] = scrub(st.get("wan"), n)
            row["telemetry_has_wan"] = "wan" in dt
            row["telemetry_wan"] = scrub(dt.get("wan"), n)
            row["redacted_matches"] = n[0]
        f.write(json.dumps(row) + "\n"); f.flush()
        time.sleep(30)
