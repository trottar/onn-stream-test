"""B94 settle: per core, the largest READ_CORE_* chunk one command answers, and the time to read the whole main memory.
Synthetic fixtures only (B61's N64 loop, a SNES LoROM loop, a PS-X EXE loop); RetroArch headless via B93's Session."""
import json, sys, time, tempfile
from pathlib import Path
sys.path.insert(0, "/home/privyhub/Projects/onn-stream-test/tools"); sys.path.insert(0, ".")
import h7_minigame_proof as P, fixture_n64, fixture_more
SPEC = {"snes": ("Made Up.sfc", fixture_more.snes(), "READ_CORE_RAM", 0x0, 0x20000),
        "ps1": ("Made Up.exe", fixture_more.psx_exe(), "READ_CORE_MEMORY", 0x0, 0x200000),
        "n64": ("Made Up.z64", fixture_n64.build()[0], "READ_CORE_MEMORY", 0x0, 0x400000)}
out = {}
for sysname, (name, data, cmd, base, size) in SPEC.items():
    tmp = Path(tempfile.mkdtemp(prefix="chunk_", dir=".")); rom = tmp / name; rom.write_bytes(data)
    s = P.Session(rom, sysname, tmp / "w")
    try:
        s.wait_playing(); time.sleep(1.0); s.pause()
        sizes = {}
        for n in (256, 1024, 4096, 8192, 16384, 21000, 21840, 22000, 32768, 65536):
            a = s.ask(f"{cmd} {base:x} {n}", 2.0)
            got = len(a.split()) - 2 if a else None
            sizes[n] = got
        best = max(n for n, g in sizes.items() if g == n)
        t0 = time.monotonic(); total = 0; fails = 0
        for addr in range(base, base + size, best):
            n = min(best, base + size - addr)
            a = s.ask(f"{cmd} {addr:x} {n}", 2.0)
            if a and len(a.split()) - 2 == n: total += n
            else: fails += 1
        out[sysname] = {"command": cmd, "answers_by_request": sizes, "largest_full_chunk": best,
                        "bytes_read": total, "of": size, "failed_chunks": fails, "seconds": round(time.monotonic() - t0, 2)}
    finally:
        s.close()
    print(json.dumps({sysname: out[sysname]}), flush=True)
