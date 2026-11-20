#!/usr/bin/env python3
"""Queue BG B178: how far the label stage's checks catch a misread label — made-up titles through the tool's label
and learn (the kept saves and register's PASS written as rehearse's scratch writes them; each reading given as the
session would). One line each; temp folder (TMPDIR) removed; numbers and lines only. usage: table.py <work copy>"""
import contextlib, io, json, os, shutil, sys, tempfile
from pathlib import Path
W = Path(sys.argv[1]); sys.path[:0] = [str(W / "tools"), str(W / "tests/b178_score_kind")]
T = Path(tempfile.mkdtemp(prefix="b178_table_"))
os.environ.update({"PRIVYHUB_ADD_GAME_HOME": str(T / "home"), "PRIVYHUB_ADD_GAME_EVIDENCE": str(T / "ev"),
                   "PRIVYHUB_H7_RULES": str(T / "rules"), "PRIVYHUB_ADD_GAME_LOGS": str(T / "logs"),
                   "PARTY_ADD_GAME_CAPTURE": "score_capture:capture", "PRIVYHUB_ADD_GAME_HUB": "http://127.0.0.1:9"})
(T / "rules").mkdir(parents=True)
import party_add_game as pag
A = {"begin": {"kind": "begin"}, "other": {"kind": "other"},
     "end_P1": {"kind": "end", "s": [21, 14], "look": 1}, "end_P1_2": {"kind": "end", "s": [42, 12], "look": 2},
     "end_P2": {"kind": "end", "s": [14, 24], "look": 3}, "end_P2_2": {"kind": "end", "s": [12, 41], "look": 4}}
B = {"begin": {"kind": "begin"}, "other": {"kind": "other"},
     "end_P1": {"kind": "end", "s": [15, 2], "look": 1}, "end_P1_2": {"kind": "end", "s": [35, 28], "look": 2},
     "end_P2": {"kind": "end", "s": [0, 22], "look": 3}, "end_P2_2": {"kind": "end", "s": [0, 29], "look": 4}}
N = [0]
def put(code, saves):
    kf = pag.kept_folder(code); kf.mkdir(parents=True, exist_ok=True)
    for r, s in saves.items():
        N[0] += 1; (kf / f"{r}.state").write_text(json.dumps({**s, "n": N[0]}))
    bp = pag.binding_path(code)
    b = json.loads(bp.read_text()) if bp.is_file() else {"code": code, "game": "madeup" + code.lower(), "players": 2,
        "system": "ps1", "result": "score", "cheat": None, "relative_path": "", "title": "", "content": ""}
    b["register_inputs"] = pag.register_inputs(b, pag.kept_states(code)); bp.write_text(json.dumps(b))
    pag.verdict_path(code, "register").parent.mkdir(parents=True, exist_ok=True)
    pag.verdict_path(code, "register").write_text(json.dumps({"verdict": "PASS", "inputs": b["register_inputs"]}))
def tool(*a):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = pag.main([str(x) for x in a])
    return rc, buf.getvalue().strip().splitlines()
def rd(x, y=None):
    return "-".join(map(str, x)) + "," + "-".join(map(str, y if y is not None else x))
def label(code, saves, wrong):
    args = [f"{r}={rd(s['s'])}" for r, s in sorted(saves.items()) if r.startswith("end_") and r not in wrong]
    return tool("label", code, *args, *[f"{r}={v}" for r, v in wrong.items()])
def line(out):
    return (out[1] if len(out) > 1 else out[0])[:150]
rows = [("the readings right", "T91", A, {}),
        ("one of its two readings misread (21-11 for 21-14)", "T92", A, {"end_P1": rd([21, 14], [21, 11])}),
        ("a digit misread as a digit other saves show, twice (24-14 for 21-14)", "T93", A, {"end_P1": rd([24, 14])}),
        ("a digit misread as a digit no save shows, twice (21-17 for 21-14)", "T94", A, {"end_P1": rd([21, 17])}),
        ("the sides swapped (14-21 for 21-14)", "T95", A, {"end_P1": rd([14, 21])}),
        ("a digit dropped (42-2 for 42-12)", "T96", A, {"end_P1_2": rd([42, 2])}),
        ("a digit only this save shows misread, twice (16-2 for 15-2; T90's shape)", "T97", B, {"end_P1": rd([16, 2])}),
        ("one glyph misread the same way in every save (every 4 read as 9)", "T98", A,
         {r: rd([int(str(x).replace("4", "9")) for x in s["s"]]) for r, s in A.items() if r.startswith("end_")})]
print("| a misread label | label | its line | learn |")
print("| --- | --- | --- | --- |")
for name, code, saves, wrong in rows:
    put(code, saves)
    rc, out = label(code, saves, wrong)
    lrn = "-"
    if rc == 0:
        rc2, out2 = tool("learn", code)
        lrn = "PASS" if rc2 == 0 else "FAIL: " + line(out2)
        if code == "T97":                                  # then one more save showing its digits, labelled right
            put(code, {"end_P1_3": {"kind": "end", "s": [39, 18], "look": 7}})
            rc3, out3 = tool("label", code, f"end_P1_3={rd([39, 18])}")
            lrn += " — then one more save (39-18), label: " + ("PASS" if rc3 == 0 else "FAIL: " + line(out3))
    print(f"| {name} | {'PASS' if rc == 0 else 'FAIL'} | {line(out) if rc else '-'} | {lrn} |")
shutil.rmtree(T)
