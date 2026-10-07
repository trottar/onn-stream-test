#!/usr/bin/env python3
"""E3-S6: the slim index's build time and in-memory size, outside the companion (the same fields and packing as
EpgPlugin._guide_index_rows), and the load time of the saved guides_index.json. Read-only."""
import json, time, tracemalloc, os
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../data/epg/metadata")
F = ("channel", "feed", "site", "site_id", "lang", "site_name")
def canon(c, f):
    c, f = (c or "").strip(), (f or "").strip()
    return "" if not c else (f"{c}@{f}" if f else c)
t0 = time.perf_counter(); c0 = time.process_time()
payload = json.loads(open(os.path.join(root, "guides.json"), "rb").read().decode("utf-8"))
t_parse = time.perf_counter() - t0
tracemalloc.start()
g = {}
for item in payload:
    if isinstance(item, dict):
        row = [str(item.get(f, "") or "") for f in F]
        k = canon(row[0], row[1])
        if k:
            g.setdefault(k, []).append("\x1f".join(row))
index = {k: "\x1e".join(v) for k, v in g.items()}
del g
size = tracemalloc.get_traced_memory()[0]
tracemalloc.stop()
t_build = time.perf_counter() - t0
cpu = time.process_time() - c0
del payload
t1 = time.perf_counter(); saved = json.loads(open(os.path.join(root, "guides_index.json")).read()); t_load = time.perf_counter() - t1
print(json.dumps({"items": None, "channels": len(index), "parse_s": round(t_parse, 3), "build_total_s": round(t_build, 3),
                  "build_cpu_s": round(cpu, 3), "index_in_memory_mb": round(size / 1048576, 1),
                  "saved_file_mb": round(os.path.getsize(os.path.join(root, "guides_index.json")) / 1048576, 2),
                  "saved_channels": len(saved.get("index", {})), "load_saved_s": round(t_load, 3)}))
