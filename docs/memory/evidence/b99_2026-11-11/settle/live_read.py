#!/usr/bin/env python3
"""B99 settle (synthetic fixtures, B61's form: RetroArch headless, the hub's AppImage and cores, temp folders, the
companion's display; no game). Every command is sent the way the companion sends it: a fresh UDP socket per command,
bound to 127.0.0.1:0, one answer read from the command port (emulator_manager._retroarch_network_request's form), so a
late answer can only reach a closed socket. Prints one JSON line per part.

  S1 SNES running: the fixture's frame counter ($0000, +1 a frame) across 60 s windows, alternately with no reads and
     with a read every second (GET_STATUS + READ_CORE_RAM of 2 bytes, as the route would send); answer times.
  S2 PS1: a per-frame counter searched in the core's own memory (paused, FRAMEADVANCE x N, words that moved by N), then
     the same windows if one is found.
  S3 a read while paused: answer times, the counter unchanged.
  S4 interleaved for 30 s while running: GET_STATUS every 0.1 s, a read every 0.25 s, a SAVE_STATE every 3 s, the
     hold's pause (PAUSE_TOGGLE, GET_STATUS, 0.5 s, PAUSE_TOGGLE) every 4 s — every answer matched to its command.
  S5 N64 (B61's ROM): the read's forms and times (its RDRAM holds only zeros: the ROM's code never lands in RDRAM —
     found with a 4 MiB dump and a store-program variant, fixture_n64_store.py; so no byte order is anchored here).
usage: live_read.py <repo> <seconds per window>"""
import json, socket, statistics, sys, threading, time, shutil, tempfile
from pathlib import Path
REPO = Path(sys.argv[1]); WIN = float(sys.argv[2])
sys.path.insert(0, str(REPO / "tools")); sys.path.insert(0, str(REPO / "tests/h7_rule_search"))
sys.path.insert(0, str(REPO / "docs/memory/evidence/b90_2026-11-11/measure"))
import h7_minigame_proof as P, fixtures as F, fixture_n64

