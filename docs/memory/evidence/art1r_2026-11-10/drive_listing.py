#!/usr/bin/env python3
"""HOME-10: the drive's folders, read only. For each KEY= in the gitignored paths file: file count, bytes and a
hash of the sorted (relative name, size) listing. No name or path is printed."""
import datetime, hashlib, os, sys
from pathlib import Path
pf = Path(os.environ.get("PRIVYHUB_PS2_PATHS", "runtime/h3_p1_paths.txt"))
print("at", datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
for line in pf.read_text().splitlines():
    if "=" not in line or line.lstrip().startswith("#"):
        continue
    k, v = line.split("=", 1); k = k.strip(); p = Path(v.strip())
    if not p.is_dir():
        print(k, "not a dir"); continue
    rows = []
    for root, _, files in os.walk(p):
        for f in files:
            fp = Path(root) / f
            try: rows.append((str(fp.relative_to(p)), fp.stat().st_size))
            except OSError: pass
    rows.sort(); h = hashlib.sha256("\n".join(f"{a}\t{b}" for a, b in rows).encode()).hexdigest()[:16]
    print(k, "files", len(rows), "bytes", sum(b for _, b in rows), "listing_sha256", h)
