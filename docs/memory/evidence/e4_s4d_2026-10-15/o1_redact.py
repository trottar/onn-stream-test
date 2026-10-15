#!/usr/bin/env python3
"""O1: strip identifiers from anything the Opal prints, before it is shown
or stored. MACs/BSSIDs become stable per-run labels; SSIDs, pre-shared
keys, IPv4/IPv6 and accounting session ids are replaced outright.

Ordering matters: secrets are removed before MAC labelling, so that a key
that happens to look like hex is never handed to the label table.
"""
import re, sys

_MAC = re.compile(r'\b([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b')
_IP4 = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
# IPv6 only: either a '::' compression or at least four colons. A bare
# 'HH:MM:SS' clock has two and must survive -- the first version of this
# file turned every timestamp the Opal printed into '<redacted-ip>'.
_IP6 = re.compile(
    r'\b(?:[0-9a-fA-F]{0,4}:){4,7}[0-9a-fA-F]{0,4}\b'
    r'|\b[0-9a-fA-F]{0,4}(?::[0-9a-fA-F]{0,4})*::'
    r'(?:[0-9a-fA-F]{0,4}(?::[0-9a-fA-F]{0,4})*)?')

# Secrets and names, in every shape these tools print them. `uci show`
# emits `wireless.default_radio1.ssid='NAME'` and `.key='SECRET'`, which
# the first version of this file did not match at all -- it matched only
# `option ssid` and a bare `ssid <word>` -- so one `uci show wireless`
# printed both SSIDs and both WPA passphrases in clear.
_SECRETS = [
    # uci show: any assignment whose leaf name is a name or a secret
    (re.compile(r"((?:^|[\w.])(?:ssid)=)'[^']*'", re.I | re.M),
     r"\1'<redacted-ssid>'"),
    (re.compile(r"((?:^|[\w.])(?:key|password|passphrase|psk|auth_secret"
                r"|wpa_psk|radius_secret)=)'[^']*'", re.I | re.M),
     r"\1'<redacted-secret>'"),
    # uci export / config file: option ssid 'NAME'
    (re.compile(r"(option\s+ssid\s+)'[^']*'", re.I), r"\1'<redacted-ssid>'"),
    (re.compile(r"(option\s+(?:key|password|passphrase|psk)\s+)'[^']*'",
                re.I), r"\1'<redacted-secret>'"),
    # iwinfo: ESSID: "NAME"
    (re.compile(r'(ESSID:\s*)"[^"]*"', re.I), r'\1"<redacted-ssid>"'),
    # iw dev: ssid NAME   (bare, to end of line)
    (re.compile(r'(\bssid\s+)(?!<redacted)\S.*$', re.I | re.M),
     r'\1<redacted-ssid>'),
    # hostapd accounting session ids and other long bare hex blobs
    (re.compile(r'(accounting session\s+)[0-9A-Fa-f]{8,}', re.I),
     r'\1<redacted-id>'),
]

_seen = {}


def _label(mac):
    m = mac.lower()
    if m not in _seen:
        i = len(_seen)
        _seen[m] = "sta-" + (chr(ord('A') + i) if i < 26 else str(i))
    return _seen[m]


def redact(t):
    for pat, rep in _SECRETS:
        t = pat.sub(rep, t)
    t = _MAC.sub(lambda m: _label(m.group(0)), t)
    t = _IP4.sub("<redacted-ip>", t)
    t = _IP6.sub("<redacted-ip>", t)
    return t


if __name__ == "__main__":
    sys.stdout.write(redact(sys.stdin.read()))
