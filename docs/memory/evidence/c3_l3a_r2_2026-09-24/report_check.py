#!/usr/bin/env python3
"""C3-L3A-R2: rebuild the decoder session report the companion rejected at
17:16:42Z from the two journal lines that carry its request, and test it
against every refusal in `companion/games/decoder_session_log.py`.

Read-only; writes nothing. Inputs, beside this file:

  * companion_journal_171642Z_rejected_post_redacted.txt -- the two journal
    lines (journald split the request line at its line limit), redacted;
  * rejected_report_20260924_171642_from_journal.json -- the report text,
    byte-exact, decoded the same way from the unredacted journal.

The redactor's IPv4 pattern matches one non-address in the report, the
core version string "Beetle PSX HW 0.9.44.1", so the redacted lines decode
to the report with "<ipv4>" in its place. This script proves the byte-exact
file is the journal's report: redact(file) == decode(redacted lines). The
size and every refusal are then tested on the byte-exact file.
Optional argv[1]: a directory of earlier decoder session files to size.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from urllib.parse import parse_qs, urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "h2_prep_2026-09-22"))
from h2_prep_redact import redact  # noqa: E402
MAX_REPORT_CHARS = 32_000  # companion/games/decoder_session_log.py

lines = open(os.path.join(HERE, "companion_journal_171642Z_rejected_post_redacted.txt"),
             encoding="utf-8").read().splitlines()
assert len(lines) == 2, lines

# journald split one request line at its line limit; the second line is the
# continuation, prefixed by its own timestamp / host / pid.
message = lines[0].split(": ", 1)[1] + lines[1].split(": ", 1)[1]
request = re.search(r'"POST (\S+) HTTP/1\.1" (\d+)', message)
target, status = request.group(1), request.group(2)
query = urlsplit(target).query
from_redacted = parse_qs(query)["report"][0].strip()  # as games.py: _first(...).strip()
report = open(os.path.join(HERE, "rejected_report_20260924_171642_from_journal.json"),
              encoding="utf-8", newline="").read()

print(f"journal line 1 chars            : {len(lines[0])}")
print(f"journal line 2 chars            : {len(lines[1])}")
print(f"HTTP status logged              : {status}")
print(f"request-target chars            : {len(target)}")
print(f"url-encoded report value chars  : {len(query) - len('report=')}")
print(f"decoded, redacted lines (chars) : {len(from_redacted)}")
print(f"byte-exact file (chars)         : {len(report)}")
print(f"redact(file) == redacted decode : {redact(report).rstrip(chr(10)) == from_redacted}")
print(f"MAX_REPORT_CHARS                : {MAX_REPORT_CHARS}")
print()
print("write_decoder_session_log refusals, in order:")
print(f"  empty                         : {not report}")
print(f"  len > MAX_REPORT_CHARS        : {len(report) > MAX_REPORT_CHARS}  (over by {len(report) - MAX_REPORT_CHARS})")
try:
    parsed = json.loads(report)
    print("  invalid JSON                  : False")
    print(f"  not a JSON object             : {not isinstance(parsed, dict)}")
except json.JSONDecodeError as exc:
    parsed = None
    print(f"  invalid JSON                  : True ({exc})")

if isinstance(parsed, dict):
    video = parsed.get("video") or {}
    kinds: dict[str, int] = {}
    for row in parsed.get("stream_discontinuities") or []:
        kind = row.get("kind") or row.get("type") if isinstance(row, dict) else row[0]
        kinds[kind] = kinds.get(kind, 0) + 1
    print()
    print(f"schema                          : {parsed.get('schema')}")
    print(f"duration_ms                     : {parsed.get('duration_ms')}")
    print(f"video.ssrc_changes              : {video.get('ssrc_changes')}")
    print(f"stream_discontinuities          : {kinds}")
    print(f"slow_event_retained (m / r)     : {parsed.get('slow_event_retained')} "
          f"({parsed.get('slow_event_retained_marked')} / {parsed.get('slow_event_retained_recent')})")
    print(f"re-serialized compact == posted : "
          f"{json.dumps(parsed, separators=(',', ':'), ensure_ascii=False) == report}")
    print("largest top-level members (compact chars):")
    sizes = sorted(((len(json.dumps(v, separators=(',', ':'), ensure_ascii=False)), k)
                    for k, v in parsed.items()), reverse=True)[:4]
    for size, key in sizes:
        print(f"  {key:30s}: {size}")
    audio = parsed.get("audio") or {}
    for key in ("arrival_holes", "tick_series"):
        print(f"  audio.{key:24s}: {len(json.dumps(audio.get(key), separators=(',', ':')))}")

if len(sys.argv) > 1:
    print()
    print("earlier accepted reports, compact re-serialization of `report` (the posted text; exact for the one above):")
    print("  file                                     duration_s  ssrc  chars  headroom")
    for path in sorted(glob.glob(os.path.join(sys.argv[1], "native_decoder_2026092[34]_*.json"))):
        body = json.load(open(path, encoding="utf-8"))["report"]
        size = len(json.dumps(body, separators=(",", ":"), ensure_ascii=False))
        print(f"  {os.path.basename(path):40s} {body.get('duration_ms', 0) / 1000:10.1f}"
              f"  {(body.get('video') or {}).get('ssrc_changes', 0):4}  {size:5}  {MAX_REPORT_CHARS - size:8}")
