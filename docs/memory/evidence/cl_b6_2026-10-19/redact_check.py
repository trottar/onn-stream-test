#!/usr/bin/env python3
"""CL-B4: no address or identifier in the files this task wrote. Secrets are loaded in process and never printed:
the paired device ids and keys (the hub's store), the adb endpoint, the host's IPv4 addresses. Also any IPv4-shaped
literal (except the RetroArch core's four-part version after "PSX HW " in title.txt). Prints one line per file: OK / FAIL (what kind, never the value)."""
import ipaddress, json, re, subprocess, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
store = json.loads((Path.home() / ".config/privyhub/paired_devices.json").read_text())
secrets = {("device_id", d.get("device_id")) for d in store.get("devices", [])} | \
          {("key", d.get("key_hex")) for d in store.get("devices", [])}
adb = subprocess.run(["adb", "devices"], capture_output=True, text=True).stdout.split("\n")[1:]
for line in adb:
    if line.strip():
        ep = line.split()[0]; secrets |= {("adb_endpoint", ep), ("adb_host", ep.split(":")[0])}
for a in re.findall(r"inet (\d+\.\d+\.\d+\.\d+)", subprocess.run(["ip", "-4", "addr"], capture_output=True, text=True).stdout):
    if not a.startswith("127."):
        secrets.add(("host_address", a))
secrets = {(k, v) for k, v in secrets if v}
files = [Path(p).resolve() for p in sys.argv[1:]]
fails = 0
for f in files:
    for p in ([f] if f.is_file() else sorted(x for x in f.rglob("*") if x.is_file())):
        text = p.read_text(errors="replace")
        bad = sorted({k for k, v in secrets if v in text})
        for m in re.findall(r"(?<!PSX HW )(?<![\d.])(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?![\d.])", text):
            try:
                ip = ipaddress.ip_address(m)
            except ValueError:
                continue
            if not ip.is_loopback and str(ip) != "0.0.0.0":
                bad.append("ipv4_literal")
        print(("FAIL " + ",".join(sorted(set(bad))) if bad else "OK"), p.relative_to(REPO))
        fails += bool(bad)
print("FAILS", fails)
