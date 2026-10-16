#!/usr/bin/env python3
"""CL-B3: the client's identity state read through `adb shell run-as` (debug APK), read-only.
Writes only: identity_v2 (bool), hub_host set (bool), device_secret present (bool), and the identity prefs' KEY NAMES
(values never read out of the device into the output: no device id, key, token or address)."""
import json, re, subprocess, sys, datetime
PKG = "com.safeiot.privyhub"
def sh(*a):
    return subprocess.run(["adb", "shell", "run-as", PKG, *a], capture_output=True, text=True, timeout=20).stdout
def prefs(name):
    return sh("cat", f"shared_prefs/{name}.xml")
s = prefs("privyhub_settings")
m = re.search(r'<boolean name="identity_v2" value="(true|false)"', s)
hub = re.search(r'<string name="hub_host">([^<]*)</string>', s)
idp = prefs("privyhub_identity")
keys = sorted(set(re.findall(r'name="([^"]+)"', idp)))
sec = sh("ls", "files/identity/").split()
out = {"at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
       "identity_v2": (m.group(1) == "true") if m else None, "identity_v2_key_present": bool(m),
       "hub_host_set": bool(hub and hub.group(1).strip()),
       "device_secret_present": "device_secret" in sec,
       "identity_prefs_keys": keys}
print(json.dumps(out))
