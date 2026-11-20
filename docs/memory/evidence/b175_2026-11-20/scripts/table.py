#!/usr/bin/env python3
"""Queue BF B175: the made-up titles through the tool's learn (the kept saves and register's PASS written as rehearse's
scratch writes them; each named save given from another look, as the user would), one line each. Temp folder (TMPDIR)
removed; only the numbers printed. usage: table.py <work copy>"""
import contextlib, io, json, os, shutil, sys, tempfile
from pathlib import Path
W = Path(sys.argv[1]); sys.path[:0] = [str(W / "tools"), str(W / "tests/b171_more_saves")]
T = Path(tempfile.mkdtemp(prefix="b175_table_"))
os.environ.update({"PRIVYHUB_ADD_GAME_HOME": str(T / "home"), "PRIVYHUB_ADD_GAME_EVIDENCE": str(T / "ev"),
                   "PRIVYHUB_H7_RULES": str(T / "rules"), "PRIVYHUB_ADD_GAME_LOGS": str(T / "logs"),
                   "PARTY_ADD_GAME_CAPTURE": "near_capture:capture"})
(T / "rules").mkdir(parents=True)
import party_add_game as pag
N = [0]
def st(kind, look=0, far=False, cur=None, mark=0):
    d = {"kind": kind, "look": look, "far": far, "mark": mark}
    if cur is not None: d["cur"] = cur
    return d
def put(code, saves):
    kf = pag.kept_folder(code); kf.mkdir(parents=True, exist_ok=True)
    for r, s in saves.items():
        N[0] += 1; (kf / f"{r}.state").write_text(json.dumps({**s, "n": N[0]}))
    bp = pag.binding_path(code)
    b = json.loads(bp.read_text()) if bp.is_file() else {"code": code, "game": "g" + code.lower(), "players": 2,
        "system": "ps1", "result": "winner", "cheat": None, "relative_path": "", "title": "", "content": ""}
    b["register_inputs"] = pag.register_inputs(b, pag.kept_states(code)); bp.write_text(json.dumps(b))
    pag.verdict_path(code, "register").parent.mkdir(parents=True, exist_ok=True)
    pag.verdict_path(code, "register").write_text(json.dumps({"verdict": "PASS", "inputs": b["register_inputs"]}))
def learn(code):
    with contextlib.redirect_stdout(io.StringIO()):
        rc = pag.main(["learn", code])
    v = pag.load_verdict(code, "learn"); return rc, v
def row(code, label, saves, looks=(), kinds=None):
    put(code, saves); rc, v = learn(code); first = v; asked = []; looks = iter(looks)
    while rc and (v.get("recorded") or {}).get("one more save") and looks:
        try: lk = next(looks)
        except StopIteration: break
        role = v["recorded"]["one more save"]; asked.append(role)
        put(code, {role: st((kinds or {}).get(pag._role_class(role), pag._role_class(role)), lk)}); rc, v = learn(code)
    cells = first["cells"]
    today = [c["cell"] for c in cells if not c["met"] and not c["cell"].startswith("left out: ") and c["cell"] != "no two saves of one ending the same picture"]
    lo = [c for c in cells if c["cell"].startswith("left out: ")]
    lo_bad = [c["cell"][10:] + (f" ({c['read'][0]})" if isinstance(c["read"], list) else f" ({c['read']})" if c["read"] else " (never ended)") for c in lo if not c["met"]]
    same = [c for c in cells if c["cell"] == "no two saves of one ending the same picture"][0]
    rec = first.get("recorded") or {}
    line = next((f"{k}: {rec[k]}" for k in ("wrong role", "same match twice", "one more save", "cannot be told apart") if k in rec), "-")
    fin = v.get("recorded") or {}
    end = "PASS" if rc == 0 else ("cap: " + ", ".join(fin["cannot be told apart"]) if "cannot be told apart" in fin else
                                  "wrong role: " + " as ".join(fin["wrong role"]) if "wrong role" in fin else "FAIL")
    print(f"| {label} | {', '.join(today) or 'all met'} | {len(lo) - len(lo_bad)} of {len(lo)} met" + (f"; not: {'; '.join(lo_bad)}" if lo_bad else "") +
          f" | {'met' if same['met'] else 'not met ' + json.dumps([p[:2] for p in same['read']])} | {line} | {', '.join(asked) or '-'} | {end} |")
B, O = st("start"), st("other")
print("| made-up title (saves) | today's cells not met | left out | same picture | the line | saves asked, each from another look | then |")
print("| --- | --- | --- | --- | --- | --- | --- |")
row("T71", "one per ending, other characters in each (settle's weak pass)", {"begin": B, "other": O, "end_P1": st("end_P1", 1), "end_P2": st("end_P2", 2)})
row("T72", "two per ending, other characters in every match", {"begin": B, "other": O, "end_P1": st("end_P1", 1), "end_P1_2": st("end_P1", 2), "end_P2": st("end_P2", 3), "end_P2_2": st("end_P2", 4)}, looks=(5, 6, 7, 8))
row("T73", "near-alike two per ending, P2's first with P1's characters", {"begin": B, "other": O, "end_P1": st("end_P1", 1), "end_P1_2": st("end_P1", 2), "end_P2": st("end_P2", 1), "end_P2_2": st("end_P2", 3)}, looks=(5, 6, 7, 8))
row("T74", "near-alike three per ending, other characters", {"begin": B, "other": O, "end_P1": st("end_P1", 1), "end_P1_2": st("end_P1", 2), "end_P1_3": st("end_P1", 4), "end_P2": st("end_P2", 1), "end_P2_2": st("end_P2", 3), "end_P2_3": st("end_P2", 5)})
row("T75", "far apart, two per ending, other characters", {"begin": B, "other": O, "end_P1": st("end_P1", 1, True), "end_P1_2": st("end_P1", 2, True), "end_P2": st("end_P2", 3, True), "end_P2_2": st("end_P2", 4, True)})
row("T76", "two per ending, the same characters within (only the cursor moved)", {"begin": B, "other": O, "end_P1": st("end_P1", 1, cur=0), "end_P1_2": st("end_P1", 1, cur=3), "end_P2": st("end_P2", 2, cur=0), "end_P2_2": st("end_P2", 2, cur=3)})
row("T77", "two per ending, end_P2_2 holding a P1 win", {"begin": B, "other": O, "end_P1": st("end_P1", 1), "end_P1_2": st("end_P1", 2), "end_P2": st("end_P2", 3), "end_P2_2": st("end_P1", 4)}, looks=(5, 6, 7, 8))
row("T78", "three per ending, a large mark only the begin shows", {"begin": st("start", mark=16), "other": O, **{r: st(pag._role_class(r), l, mark=16) for r, l in (("end_P1", 1), ("end_P1_2", 2), ("end_P1_3", 4), ("end_P2", 1), ("end_P2_2", 3), ("end_P2_3", 5))}})
shutil.rmtree(T)
