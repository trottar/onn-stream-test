#!/usr/bin/env python3
"""CL-B4: the client's identity state and pairing, read-only (CL-B3's reader plus the pairing comparison).
`adb shell run-as` (debug APK) and the hub's paired store, read in process. Writes only booleans, counts and the
prefs' KEY NAMES: no device id, key, token or address leaves this process. Also the installed APK's sha256."""
import datetime, hashlib, json, re, subprocess, sys
from pathlib import Path
PKG = "com.safeiot.privyhub"
def sh(*a):
    return subprocess.run(["adb", "shell", "run-as", PKG, *a], capture_output=True, text=True, timeout=20).stdout
def device_apk_sha256():
    path = subprocess.run(["adb", "shell", "pm", "path", PKG], capture_output=True, text=True, timeout=20).stdout
    path = path.strip().splitlines()[0].split(":", 1)[1] if path.strip() else ""
    out = subprocess.run(["adb", "shell", "sha256sum", path], capture_output=True, text=True, timeout=60).stdout
    return out.split()[0] if out else None
s = sh("cat", "shared_prefs/privyhub_settings.xml")
m = re.search(r'<boolean name="identity_v2" value="(true|false)"', s)
hub = re.search(r'<string name="hub_host">([^<]*)</string>', s)
idp = sh("cat", "shared_prefs/privyhub_identity.xml")
keys = sorted(set(re.findall(r'name="([^"]+)"', idp)))
dev = re.search(r'<string name="device_id">([^<]*)</string>', idp)
sec = sh("ls", "files/identity/").split()
store = json.loads((Path.home() / ".config/privyhub/paired_devices.json").read_text())
ids = {d.get("device_id") for d in store.get("devices", [])}
perms = sorted(next((d.get("permissions", []) for d in store.get("devices", []) if dev and d.get("device_id") == dev.group(1)), []))
print(json.dumps({
    "at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "device_apk_sha256": device_apk_sha256(),
    "identity_v2": (m.group(1) == "true") if m else None,
    "hub_host_set": bool(hub and hub.group(1).strip()),
    "device_secret_present": "device_secret" in sec,
    "identity_prefs_keys": keys,
    "host_paired_devices": len(ids),
    "client_device_id_present": bool(dev),
    "client_device_id_in_host_store": bool(dev and dev.group(1) in ids),
    "host_stored_permissions": perms,
}))
