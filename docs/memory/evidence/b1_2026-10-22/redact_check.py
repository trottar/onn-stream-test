#!/usr/bin/env python3
"""B1 (CL-B7P's check, reused): no address or identifier in the files this task wrote. CL-B6's check without adb (this task runs no adb)
and without reading the hub's device store (nothing from it was read or written here). Secrets loaded in process,
never printed: the host's IPv4 addresses and its host name. Also any IPv4-shaped literal (not loopback / 0.0.0.0),
MAC-shaped literal, a name-colon-5555 adb endpoint.
The host name is skipped when it equals the project's own name (any case): it then appears legitimately in every
class and path name and says nothing about the network. Prints one line per file: OK / FAIL (the kind, never the value)."""
import ipaddress, re, socket, subprocess, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
_h = socket.gethostname()
secrets = set() if _h.lower() == "privyhub" else {("host_name", _h)}
for a in re.findall(r"inet (\d+\.\d+\.\d+\.\d+)", subprocess.run(["ip", "-4", "addr"], capture_output=True, text=True).stdout):
    if not a.startswith("127."):
        secrets.add(("host_address", a))
secrets = {(k, v) for k, v in secrets if v and len(v) > 3}
fails = 0
for f in [Path(p).resolve() for p in sys.argv[1:]]:
    for p in ([f] if f.is_file() else sorted(x for x in f.rglob("*") if x.is_file())):
        if p.name == "redact_check.txt":
            continue
        text = p.read_text(errors="replace")
        bad = sorted({k for k, v in secrets if re.search(r"(?<![\w.-])" + re.escape(v) + r"(?![\w-])", text)})
        for m in re.findall(r"(?<![\d.])(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?![\d.])", text):
            try:
                ip = ipaddress.ip_address(m)
            except ValueError:
                continue
            if not ip.is_loopback and str(ip) != "0.0.0.0":
                bad.append("ipv4_literal")
        if re.search(r"\b[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}\b", text):
            bad.append("mac_literal")
        if re.search(r"\b[\w.-]+:5555\b", text):
            bad.append("adb_endpoint")
        print(("FAIL " + ",".join(sorted(set(bad))) if bad else "OK"), p.relative_to(REPO))
        fails += bool(bad)
print("FAILS", fails)