def cmd(port, text, wait=0.25, answer=True):
    """One command, the companion's way: its own socket; returns (answer or None, ms)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(("127.0.0.1", 0)); s.settimeout(wait)
        t0 = time.perf_counter(); s.sendto(text.encode(), ("127.0.0.1", port))
        if not answer:
            return None, 0.0
        try:
            while True:
                data, src = s.recvfrom(65536)
                if src[1] == port:
                    return data.decode(errors="replace").strip(), (time.perf_counter() - t0) * 1000
        except socket.timeout:
            return None, (time.perf_counter() - t0) * 1000

def counter(port, kind, addr, n):
    a, _ = cmd(port, f"READ_CORE_{kind} {addr:x} {n}", 0.5)
    parts = (a or "").split()
    if len(parts) != n + 2 or parts[0] != f"READ_CORE_{kind}" or int(parts[1], 16) != addr:
        raise RuntimeError(f"bad counter answer: {a!r}")
    return int.from_bytes(bytes(int(b, 16) for b in parts[2:]), "little")

def windows(port, kind, addr, n, wrap):
    rows = []
    for i, reads in enumerate((False, True, False, True)):
        c0 = counter(port, kind, addr, n); t0 = time.monotonic(); times = []; bad = 0
        while time.monotonic() - t0 < WIN:
            if reads:
                st, ms1 = cmd(port, "GET_STATUS")
                rd, ms2 = cmd(port, f"READ_CORE_{kind} {addr:x} {n}")
                ok = bool(st and st.startswith("GET_STATUS ")) and bool(rd and rd.split()[:2] == [f"READ_CORE_{kind}", f"{addr:x}"])
                bad += not ok; times += [ms1, ms2]
                time.sleep(max(0.0, 1.0 - (time.monotonic() - t0) % 1.0))
            else:
                time.sleep(0.2)
        c1 = counter(port, kind, addr, n); dt = time.monotonic() - t0
        rows.append({"window": i + 1, "reads": reads, "seconds": round(dt, 2), "frames": (c1 - c0) % wrap,
                     "frames_per_s": round(((c1 - c0) % wrap) / dt, 3),
                     **({"commands": len(times), "answers_bad_or_lost": bad,
                         "answer_ms_median": round(statistics.median(times), 2), "answer_ms_worst": round(max(times), 2)}
                        if reads else {})})
    return rows

def resume(port):
    """Running again: PAUSE_TOGGLE only when GET_STATUS says PAUSED (FRAMEADVANCE leaves the core paused)."""
    st, _ = cmd(port, "GET_STATUS")
    if st and "PAUSED" in st:
        cmd(port, "PAUSE_TOGGLE", answer=False); time.sleep(0.3)
    st, _ = cmd(port, "GET_STATUS")
    return st

def session(rom, system, tmp):
    s = P.Session(rom, system, tmp); s.wait_playing(); time.sleep(1.0); return s

def dump(port, kind, size):
    out = bytearray()
    for a in range(0, size, 16384):
        r, _ = cmd(port, f"READ_CORE_{kind} {a:x} {min(16384, size - a)}", 2.0)
        out += bytes(int(b, 16) for b in r.split()[2:])
    return bytes(out)

tmp = Path(tempfile.mkdtemp(prefix="b99_settle_"))
try:
    # S1 + S3 + S4: SNES
    rom = tmp / "Made Up.sfc"; rom.write_bytes(F.snes())
    s = session(rom, "snes", tmp / "snes")
    try:
        port = s.port
        print(json.dumps({"S1_snes_frames": windows(port, "RAM", 0x0000, 2, 65536)}), flush=True)
        s.pause(); time.sleep(0.3)
        c0 = counter(port, "RAM", 0, 2); times = []
        for _ in range(20):
            st, a = cmd(port, "GET_STATUS"); rd, b = cmd(port, "READ_CORE_RAM 0 2"); times += [a, b]; time.sleep(0.1)
        c1 = counter(port, "RAM", 0, 2)
        print(json.dumps({"S3_paused": {"status": st, "commands": len(times), "answer_ms_median": round(statistics.median(times), 2),
                                        "answer_ms_worst": round(max(times), 2), "counter_moved": (c1 - c0) % 65536}}), flush=True)
        st0 = resume(port)                                          # running again
        stats = {k: {"sent": 0, "answered": 0, "matched": 0, "crossed": 0} for k in ("status", "read", "save", "hold")}
        stop = time.monotonic() + 30; lock = threading.Lock()
        def note(k, ans, want):
            with lock:
                stats[k]["sent"] += 1
                if ans is not None:
                    stats[k]["answered"] += 1
                    if want(ans): stats[k]["matched"] += 1
                    else: stats[k]["crossed"] += 1
        def poll():
            while time.monotonic() < stop:
                a, _ = cmd(port, "GET_STATUS"); note("status", a, lambda x: x.startswith("GET_STATUS ")); time.sleep(0.1)
        def reads():
            i = 0
            while time.monotonic() < stop:
                addr = (0x0000, 0x1000, 0x1200)[i % 3]; i += 1
                a, _ = cmd(port, f"READ_CORE_RAM {addr:x} 4")
                note("read", a, lambda x, addr=addr: x.split()[:2] == ["READ_CORE_RAM", f"{addr:x}"] and len(x.split()) == 6)
                time.sleep(0.25)
        def saves():
            while time.monotonic() < stop:
                cmd(port, "SAVE_STATE", answer=False); note("save", None, None); time.sleep(3.0)
        def hold():
            while time.monotonic() < stop:
                time.sleep(4.0)
                cmd(port, "PAUSE_TOGGLE", answer=False)
                a, _ = cmd(port, "GET_STATUS"); note("hold", a, lambda x: x.startswith("GET_STATUS "))
                time.sleep(0.5); cmd(port, "PAUSE_TOGGLE", answer=False)
        th = [threading.Thread(target=f) for f in (poll, reads, saves, hold)]
        [t.start() for t in th]; [t.join() for t in th]
        saved = sorted(p.name for p in (tmp / "snes" / "states").rglob("*") if p.is_file())
        print(json.dumps({"S4_interleaved_30s": stats, "status_at_start": st0, "state_files_written": len(saved)}), flush=True)
    finally:
        s.close()
    # S2: PS1
    rom = tmp / "Made Up.exe"; rom.write_bytes(F.psx_exe())
    s = session(rom, "ps1", tmp / "ps1")
    try:
        port = s.port; s.pause(); time.sleep(0.3)
        a = dump(port, "RAM", 0x200000)
        for _ in range(30):
            cmd(port, "FRAMEADVANCE", answer=False); time.sleep(0.05)
        time.sleep(0.3); b = dump(port, "RAM", 0x200000)
        for _ in range(30):
            cmd(port, "FRAMEADVANCE", answer=False); time.sleep(0.05)
        time.sleep(0.3); c = dump(port, "RAM", 0x200000)
        hits = []
        for off in range(0, 0x200000, 4):
            x, y, z = (int.from_bytes(m[off:off + 4], "little") for m in (a, b, c))
            if y - x == 30 and z - y == 30:
                hits.append(off)
        moved = sum(1 for k in range(0x200000) if a[k] != c[k])
        print(json.dumps({"S2_ps1_counter_search": {"bytes_changed_over_60_frames": moved, "words_plus_30_twice": len(hits),
                                                    "first": [hex(h) for h in hits[:4]]}}), flush=True)
        st0 = resume(port)
        if hits:
            print(json.dumps({"S2_status_before_windows": st0}), flush=True)
            print(json.dumps({"S2_ps1_frames": windows(port, "RAM", hits[0], 4, 1 << 32)}), flush=True)
    finally:
        s.close()
    # S5: N64
    rom = tmp / "Made Up.z64"; rom.write_bytes(fixture_n64.build()[0])
    s = session(rom, "n64", tmp / "n64")
    try:
        port = s.port; out = {}
        for q in ("READ_CORE_RAM 400 4", "READ_CORE_MEMORY 400 4", "READ_CORE_MEMORY 80000400 4", "READ_CORE_RAM 402 2"):
            a, ms = cmd(port, q, 0.5); out[q] = {"answer": a, "ms": round(ms, 2)}
        print(json.dumps({"S5_n64_reads_b61_rom": out}), flush=True)
    finally:
        s.close()
finally:
    shutil.rmtree(tmp, ignore_errors=True)
