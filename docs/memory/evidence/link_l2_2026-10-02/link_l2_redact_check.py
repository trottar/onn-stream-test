#!/usr/bin/env python3
"""LINK-L2 -- h2_prep_redact.py --check over every text file this task wrote; for a file that fails, list
what matched, and call it FLAG (benign) only if every match is the IPv4 pattern on 127.0.0.1 (loopback),
0.0.0.0 (bind) or 0.9.44.1 (the Beetle PSX HW core's version), as LINK-L1's check did. Anything else is FAIL.
    link_l2_redact_check.py <file>...   -> stdout lines; exit 1 on any FAIL"""
import importlib.util, subprocess, sys
RED = "docs/memory/evidence/h2_prep_2026-09-22/h2_prep_redact.py"
spec = importlib.util.spec_from_file_location("red", RED); red = importlib.util.module_from_spec(spec); spec.loader.exec_module(red)
BENIGN = {"127.0.0.1", "0.0.0.0", "0.9.44.1"}
fail = 0
for f in sys.argv[1:]:
    rc = subprocess.run([sys.executable, RED, "--check"], stdin=open(f, "rb"), capture_output=True).returncode
    if rc == 0:
        print(f"PASS {f}")
        continue
    bad, ipv4 = [], set()
    for n, line in enumerate(open(f, errors="replace").read().splitlines(), 1):
        if red.EDID_LINE.match(line):
            bad.append(f"{n}: EDID line")
        for i, (pat, _) in enumerate(red.PATTERNS):
            for m in pat.finditer(line):
                if i == 3 and m.group(0) in BENIGN:
                    ipv4.add(m.group(0))
                else:
                    bad.append(f"{n}: pattern {i} {m.group(0)[:3]}...")
    if bad:
        fail += 1
        print(f"FAIL {f} ({len(bad)} non-benign: {bad[:3]})")
    else:
        print(f"FLAG {f} (non-benign matches: 0; benign IPv4 only: {sorted(ipv4)})")
sys.exit(1 if fail else 0)
