#!/usr/bin/env python3
"""B101 settle (synthetic fixtures, B61's form: RetroArch headless, the hub's AppImage, cores and base config, temp
folders, the companion's display; no game). Commands sent the companion's way (a fresh UDP socket per command).
Per system (SNES: the fixture's frame counter $0000; PS1: the core's own per-frame word, B99's settle):
  L  a state made paused (B95's way: planted values P1 0 / P2 0 written, then saved paused) is loaded into RUNNING
     content as the contest would: the file put in the core's state folder as <stem>.state8, LOAD_STATE_SLOT 8, the
     command's answer, RetroArch's own load line ("[State] Loading state ..., N bytes" — the time from the command),
     the first read after it (equal to the state's own values?), the scratch removed;
  C  the clock: 10, 30 and 60 s by the hub's clock (time.monotonic) with a read (GET_STATUS + 2 fields) every second,
     against the frames the counter moved;
  E  the end: at "time is up" the counter read; then (i) the final read alone — frames until its answer; (ii) a
     hub-side pause (PAUSE_TOGGLE, GET_STATUS until PAUSED) — frames until the pause took hold, and the read after it.
usage: contest.py <repo>"""
import json, re, socket, sys, time, shutil, tempfile
from pathlib import Path
REPO = Path(sys.argv[1])
sys.path.insert(0, str(REPO / "tools")); sys.path.insert(0, str(REPO / "tests/h7_rule_search"))
import h7_minigame_proof as P, fixtures as F
LOADING = re.compile(r'\[State\] Loading state ".*", (\d+) bytes\.')

def cmd(port, text, wait=0.5, answer=True):
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

def word(port, addr, n):
    a, _ = cmd(port, f"READ_CORE_RAM {addr:x} {n}")
    p = (a or "").split()
    assert len(p) == n + 2 and int(p[1], 16) == addr, a
    return int.from_bytes(bytes(int(b, 16) for b in p[2:]), "little")

def status(port):
    return cmd(port, "GET_STATUS")[0] or ""

SPEC = {"snes": ("Made Up.sfc", F.snes, 0x0000, 2, 1 << 16, F.SNES),
        "ps1": ("Made Up.exe", F.psx_exe, 0x44EE0, 4, 1 << 32, F.PS1)}
