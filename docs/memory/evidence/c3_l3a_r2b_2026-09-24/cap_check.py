#!/usr/bin/env python3
"""C3-L3A-R2B: call the companion's write_decoder_session_log directly.

Its output directory is <project_root>/logs/games/decoder_sessions, and
project_root is a parameter, so every write lands in a scratch project root
(argv[1]), never in the repository's logs/. Cases:
  (a) the session-2 report rebuilt from the journal (32,057 chars) - accepted
  (b) a synthetic 47,000-char JSON object                         - accepted
  (c) a synthetic 49,000-char JSON object                         - refused, length
  (d) exactly MAX_REPORT_CHARS / MAX_REPORT_CHARS + 1             - accepted / refused
Also prints the transport ceiling: the longest decoded report whose
URL-encoded request line (as the client builds it) fits http.server's
65,536-byte limit, at this report's own encoding ratio.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import quote_plus

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "companion"))

from games import decoder_session_log as dsl  # noqa: E402

scratch = Path(sys.argv[1]).resolve()
assert REPO not in scratch.parents and scratch != REPO, "scratch must be outside the repo"

rebuilt = (REPO / "docs/memory/evidence/c3_l3a_r2_2026-09-24/"
           "rejected_report_20260924_171642_from_journal.json").read_text(encoding="utf-8")


def synthetic(chars: int) -> str:
    head = '{"schema":"synthetic_c3_l3a_r2b","pad":"'
    tail = '"}'
    text = head + "x" * (chars - len(head) - len(tail)) + tail
    assert len(text) == chars and isinstance(json.loads(text), dict)
    return text


print(f"MAX_REPORT_CHARS = {dsl.MAX_REPORT_CHARS}")
cases = [
    ("a rebuilt session-2 report", rebuilt),
    ("b synthetic", synthetic(47_000)),
    ("c synthetic", synthetic(49_000)),
    ("d at the cap", synthetic(dsl.MAX_REPORT_CHARS)),
    ("d cap + 1", synthetic(dsl.MAX_REPORT_CHARS + 1)),
]
for label, text in cases:
    # Filenames are millisecond-stamped; two writes in one millisecond share
    # a name and the second replaces the first. Space the cases apart.
    time.sleep(0.01)
    try:
        result = dsl.write_decoder_session_log(scratch, text)
        saved = scratch / result["log_path"]
        stored = json.loads(saved.read_text(encoding="utf-8"))["report"]
        same = json.dumps(stored, separators=(",", ":"), ensure_ascii=False) == text
        print(f"{label:28s} {len(text):6d} chars  ACCEPTED  saved under scratch, report round-trips: {same}")
    except ValueError as exc:
        print(f"{label:28s} {len(text):6d} chars  REFUSED   {exc}")

written = sorted(p.name for p in (scratch / "logs/games/decoder_sessions").glob("*.json"))
print(f"files written (scratch only): {len(written)}")

# The transport ceiling. The client: URLEncoder.encode(report, "UTF-8"),
# form encoding like quote_plus (they differ only on '*' and '~': the
# journal's own request carried 50,717 encoded chars for this report).
encoded = quote_plus(rebuilt)
ratio = len(encoded) / len(rebuilt)
fixed = len("POST /plugins/games/decoder-session-log?report= HTTP/1.1\r\n")
print(f"rebuilt report: {len(rebuilt)} chars -> {len(encoded)} encoded (ratio {ratio:.4f})")
print(f"request line = {fixed} fixed bytes + encoded report; http.server limit 65,536")
print(f"transport ceiling at this ratio: ~{int((65_536 - fixed) / ratio)} decoded chars")
