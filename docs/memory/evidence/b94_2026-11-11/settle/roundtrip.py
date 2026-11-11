"""B94 settle 2 (synthetic fixtures): frames passed at a paused load, stability over loads, the state file's layout."""
import json, sys, time, tempfile, zlib, hashlib, shutil
from pathlib import Path
sys.path.insert(0, "/home/privyhub/Projects/onn-stream-test/tools"); sys.path.insert(0, "/home/privyhub/Projects/onn-stream-test/tests/h7_rule_search"); sys.path.insert(0, ".")
import h7_minigame_proof as P, fixtures as F, fixture_n64
SPEC = {"snes": ("Made Up.sfc", F.snes(), "RAM", 0x20000, 0x0000, 0x0800),
        "ps1": ("Made Up.exe", F.psx_exe(), "MEMORY", 0x200000, 0x080000, 0x0C0000),
        "n64": ("Made Up.z64", fixture_n64.build()[0], "MEMORY", 0x400000, None, 0x300000)}
CH = 16384
def dump(s, kind, size):
    out = bytearray()
    for a in range(0, size, CH):
        r = s.ask(f"READ_CORE_{kind} {a:x} {min(CH, size - a)}", 2.0).split()[2:]
        out += bytes(int(b, 16) for b in r)
    return bytes(out)
def word(s, kind, addr):
    r = s.ask(f"READ_CORE_{kind} {addr:x} 4", 1.0).split()[2:]
    return bytes(int(b, 16) for b in r).hex()
def unpack(raw):
    info = {"magic": raw[:8].hex(), "size": len(raw)}
    if raw[:8] == b"#RZIPv\x01#":
        chunk = int.from_bytes(raw[8:12], "little"); total = int.from_bytes(raw[12:20], "little"); p = 20; out = b""
        while p < len(raw):
            n = int.from_bytes(raw[p:p + 4], "little"); out += zlib.decompress(raw[p + 4:p + 4 + n]); p += 4 + n
        info["container"] = "RZIP"; return out, info
    info["container"] = "plain"; return raw, info
res = {}
for sysname, (name, data, kind, size, counter, plant) in SPEC.items():
    tmp = Path(tempfile.mkdtemp(prefix="rt_", dir=".")); rom = tmp / name; rom.write_bytes(data)
    r = {}
    s = P.Session(rom, sysname, tmp / "a")
    try:
        s.wait_playing(); time.sleep(1.0)
        if counter is not None:
            c1 = word(s, kind, counter); time.sleep(0.3); r["code_runs"] = c1 != word(s, kind, counter)
        s.pause()
        pat = hashlib.sha256(sysname.encode()).digest() * 2           # 64 bytes, distinct
        s.send(f"WRITE_CORE_{kind} {plant:x} " + " ".join(f"{b:02x}" for b in pat)); time.sleep(0.3)
        r["write_read_back"] = word(s, kind, plant) == pat[:4].hex()
        before = dump(s, kind, size)
        s.save_state(tmp / "x.state")
        after_save = dump(s, kind, size)
        r["paused_save_changed_bytes"] = sum(a != b for a, b in zip(before, after_save))
    finally:
        s.close()
    raw = (tmp / "x.state").read_bytes(); body, info = unpack(raw); r["state_file"] = info
    i = body.find(pat)
    swapped = b"".join(pat[k:k + 4][::-1] for k in range(0, 64, 4))
    j = body.find(swapped)
    r["pattern_in_file"] = {"as_is": i, "word_swapped": j}
    off = (i if i >= 0 else j) - plant if (i >= 0 or j >= 0) else None
    if off is not None and off >= 0:
        region = body[off:off + size]
        if i < 0:   # N64: 32-bit words byte-swapped in the file relative to the read
            region = b"".join(region[k:k + 4][::-1] for k in range(0, len(region), 4))
        r["file_ram_equals_paused_read"] = {"bytes_equal": sum(a == b for a, b in zip(region, before)), "of": size,
                                            "region_complete": len(region) == size}
    # three paused loads
    loads = []; frames = []
    for n in range(3):
        s = P.Session(rom, sysname, tmp / f"l{n}")
        try:
            s.wait_playing(); s.pause()
            s.load_state(tmp / "x.state")
            time.sleep(0.5)
            m = dump(s, kind, size); loads.append(m)
            if counter is not None:
                frames.append(int.from_bytes(m[counter:counter + 2] if sysname == "snes" else m[counter:counter + 4], "little")
                              - int.from_bytes(before[counter:counter + 2] if sysname == "snes" else before[counter:counter + 4], "little"))
        finally:
            s.close()
    r["paused_load"] = {"counter_advance_after_load": frames,
                        "bytes_differing_from_saved": [sum(a != b for a, b in zip(m, before)) for m in loads],
                        "bytes_differing_between_loads": sum(1 for k in range(size) if len({m[k] for m in loads}) > 1)}
    # three running loads (load, then pause)
    run = []
    for n in range(3):
        s = P.Session(rom, sysname, tmp / f"r{n}")
        try:
            s.wait_playing(); s.load_state(tmp / "x.state"); s.pause(); run.append(dump(s, kind, size))
        finally:
            s.close()
    r["running_load_then_pause"] = {"bytes_differing_between_loads": sum(1 for k in range(size) if len({m[k] for m in run}) > 1)}
    shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps({sysname: r}), flush=True)
