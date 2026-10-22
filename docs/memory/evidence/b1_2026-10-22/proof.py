#!/usr/bin/env python3
"""B1: the in-process proof. Loopback only; no stream; no companion.

    B1_ROOT=<a copy holding companion/> python3 -B proof.py [out_dir]

A. The downlink: G8-P1's synthetic source (60 fps x 12 packets) -> Shim(blackout-4s@down,every=20s,first=10s) ->
   a capture, 60 s; and the default blackout-4s@both over 60 s (nothing before 120 s).
B. The uplink: the real NativeControllerBridge receive loop on the loopback at 430 packets/s for 60 s, gated by
   blackout-4s@both,every=20s,first=10s; recovery's silence callback at 1,000 ms.
C. Both on one clock: A's downlink and B's uplink at once, from one shared Blackout.
D. The HTTP gates (heartbeat, client_health) through the shared gate, in and out of a dark span.
E. Flag absent: the hooked functions' AST with the guarded `if _impairment_uplink ...` removed == HEAD's (git);
   a fresh process with no flag imports no `impairment`.
F. The cost: the gate's per-call time; the shim thread's CPU in A.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
ROOT = Path(os.environ.get("B1_ROOT", str(REPO)))
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(ROOT / "tests" / "impairment"))
SECONDS = int(os.environ.get("B1_SECONDS", "60"))

import impairment as imp  # noqa: E402

_g = importlib.util.spec_from_file_location("g8p1", HERE.parent / "g8_p1_2026-10-16" / "proof.py")
G8 = importlib.util.module_from_spec(_g)
_g.loader.exec_module(G8)                      # source(), Capture, rtp(); runs nothing
import test_blackout as TB  # noqa: E402       # run_bridge(): the real receive loop, gamepads stubbed

FRAME = 1.0 / G8.FPS


def dark_spans(times, min_gap):
    return [(a, b - a) for a, b in zip(times, times[1:]) if b - a > min_gap]


def downlink(spec, seconds, blackout=None):
    p = imp.parse(spec)
    cap = G8.Capture()
    shim = imp.Shim(p, listen_port=0, forward=cap.addr, blackout=blackout)
    shim.start()
    t0 = time.monotonic()
    t0_ns = time.perf_counter_ns()
    sent = G8.source((G8.LOOP, shim.port), seconds)
    time.sleep(0.3)
    shim.stop()
    got = cap.finish()
    times = [(ns - t0_ns) / 1e9 for ns, _ in got]
    c = shim.impairer.counters.as_dict()
    return {"spec": spec, "t0": t0, "sent": sent, "got": len(got), "spans": dark_spans(times, 0.1),
            "dropped_share_pct": round(100.0 * (sent - len(got)) / sent, 2), "counters": c}


def main(out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    res, lines, ok = {}, ["# B1 proof (in process, loopback only)", ""], True

    # A
    a = downlink("blackout-4s@down,every=20s,first=10s", SECONDS)
    starts = [round(s, 3) for s, _ in a["spans"]]
    lens = [round(g, 3) for _, g in a["spans"]]
    a_ok = (len(a["spans"]) == 3 and all(abs(s - e) <= 2 * FRAME for s, e in zip(starts, (10, 30, 50)))
            and all(abs(g - 4.0 - FRAME) <= 2 * FRAME for g in lens)
            and abs(a["dropped_share_pct"] - 20.0) <= 0.5
            and a["counters"]["dropped_blackout"] == a["sent"] - a["got"])
    a2 = downlink("blackout-4s@both", SECONDS)
    a2_ok = a2["got"] == a2["sent"] and a2["counters"]["dropped_blackout"] == 0
    ok &= a_ok and a2_ok
    res["A"] = {"blackout": a, "default_both": a2}
    lines += ["## A. The downlink", "",
              f"- `blackout-4s@down,every=20s,first=10s`, {SECONDS} s: sent {a['sent']}, received {a['got']}, dropped "
              f"{a['dropped_share_pct']} % (`dropped_blackout` {a['counters']['dropped_blackout']}); dark spans start "
              f"{starts} s, last {lens} s (the gap between the last packet before and the first after: 4 s + one "
              f"frame). Tolerance: 3 spans at 10 / 30 / 50 s ± 2 frames, each 4 s + 1 frame ± 2 frames, 20 % ± 0.5: "
              f"**{'MET' if a_ok else 'NOT MET'}**.",
              f"- `blackout-4s@both` (defaults: every 120 s, the first at 120 s), {SECONDS} s: dropped "
              f"{a2['sent'] - a2['got']}: **{'MET' if a2_ok else 'NOT MET'}** (nothing before 120 s).",
              f"- The shim thread's CPU: {round(100 * a['counters']['cpu_s'] / SECONDS, 2)} % / "
              f"{round(100 * a2['counters']['cpu_s'] / SECONDS, 2)} % of a core (G8-P1: 2.1-7.0 %).", ""]

    # B
    epoch = time.monotonic()
    gate = imp.UplinkGate(imp.Blackout(4.0, 20.0, 10.0, epoch=epoch))
    b = TB.run_bridge(float(SECONDS), gate, silence_ms=1000.0)
    spans = [(round(s - epoch, 3), round(g, 3)) for s, g in dark_spans(b["applied"], 0.06)]
    neut = [round(t - epoch, 2) for t, _ in b["neutralized"]]
    sil = [(round(t - epoch, 2), round(ms)) for t, ms in b["silences"]]
    expect_dropped = sum(1 for k in range(b["sent"]) if gate.blackout.active(b["t0"] + k / 430.0))
    b_ok = (len(spans) == 3 and all(abs(s - e) <= 0.06 for (s, _), e in zip(spans, (10, 30, 50)))
            and all(abs(g - 4.0) <= 0.06 for _, g in spans) and len(sil) == 3
            and abs(gate.dropped["controller"] - expect_dropped) <= 2 * 430 * 0.01 + 2)
    ok &= b_ok
    res["B"] = {"sent": b["sent"], "applied": len(b["applied"]), "spans": spans, "silences": sil,
                "neutralized_at": neut, "uplink_dropped": gate.dropped, "expected_dropped": expect_dropped}
    lines += ["## B. The uplink (the real controller-bridge receive loop)", "",
              f"- 430 packets/s for {SECONDS} s: sent {b['sent']}, applied {len(b['applied'])}, `uplink_dropped` "
              f"{gate.dropped['controller']} (the schedule's count of sends in the dark: {expect_dropped}).",
              f"- Applied-packet gaps > 60 ms: {spans} (start s, length s).",
              f"- Recovery's silence callback (threshold 1,000 ms): {len(sil)} calls at {sil} (s, ms).",
              f"- Neutralize calls at {neut} s (once per blackout, ~250 ms in).",
              f"- Tolerance: 3 gaps of 4.0 s ± 60 ms at 10 / 30 / 50 s, no other, 3 silence calls, the drop count ± "
              f"the sender's 1 % timing: **{'MET' if b_ok else 'NOT MET'}**.", ""]

    # C
    shared = imp.Blackout(4.0, 20.0, 10.0, epoch=time.monotonic())
    gate_c = imp.UplinkGate(shared)
    box = {}
    th = threading.Thread(target=lambda: box.update(down=downlink("blackout-4s@down,every=20s,first=10s",
                                                                    SECONDS, blackout=shared)))
    th.start()
    up = TB.run_bridge(float(SECONDS), gate_c, silence_ms=1000.0)
    th.join()
    d_starts = [round(box["down"]["t0"] + s - shared.epoch, 3) for s, _ in box["down"]["spans"]]
    u_starts = [round(s - shared.epoch, 3) for s, _ in dark_spans(up["applied"], 0.06)]
    diffs = [round(abs(x - y) * 1000) for x, y in zip(d_starts, u_starts)]
    c_ok = len(d_starts) == len(u_starts) == 3 and max(diffs) <= 20 + 1000 * 2 * FRAME
    ok &= c_ok
    res["C"] = {"down_starts": d_starts, "up_starts": u_starts, "diff_ms": diffs}
    lines += ["## C. Both directions on one clock", "",
              f"- Downlink dark spans start {d_starts} s, uplink {u_starts} s after the shared epoch: within "
              f"{diffs} ms. Tolerance ≤ 20 ms + 2 frames: **{'MET' if c_ok else 'NOT MET'}**.", ""]

    # D
    clock = {"t": 0.0}
    g = imp.UplinkGate(imp.Blackout(4.0, 20.0, 10.0, epoch=0.0), clock=lambda: clock["t"])
    seen = []
    for t in (5.0, 10.5, 13.9, 14.1, 31.0):
        clock["t"] = t
        seen.append((t, g.drop("heartbeat"), g.drop("client_health")))
    d_ok = [x[1] for x in seen] == [False, True, True, False, True] and g.dropped["heartbeat"] == 3
    ok &= d_ok
    res["D"] = {"seen": seen, "dropped": g.dropped}
    lines += ["## D. The HTTP gates", "",
              f"- heartbeat / client_health at {[x[0] for x in seen]} s: {[(x[1], x[2]) for x in seen]}; counted "
              f"{g.dropped}: **{'MET' if d_ok else 'NOT MET'}**.", ""]

    # E
    # every guarded statement of B1, B2 and B3 (the queue's three flags absent), so the comparison is with HEAD
    later = ("self._input_hold is not None", "_input_hold is not None", "_LINK_FIELDS is not None",
             "LINK_FIELDS is not None")

    def any_b(node):
        return TB.is_hook(node) or ast.unparse(node.test) in later

    def strip(tree):
        class T(ast.NodeTransformer):
            def visit_If(self, node):
                self.generic_visit(node)
                if any_b(node):
                    return None
                return node
        return T().visit(tree)

    def funcs(src, names):
        tree = strip(ast.parse(src))
        found = {}
        for n in ast.walk(tree):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names:
                found.setdefault(n.name, []).append(ast.dump(n))
        return found

    targets = {"companion/native_session_io.py": ["_receive_loop"], "companion/plugins/games.py": ["handle", "_handle_action", "route"],
               "companion/privyhub_service.py": ["do_POST"]}
    e_rows = []
    for rel, names in targets.items():
        head = subprocess.run(["git", "-C", str(REPO), "show", f"HEAD:{rel}"], capture_output=True, text=True,
                              check=True).stdout
        now = (ROOT / rel).read_text()
        hooked = [n.name for n in ast.walk(ast.parse(now)) if isinstance(n, (ast.FunctionDef,)) and any(
            isinstance(x, ast.If) and TB.is_hook(x) for x in ast.walk(n))]
        # the function that holds the hook, compared whole
        holder = hooked[-1] if hooked else None
        fh2, fn2 = funcs(head, [holder]), funcs(now, [holder])
        same = fh2 == fn2 and bool(fh2)
        e_rows.append((rel, holder, same))
    env = {k: v for k, v in os.environ.items() if k != imp.FLAG_ENV}
    fresh = subprocess.run([sys.executable, "-B", "-c", "import sys; sys.path.insert(0, 'companion'); "
                            "import native_session_io as n; print('impairment' in sys.modules, n._impairment_uplink)"],
                           cwd=ROOT, env=env, capture_output=True, text=True, timeout=120).stdout.strip()
    e_ok = all(r[2] for r in e_rows) and fresh == "False None"
    ok &= e_ok
    res["E"] = {"functions": e_rows, "fresh_process": fresh}
    lines += ["## E. Flag absent", "",
              "| file | the function holding the hook | AST, every guarded B1-B3 statement removed, == HEAD's |",
              "| --- | --- | --- |"]
    lines += [f"| `{r}` | `{h}` | {'**identical**' if s else 'DIFFERS'} |" for r, h, s in e_rows]
    lines += ["", f"- A fresh process with no flag, importing `native_session_io`: `impairment` imported / the gate = "
                  f"`{fresh}` (want `False None`).", f"- **{'MET' if e_ok else 'NOT MET'}**.", ""]

    # F
    gf = imp.UplinkGate(imp.Blackout(4.0, 120.0, 120.0, epoch=time.monotonic()))
    n = 1_000_000
    t = time.perf_counter_ns()
    for _ in range(n):
        gf.drop("controller")
    per = (time.perf_counter_ns() - t) / n
    res["F"] = {"gate_ns_per_call": round(per, 1), "controller_packets_per_s": 430,
                "gate_core_pct_at_430": round(per * 430 / 1e9 * 100, 4)}
    lines += ["## F. The cost", "",
              f"- The gate: {round(per)} ns a call (outside a blackout); at 430 controller packets/s that is "
              f"{res['F']['gate_core_pct_at_430']} % of a core. The heartbeat / client-health gates run once per 2 s.",
              "- The shim thread: §A's line (G8-P1's cost bar, reported there as not met, is not re-litigated).", ""]
    lines.append(f"**All: {'MET' if ok else 'NOT MET'}**")
    (out / "proof_tables.md").write_text("\n".join(lines) + "\n")
    (out / "proof.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE))
