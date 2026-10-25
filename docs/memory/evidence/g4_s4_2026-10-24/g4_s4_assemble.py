#!/usr/bin/env python3
"""G4-S4 Part 2: assemble the copies for the whole off-site play (read-only on the sources).

The span: 2026-10-24T19:15:00Z (before the first VOD) to 2026-10-25T17:40:00Z (before the onn's first LAN setup at
17:42:40Z). For each rotating log: the live file and its stream_log_archive/<name>.1 are read, the rows inside the span
kept, de-duplicated (the exact line), and sorted by their time key. The driver's raw copies (~/privyhub_g4_s4/logs,
19:27:32-21:21:12Z) are compared row-for-row inside their own span as a check. New decoder_sessions/ and
audio_timing/ files are copied by their received time. Nothing is moved or deleted at the source.

    g4_s4_assemble.py  ->  copies/logs/games/..., copies/assemble_check.json
"""
import json
import os
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SRC = REPO / "logs/games"
ARCH = SRC / "stream_log_archive"
RAW = Path.home() / "privyhub_g4_s4/logs"
OUT = HERE / "copies/logs/games"
LO, HI = "2026-10-24T19:15:00", "2026-10-25T17:40:00"
RAW_LO, RAW_HI = "2026-10-24T19:27:32", "2026-10-24T21:21:12"
LOGS = {"native_stream_heartbeat.log": "received_at_utc", "native_stream_ctrl_gaps.log": "start_utc",
        "native_frame_sizes.jsonl": "at_utc", "adaptive_bitrate_shadow.jsonl": "at_utc",
        "native_stream_recovery.log": "at_utc", "host_resource_samples.jsonl": "at_utc"}
TKEY = re.compile(r'"(?:at_utc|received_at_utc|start_utc|t_utc)"\s*:\s*"([0-9T:.\-]+)Z?"')


def rows(p, key):
    out = []
    if not p.exists():
        return out
    for line in open(p, errors="replace"):
        line = line.rstrip("\n")
        try:
            t = str(json.loads(line).get(key) or "")
        except ValueError:
            m = TKEY.search(line)
            t = m.group(1) if m else ""
        out.append((t, line))
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    check = {"span": [LO + "Z", HI + "Z"], "logs": {}}
    for name, key in LOGS.items():
        seen, keep = set(), []
        for src in (ARCH / f"{name}.1", SRC / name):
            for t, line in rows(src, key):
                if LO <= t < HI and line not in seen:
                    seen.add(line)
                    keep.append((t, line))
        keep.sort(key=lambda x: x[0])
        with open(OUT / name, "w") as fh:
            fh.writelines(l + "\n" for _, l in keep)
        raw = {l for t, l in rows(RAW / name, key) if RAW_LO <= t < RAW_HI}
        mine = {l for t, l in keep if RAW_LO <= t < RAW_HI}
        check["logs"][name] = {"rows": len(keep), "first": keep[0][0] if keep else None, "last": keep[-1][0] if keep else None,
                               "raw_copy_rows_in_its_span": len(raw), "assembled_rows_in_that_span": len(mine),
                               "raw_rows_missing_from_assembled": len(raw - mine), "assembled_rows_not_in_raw": len(mine - raw)}
    for sub, rx in (("decoder_sessions", re.compile(r"native_decoder_(\d{8})_(\d{6})")),
                    ("audio_timing", None)):
        n = 0
        (OUT / sub).mkdir(exist_ok=True)
        for p in sorted((SRC / sub).glob("*.json")):
            try:
                t = str(json.load(open(p)).get("received_at_utc") or "")
            except (OSError, ValueError):
                t = ""
            if not t and rx is None:
                m = re.search(r"(\d{8})_(\d{6})", p.name)          # audio_timing names are local time; use mtime instead
                from datetime import datetime, timezone
                t = datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            if LO <= t < HI:
                shutil.copy2(p, OUT / sub / p.name)
                n += 1
        check[sub] = n
    (HERE / "copies/assemble_check.json").write_text(json.dumps(check, indent=1) + "\n")
    print(json.dumps(check, indent=1))


if __name__ == "__main__":
    main()
