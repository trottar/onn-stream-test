#!/usr/bin/env python3
"""UX-R1 §0: copy everything covering 2026-10-19T17:48Z -> now into session/.

Copies only (sources are read, never moved or truncated). Every copy passes
through the project redactor (addresses, MACs, UUIDs, adb serials) and a
mask for client ids / token refs, so no identifier lands in docs/.
Whole files for the ladder / frame-size / heartbeat logs and their rotated
archives; span rows for the audit and the HTTP log; the encoder log from the
first block that starts in the span.
"""
from __future__ import annotations

import glob, importlib.util, json, os, re, subprocess, sys
from datetime import datetime, timezone

ROOT = "/home/privyhub/Projects/onn-stream-test"
OUT = os.path.join(ROOT, "docs/memory/evidence/ux_r1_2026-10-20/session")
SPAN = datetime(2026, 10, 19, 17, 48, tzinfo=timezone.utc)
SPAN_EPOCH = SPAN.timestamp()

spec = importlib.util.spec_from_file_location(
    "r", os.path.join(ROOT, "docs/memory/evidence/h2_prep_2026-09-22/h2_prep_redact.py"))
R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
EXTRA = [
    (re.compile(r'"client_id":\s*"[^"]*"'), '"client_id": "<client>"'),
    (re.compile(r'"token_ref":\s*"[^"]*"'), '"token_ref": "<token>"'),
    (re.compile(r"\bdev-[0-9a-f]{8,}\b"), "<client>"),
]

def clean(text: str) -> str:
    text = R.redact(text)
    for p, s in EXTRA:
        text = p.sub(s, text)
    return text

def put(name: str, text: str) -> None:
    path = os.path.join(OUT, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(clean(text))
    print(f"copied {name} ({len(text)} bytes in)")

def whole(src: str, name: str | None = None) -> None:
    with open(src, errors="replace") as f:
        put(name or os.path.relpath(src, ROOT), f.read())

def after_span(src: str) -> bool:
    return os.path.getmtime(src) >= SPAN_EPOCH - 600

G = os.path.join(ROOT, "logs/games")
# ladder logs, frame sizes, heartbeat, host sampler: current + every rotated archive
for base in ("adaptive_bitrate_shadow.jsonl", "native_frame_sizes.jsonl"):
    whole(os.path.join(G, base))
    for a in sorted(glob.glob(os.path.join(G, "stream_log_archive", base + ".*"))):
        whole(a)
for base in ("native_stream_heartbeat.log", "native_stream_recovery.log",
             "native_stream_ctrl_gaps.log", "host_resource_samples.jsonl",
             "native_pulseaudio.log"):
    whole(os.path.join(G, base))
for a in sorted(glob.glob(os.path.join(G, "stream_log_archive", "*"))):
    if after_span(a):
        whole(a)
# client health reports, audio timing, game session logs, other logs/ files touched in the span
ALREADY = {"native_stream_heartbeat.log", "native_stream_recovery.log",
           "native_stream_ctrl_gaps.log", "native_pulseaudio.log", "native_video_alpha.log"}
for pat in ("decoder_sessions/*.json", "audio_timing/*.json", "*.log", "*.txt", "*.json"):
    for src in sorted(glob.glob(os.path.join(G, pat))):
        if after_span(src) and os.path.basename(src) not in ALREADY:
            whole(src)
# encoder log: from the first block whose capture starts in the span
enc = open(os.path.join(G, "native_video_alpha.log"), errors="replace").read()
blocks = enc.split("=" * 72 + "\nStarting PrivyHub")
keep, started = [], False
for b in blocks[1:]:
    m = re.search(r"start: (\d+\.\d+)", b)
    if m and float(m.group(1)) >= SPAN_EPOCH:
        started = True
    if started:
        keep.append("=" * 72 + "\nStarting PrivyHub" + b)
put("logs/games/native_video_alpha.span.log",
    f"# UX-R1 extract: blocks of native_video_alpha.log whose x11grab start >= {SPAN.isoformat()} ({len(keep)} of {len(blocks)-1} blocks)\n" + "".join(keep))
# span rows: audit + HTTP log
def span_rows(src, name, key):
    rows = []
    for line in open(src, errors="replace"):
        try:
            t = json.loads(line).get(key, "")
        except Exception:
            continue
        if t >= SPAN.strftime("%Y-%m-%dT%H:%M"):
            rows.append(line)
    put(name, "".join(rows))
span_rows(os.path.join(ROOT, "logs/session_audit.jsonl"), "logs/session_audit.span.jsonl", "t")
srv = [l for l in open(os.path.join(ROOT, "logs/server.log"), errors="replace")
       if re.search(r"\[(19/Oct/2026 (1[4-9]|2[0-3])|20/Oct/2026)", l)]
put("logs/server.span.log", "".join(srv))
# the companion journal for the span (EPG grabber / scheduler log lines live here too)
j = subprocess.run(["journalctl", "--user", "-u", "privyhub-companion", "--no-pager",
                    "-o", "short-iso-precise", "--since", "2026-10-19 17:48:00 UTC"],
                   capture_output=True, text=True).stdout
put("journal_privyhub_companion.span.txt", j)
