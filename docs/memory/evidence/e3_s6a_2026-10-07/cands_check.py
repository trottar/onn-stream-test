#!/usr/bin/env python3
"""E3-S6A: the candidates per suite channel from the index file the adopted companion built, compared with E3-S6's
smoke dump (both its paths: today's parse and the index). Offline, in its own process: imports companion/plugins/epg.py,
reads data/epg/metadata/guides_index.json, unpacks a channel's rows exactly as _guide_index_rows does and runs the
plugin's unchanged _candidate_mappings. Also today's parse of guides.json, for the same channels. Read-only."""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
spec = importlib.util.spec_from_file_location("epg", os.path.join(REPO, "companion/plugins/epg.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
P = m.EpgPlugin.__new__(m.EpgPlugin)        # no __init__ (no threads, no warmer): only the roots it reads
P.data_root = __import__("pathlib").Path(REPO) / "data" / "epg"
P.toolchain_root, P.metadata_root = P.data_root / "toolchain", P.data_root / "metadata"
F = m.EpgPlugin._GUIDE_INDEX_FIELDS
idx = json.load(open(os.path.join(REPO, "data/epg/metadata/guides_index.json")))
meta = json.load(open(os.path.join(REPO, "data/epg/metadata/guides.json")))
smoke = {}
for line in open(os.path.join(REPO, "docs/memory/evidence/e3_s6_2026-10-07/smoke.jsonl")):
    d = json.loads(line)
    if d["label"] == "cands":
        smoke[d["channel"]] = d["reply"]
out = {"index_key": idx["key"], "index_channels": len(idx["index"]), "channels": {}}
for ch, s6 in smoke.items():
    packed = idx["index"].get(ch)
    rows = [dict(zip(F, r.split("\x1f"))) for r in packed.split("\x1e")] if packed else []
    a = P._candidate_mappings(ch, rows)
    b = P._candidate_mappings(ch, meta)
    out["channels"][ch] = {"candidates": len(a), "adopted_index_eq_parse_now": a == b,
                           "eq_s6_smoke_index": a == s6["index"], "eq_s6_smoke_parsed": a == s6["parsed"]}
out["all_identical"] = all(v["adopted_index_eq_parse_now"] and v["eq_s6_smoke_index"] and v["eq_s6_smoke_parsed"]
                           for v in out["channels"].values()) and len(out["channels"]) == 6
print(json.dumps(out, indent=1))
