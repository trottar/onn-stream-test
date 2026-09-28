#!/usr/bin/env python3
"""C3-L3A-R3: size of session 3's stored decoder report against the raised
cap (48,000, C3-L3A-R2B) and the transport ceiling (~41.4K decoded), and
proof the stored file is the posted text. Read-only.

Inputs: native_decoder_20260924_193658_993.json (byte copy, here) and the
journal lines of the POST (argv[1], unredacted, read in place and never
stored; only numbers are printed).
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent
MAX_REPORT_CHARS = 48_000       # companion/games/decoder_session_log.py (R2B)
OLD_CAP = 32_000                # before R2B
REQUEST_LINE_MAX = 65_536       # http.server
FIXED = 58  # R2B cap_check.txt: "POST " + path + "?report=" + " HTTP/1.1\r\n"

stored = json.loads((HERE / "native_decoder_20260924_193658_993.json").read_text())
report = stored["report"]
compact = json.dumps(report, separators=(",", ":"), ensure_ascii=False)
print(f"stored file schema              : {stored['schema']}")
print(f"received_at_utc                 : {stored['received_at_utc']}")
print(f"report duration_ms              : {report['duration_ms']}")
print(f"video.ssrc_changes              : {report['video']['ssrc_changes']}")
print(f"compact report chars            : {len(compact)}")
print(f"headroom under 48,000           : {MAX_REPORT_CHARS - len(compact)}")
print(f"over the old 32,000 by          : {len(compact) - OLD_CAP}")

lines = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
post = [i for i, l in enumerate(lines) if "decoder-session-log?report=" in l]
assert len(post) == 1, post
i = post[0]
message = lines[i].split(": ", 1)[1]
# journald splits a long line at its limit: append continuation lines until
# the access-log tail appears.
j = i
while '" 200 -' not in message and '" 400 -' not in message:
    j += 1
    message += lines[j].split(": ", 1)[1]
req = re.search(r'"POST (\S+) HTTP/1\.1" (\d+)', message)
target, status = req.group(1), req.group(2)
encoded = len(urlsplit(target).query) - len("report=")
posted = parse_qs(urlsplit(target).query)["report"][0].strip()
ratio = encoded / len(posted)
print(f"journal lines for the POST      : {j - i + 1}")
print(f"HTTP status logged              : {status}")
print(f"request-target chars            : {len(target)}")
print(f"url-encoded report value chars  : {encoded}")
print(f"decoded posted chars            : {len(posted)}")
print(f"posted == stored compact        : {posted == compact}")
print(f"encoded / decoded ratio         : {ratio:.3f}")
ceiling = (REQUEST_LINE_MAX - FIXED) / ratio
print(f"transport ceiling at this ratio : {ceiling:,.0f} decoded chars")
print(f"headroom under that ceiling     : {ceiling - len(posted):,.0f}")
print(f"request line bytes (value + 58)  : {encoded + FIXED} of {REQUEST_LINE_MAX}")
