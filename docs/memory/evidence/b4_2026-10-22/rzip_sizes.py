import glob, os, struct, sys, zlib, statistics, json
root = sys.argv[1]
def header(p):
    b = open(p, "rb").read(20)
    assert b[:8] == b"#RZIPv\x01#", p
    chunk, total = struct.unpack("<IQ", b[8:20])
    return chunk, total
def full(p):
    d = open(p, "rb").read(); off = 20; out = 0
    while off < len(d):
        (n,) = struct.unpack("<I", d[off:off+4]); off += 4
        out += len(zlib.decompress(d[off:off+n])); off += n
    return out
res = {}
for core in sorted(os.listdir(root)):
    sizes = []
    for p in sorted(glob.glob(os.path.join(root, core, "*"))):
        if p.endswith(".png"): continue
        c, t = header(p); sizes.append((t, os.path.getsize(p)))
    res[core] = {"files": len(sizes), "raw_min": min(s[0] for s in sizes), "raw_max": max(s[0] for s in sizes),
                 "disk_max": max(s[1] for s in sizes)}
p = sorted(q for q in glob.glob(os.path.join(root, "Snes9x", "*")) if not q.endswith(".png"))[0]
res["_check_full_decompress_snes9x"] = {"header": header(p)[1], "decompressed": full(p)}
p = sorted(q for q in glob.glob(os.path.join(root, "Beetle PSX HW", "*")) if not q.endswith(".png"))[0]
res["_check_full_decompress_psx"] = {"header": header(p)[1], "decompressed": full(p)}
print(json.dumps(res, indent=1))
