#!/usr/bin/env python3
"""Queue BE B171 "settle first": learn (the tool's own labels, the learner unchanged) on the made-up near-alike screens
of tests/b171_more_saves/near_capture.py — how many saves per ending, how different, more pictures per save. Pictures in
a temp folder (TMPDIR), removed; only the numbers printed. usage: settle_experiment.py <work copy>"""
import json, os, shutil, sys, tempfile
from pathlib import Path
W = Path(sys.argv[1])
sys.path[:0] = [str(W / "tools"), str(W / "tests/b171_more_saves")]
T = Path(tempfile.mkdtemp(prefix="b171_settle_"))
os.environ.update({"PRIVYHUB_ADD_GAME_HOME": str(T / "home"), "PRIVYHUB_H7_RULES": str(T / "rules"),
                   "PRIVYHUB_ADD_GAME_LOGS": str(T / "logs"), "PARTY_ADD_GAME_CAPTURE": "near_capture:capture"})
import party_add_game as pag, near_capture as nc
es = pag._endscreen()
def run(code, label, saves, every=pag.CAPTURE_EVERY):
    pag.CAPTURE_EVERY = every
    kf = pag.kept_folder(code); kf.mkdir(parents=True)
    for n, (role, (kind, look, far)) in enumerate(saves.items()):
        (kf / f"{role}.state").write_text(nc.state(kind, look, far, n))
    b = {"code": code, "game": "g" + code, "players": 2, "system": "ps1", "result": "winner", "cheat": None}
    kept = pag.kept_states(code); pics = pag._pictures(code, b, kept)
    (pics / "labels.json").write_text(json.dumps(pag._labels(pics, kept, es)))
    spec, arrays, rep = es.learn(pics, pics / "labels.json", "first", name=b["game"])
    sc = es.score(pics, pics / "labels.json", spec, arrays, "second")
    held = {c: r for c, r in (sc.get("confusion") or {}).items() if c not in ("other", "ignore")}
    unk = sum(r.get("unknown", 0) + r.get("other", 0) for r in held.values()) / (sum(sum(r.values()) for r in held.values()) or 1)
    print(f"| {label} | {spec['margin_needed']} | {sorted(k for k, v in spec['separable'].items() if not v) or 'all'} | "
          f"{round(unk, 3)} | {spec['outcome_mask_px']} | {sum(spec['frames'][c] for c in ('end_P1', 'end_P2'))} |")
B, O = ("start", 0, False), ("other", 0, False)
e = lambda k, l, f=False: (k, l, f)
print("| saves | margin_needed (bar 0.0796) | not separable | held-out unknown (bar 0.105) | outcome mask px | ending frames |")
print("| --- | --- | --- | --- | --- | --- |")
run("T01", "one per ending, the same characters", {"begin": B, "other": O, "end_P1": e("end_P1", 1), "end_P2": e("end_P2", 1)})
run("T02", "the same, twice the pictures", {"begin": B, "other": O, "end_P1": e("end_P1", 1), "end_P2": e("end_P2", 1)}, every=0.25)
run("T03", "two per ending, the same look", {"begin": B, "other": O, "end_P1": e("end_P1", 1), "end_P1_2": e("end_P1", 1), "end_P2": e("end_P2", 1), "end_P2_2": e("end_P2", 1)})
run("T04", "two per ending, the second other characters", {"begin": B, "other": O, "end_P1": e("end_P1", 1), "end_P1_2": e("end_P1", 2), "end_P2": e("end_P2", 1), "end_P2_2": e("end_P2", 3)})
run("T05", "three per ending, other characters", {"begin": B, "other": O, "end_P1": e("end_P1", 1), "end_P1_2": e("end_P1", 2), "end_P1_3": e("end_P1", 4), "end_P2": e("end_P2", 1), "end_P2_2": e("end_P2", 3), "end_P2_3": e("end_P2", 5)})
run("T06", "far apart, one per ending", {"begin": B, "other": O, "end_P1": e("end_P1", 1, True), "end_P2": e("end_P2", 1, True)})
run("T07", "far apart, two per ending", {"begin": B, "other": O, "end_P1": e("end_P1", 1, True), "end_P1_2": e("end_P1", 2, True), "end_P2": e("end_P2", 1, True), "end_P2_2": e("end_P2", 3, True)})
run("T08", "one per ending, different characters in each (a weak pass)", {"begin": B, "other": O, "end_P1": e("end_P1", 1), "end_P2": e("end_P2", 2)})
shutil.rmtree(T)