tmp = Path(tempfile.mkdtemp(prefix="b101_settle_"))
try:
    for system, (name, build, ctr, cn, wrap, plan) in SPEC.items():
        rom = tmp / name; rom.write_bytes(build())
        pa = plan["block"] + plan["rounds"]; pb = pa + plan["stride"]
        # the state, made paused
        s = P.Session(rom, system, tmp / f"{system}_make"); s.wait_playing(); time.sleep(1.0); s.pause()
        for a in (pa, pb):
            s.send(f"WRITE_CORE_RAM {a:x} 00 00"); time.sleep(0.05)
        state = tmp / f"{system}.state"; s.save_state(state); s.close()
        # the contest's load into running content
        s = P.Session(rom, system, tmp / f"{system}_run"); s.wait_playing(); time.sleep(1.0)
        port = s.port
        cmd(port, f"WRITE_CORE_RAM {pa:x} 32 00", answer=False); cmd(port, f"WRITE_CORE_RAM {pb:x} 3c 00", answer=False)
        time.sleep(0.2)
        before = (word(port, pa, 2), word(port, pb, 2))
        scratch = s.state_path().with_name(s.state_path().name + "8")
        shutil.copyfile(state, scratch)
        off = len(s.text()); t0 = time.perf_counter()
        ans, ms = cmd(port, "LOAD_STATE_SLOT 8", 2.0)
        line_ms = None; line = None
        end = time.monotonic() + 5
        while time.monotonic() < end:
            m = LOADING.search(s.text()[off:])
            if m:
                line_ms = (time.perf_counter() - t0) * 1000; line = f"[State] Loading state, {m.group(1)} bytes"; break
            time.sleep(0.005)
        first = (word(port, pa, 2), word(port, pb, 2))
        scratch.unlink()
        st = status(port)
        print(json.dumps({system: {"L_load": {"running_before": "PLAYING" in st, "values_before": before,
                                               "answer": ans, "answer_ms": round(ms, 1), "load_line": line,
                                               "line_ms": round(line_ms, 1) if line_ms else None,
                                               "failed_line": "Failed to load state" in s.text()[off:],
                                               "first_read": first, "equals_state": first == (0, 0),
                                               "running_after": "PLAYING" in status(port)}}}), flush=True)
        # the clock
        for N in (10, 30, 60):
            c0 = word(port, ctr, cn); t0 = time.monotonic(); reads = 0
            while True:
                el = time.monotonic() - t0
                if el >= N:
                    break
                cmd(port, "GET_STATUS"); word(port, pa, 2); word(port, pb, 2); reads += 1
                time.sleep(max(0.0, min(1.0 - (time.monotonic() - t0) % 1.0, N - (time.monotonic() - t0))))
            c1 = word(port, ctr, cn); el = time.monotonic() - t0
            print(json.dumps({system: {f"C_{N}s": {"hub_seconds": round(el, 3), "frames": (c1 - c0) % wrap,
                                                    "frames_per_hub_second": round(((c1 - c0) % wrap) / el, 3),
                                                    "reads": reads}}}), flush=True)
        # the end: (i) the final read alone; (ii) a hub-side pause
        c_up = word(port, ctr, cn); t_up = time.perf_counter()
        fin = (word(port, pa, 2), word(port, pb, 2)); fin_ms = (time.perf_counter() - t_up) * 1000
        c_fin = word(port, ctr, cn)
        c_up2 = word(port, ctr, cn); t_up2 = time.perf_counter()
        cmd(port, "PAUSE_TOGGLE", answer=False)
        while "PAUSED" not in status(port) and time.perf_counter() - t_up2 < 3:
            pass
        held_ms = (time.perf_counter() - t_up2) * 1000
        c_p = word(port, ctr, cn); time.sleep(0.5); c_p2 = word(port, ctr, cn)
        after = (word(port, pa, 2), word(port, pb, 2))
        print(json.dumps({system: {"E_end": {"final_read_ms": round(fin_ms, 1), "frames_from_time_up_to_after_final_read": (c_fin - c_up) % wrap,
                                             "pause_took_hold_ms": round(held_ms, 1), "frames_from_time_up_to_paused": (c_p - c_up2) % wrap,
                                             "frames_in_0_5_s_paused": (c_p2 - c_p) % wrap, "read_after_pause": after}}}), flush=True)
        s.close()
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# F: the state folder RetroArch uses per core under the hub's base config (sorted by the core's library name?) —
#    SAVE_STATE_SLOT 8 on each core the hub runs for PS1 / SNES; the folder the file lands in (its name only).
tmp = Path(tempfile.mkdtemp(prefix="b101_settle_f_"))
try:
    out = {}
    for system, core, name, build in (("snes", "snes9x_libretro.so", "Made Up.sfc", F.snes),
                                      ("snes", "bsnes_libretro.so", "Made Up.sfc", F.snes),
                                      ("ps1", "mednafen_psx_hw_libretro.so", "Made Up.exe", F.psx_exe)):
        old = P.SYSTEMS[system]
        P.SYSTEMS[system] = (core, old[1])
        try:
            rom = tmp / name; rom.write_bytes(build())
            work = tmp / core
            s = P.Session(rom, system, work); s.wait_playing(); time.sleep(1.0)
            a, _ = cmd(s.port, "SAVE_STATE_SLOT 8", 2.0); time.sleep(1.0)
            files = [p for p in (work / "states").rglob("*.state8")]
            out[core] = {"answer": a, "folder": [p.parent.name if p.parent != work / "states" else "(the states folder itself)" for p in files]}
            s.close()
        finally:
            P.SYSTEMS[system] = old
    print(json.dumps({"F_state_folder_per_core": out}), flush=True)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
