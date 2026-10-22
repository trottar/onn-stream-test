#!/usr/bin/env python3
"""B1b: the in-process proof (loopback only; no stream; no companion).
    B1B_ROOT=<a copy holding companion/ and tests/> python3 -B proof.py
1. The gate: `desync` dropped inside a dark span, passed outside, counted by kind.
2. The plugin's real GamesPlugin.handle_post_request on a stub self (a fake recovery): a desync inside a dark span
   returns impairment=uplink_blackout and never reaches the recovery; outside it is accepted; with no gate, today.
3. A B7 stall datagram through the real receive loop while dark: dropped (counted `controller`), never parsed.
4. AST: the plugin module with B1b's one guarded statement removed == the predecessor (whole module); `@down` has
   no uplink gate. Writes proof.json and proof.md."""
import ast, json, os, sys, time, types
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B1B_ROOT", str(HERE.parents[3])))
sys.path.insert(0, str(ROOT / "companion")); sys.path.insert(0, str(ROOT / "tests" / "stall_signal"))
import impairment as imp  # noqa: E402
res = {}

class Clock:
    def __init__(self): self.t = 0.0
    def __call__(self): return self.t

c = Clock()
gate = imp.UplinkGate(imp.Blackout(4.0, 120.0, 10.0, epoch=0.0), clock=c)   # dark 10-14 s, 130-134 s
seen = []
for t in (9.9, 10.1, 13.9, 14.1, 130.5):
    c.t = t; seen.append((t, gate.drop("desync")))
res["1_gate"] = {"drop_at": seen, "dropped": dict(gate.dropped),
                 "ok": [x[1] for x in seen] == [False, True, True, False, True] and gate.dropped.get("desync") == 3}

from plugins import games as G  # noqa: E402

class Rec:
    def __init__(self): self.calls = []
    def note_client_desync(self, reason, age): self.calls.append((reason, age))
    def status(self): return {"state": "fake"}

def call(g):
    rec = Rec()
    stub = types.SimpleNamespace(PLUGIN_ID=G.GamesPlugin.PLUGIN_ID, _first=G.GamesPlugin._first,
                                 _parse_int=G.GamesPlugin._parse_int, _recovery=rec)
    G._impairment_uplink = g
    try:
        out = G.GamesPlugin.handle_post_request(stub, "native-stream-desync", "reason=output_silence&age_ms=1200",
                                                "127.0.0.1")
    finally:
        G._impairment_uplink = None
    return out, rec.calls
c.t = 11.0; dark = call(gate)
c.t = 20.0; light = call(gate)
none = call(None)
res["2_handler"] = {"dark": dark, "light": [light[0].get("accepted"), light[1]], "no_gate": [none[0].get("accepted"), none[1]],
                    "ok": dark[0].get("impairment") == "uplink_blackout" and dark[1] == []
                    and light[0].get("accepted") is True and light[1] == [("output_silence", 1200.0)]
                    and none[0].get("accepted") is True and none[1] == [("output_silence", 1200.0)]}

import test_stall_signal as TS  # noqa: E402
rig = TS.Rig()
g2 = imp.UplinkGate(imp.Blackout(10.0, 100.0, 0.0, epoch=time.monotonic()))        # dark from now, 10 s
TS.run(rig, 0.6, lambda t: (True, (TS.ss.KIND_STALL, False, 900)), gate=g2)
res["3_stall_dropped"] = {"stalls_parsed": rig.sig.stalls, "controller_dropped": g2.dropped.get("controller"),
                          "ok": rig.sig.stalls == 0 and g2.dropped.get("controller", 0) > 0}

GUARD = "_impairment_uplink is not None and _impairment_uplink.drop('desync')"
class Strip(ast.NodeTransformer):
    def visit_If(self, node):
        self.generic_visit(node)
        return None if ast.unparse(node.test) == GUARD else node
new = ast.parse((ROOT / "companion/plugins/games.py").read_text())
old = ast.parse((HERE / "predecessors/companion/plugins/games.py").read_text())
n_guards = sum(1 for n in ast.walk(new) if isinstance(n, ast.If) and ast.unparse(n.test) == GUARD)
res["4_ast"] = {"guards": n_guards, "identical_without_it": ast.dump(Strip().visit(new)) == ast.dump(old),
                "down_has_no_gate": imp.uplink_gate(imp.parse("blackout-4s@down")) is None}
res["4_ast"]["ok"] = n_guards == 1 and res["4_ast"]["identical_without_it"] and res["4_ast"]["down_has_no_gate"]
allok = all(v["ok"] for v in res.values())
(HERE / "proof.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
md = ["# B1b — proof (in process)", ""] + [f"- **{k}**: {'MET' if v['ok'] else 'NOT MET'} — " +
      json.dumps({x: y for x, y in v.items() if x != 'ok'}, default=str) for k, v in res.items()] + ["", f"**{'ALL MET' if allok else 'NOT ALL MET'}**"]
(HERE / "proof.md").write_text("\n".join(md) + "\n")
print("\n".join(md)); sys.exit(0 if allok else 1)
