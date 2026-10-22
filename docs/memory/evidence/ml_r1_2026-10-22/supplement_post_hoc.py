#!/usr/bin/env python3
"""ML-R1 POST-HOC SUPPLEMENT -- NOT PRE-REGISTERED; written after the hashed run's results were read (2026-10-22).

Why: the hashed false-alarm definition (an episode with no hitch in it) is met by an alarm that is always on (one long
episode per session always holds a hitch), and the hashed thresholds came out at that degenerate point (alarm on
597-600 s per 10 min). This script reads the FROZEN run (features.npz, scores_heldout.npz, model_*.json; nothing refit)
and reports two operating points that an always-on alarm cannot game, plus BENCH-R1 cell 8, which the hashed
eligibility rule dropped (its session ended 14 s after the gap log's last row):
  (a) strict: the lowest threshold whose false-alarm SECONDS (alarm and hitch_next_k = 0) on the training clean
      references (out-of-fold scores) are <= 1 per 10 min;
  (b) duty-matched: the threshold whose alarm seconds per 10 min on the training clean references equal the 250-ms
      silence rule's on the same rows.
Nothing here changes the hashed result or its reading. -> supplement/supplement.json, supplement/supplement.md
"""
import importlib.util, json, shutil, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / "supplement"
OUT.mkdir(exist_ok=True)
sys.argv = [sys.argv[0]]
sp = importlib.util.spec_from_file_location("pipe", HERE / "ml_r1_pipeline.py")
P = importlib.util.module_from_spec(sp)
sp.loader.exec_module(P)
P.status = lambda **kw: None                 # the finished unit's status line is left as it is
P.log = lambda *a: print("[supplement]", *a)  # and its log
sp = importlib.util.spec_from_file_location("hp", HERE.parents[3] / "tools/hitch_predictor.py")
HP = importlib.util.module_from_spec(sp)
sp.loader.exec_module(HP)

D = np.load(HERE / "features.npz")
X, Y, C, S, CR = D["X"], D["Y"], D["C"], D["S"], D["CR"]
SC = np.load(HERE / "scores_heldout.npz")
fm = json.loads((P.WORK / "features_meta.json").read_text())
sets, inputs = fm["sets"], fm["inputs"]
col = {c: i for i, c in enumerate(inputs)}
sid = {s: i for i, s in enumerate(sets)}
sess, t = C[:, 2].astype(int), C[:, 3].astype(int)
tr = S == sid["train"]
sil250 = X[:, col["ctrl_max_in_sec"]] >= 0.25


def fa_seconds(al, y):
    return float(((al) & (y == 0)).sum() / (len(al) / 600.0)) if len(al) else float("nan")


def evaluate(al, k):
    out = {}
    ki = k - 1
    hnow = Y[:, -1]
    groups = {"heldout_evenings": (S == sid["heldout_ux_r1"]) | (S == sid["heldout_ux_r2"]),
              **{s: S == sid[s] for s in sets if s != "train"}, "train_oof": tr}
    for g, gm in groups.items():
        o = np.nonzero(gm)[0]
        o = o[np.lexsort((t[o], sess[o]))]
        rc, tot, orc, ot, leads = P.recall(al[o], hnow[o], t[o], sess[o], k)
        lab = o[~np.isnan(Y[o, ki])]
        e = {"recall": rc, "hitch_seconds": tot, "onset_recall": orc, "onsets": ot, "lead_median": float(np.median(leads)) if leads else None,
             "alarm_s_per_10min": float(al[o].sum() / (len(o) / 600))}
        for side, code in (("train_clean", 1), ("heldout_clean", 2)):
            cm = lab[CR[lab] == code]
            if len(cm):
                e[f"fa_seconds_per_10min_{side}"] = round(fa_seconds(al[cm], Y[cm, ki]), 3)
                e[f"fa_episodes_per_10min_{side}"] = round(P.fa_rate(al[cm], Y[cm, ki], t[cm], sess[cm])[0], 3)
        out[g] = e
    mom = {}
    for ename, (ev, a, b) in P.EVENTS.items():
        gm = S == sid["heldout_" + ev]
        E = int(P.ts(a)) if b is None else min(int(x) for x, h, g in zip(t, Y[:, -1], gm) if g and h > 0 and P.ts(a) <= x <= P.ts(b))
        w = gm & (t >= E - 10) & (t <= E - 2)
        f = t[w & al]
        mom[ename] = {"E": P.sec(E), "fires_ge2s_before": bool((w & al).any()), "first_alarm_s_before": int(E - f.min()) if len(f) else None,
                      "alarm_s_before_in_30s": [int(E - x) for x in sorted(t[gm & al & (t >= E - 30) & (t <= E)])]}
    out["moments"] = mom
    return out


res = {"note": "POST-HOC, not pre-registered; the frozen run's scores; nothing refit", "k": {}}
crt = np.nonzero((CR == 1) & tr)[0]
for k in (1, 2, 3):
    ki = k - 1
    lab = crt[~np.isnan(Y[crt, ki])]
    rk = {"silence_250": evaluate(sil250, k)}
    duty_rule = float(sil250[lab].sum() / (len(lab) / 600))
    for m in ("logreg", "hgb"):
        s = SC[f"{m}_k{k}"]
        sc = s[lab]
        cands = np.unique(np.quantile(sc, np.linspace(0, 1, 2001)))
        strict = [float(c) for c in cands if fa_seconds(sc >= c, Y[lab, ki]) <= 1.0]
        th_strict = min(strict) if strict else float(sc.max()) + 1e-9
        duty = [(abs(float((sc >= c).sum() / (len(lab) / 600)) - duty_rule), float(c)) for c in cands]
        th_duty = min(duty)[1]
        rk[f"{m}_strict"] = {"threshold": th_strict, **evaluate(s >= th_strict, k)}
        rk[f"{m}_duty_matched"] = {"threshold": th_duty, "rule_duty_s_per_10min_train_clean": round(duty_rule, 2), **evaluate(s >= th_duty, k)}
    res["k"][str(k)] = rk

# BENCH-R1 cell 8: the pipeline's own feature code, the session forced eligible, into supplement/cell8/ (frozen models)
inv = json.loads((HERE / "inventory.json").read_text())
c8 = [r for r in inv["sessions"] if (r.get("bench_cell") or "").startswith("08")][0]
c1 = [r for r in inv["sessions"] if (r.get("bench_cell") or "").startswith("01")][0]
d8 = OUT / "cell8"
w8 = OUT / "cell8_work"
d8.mkdir(exist_ok=True)
w8.mkdir(exist_ok=True)
inv2 = dict(inv)
inv2["sessions"] = [dict(r, eligible=(r["i"] in (c8["i"], c1["i"])), set=("heldout_bench8" if r["i"] == c8["i"] else r["set"]))
                    for r in inv["sessions"]]
(d8 / "inventory.json").write_text(json.dumps(inv2))
shutil.copy(P.WORK / "hitch_seconds.json", w8 / "hitch_seconds.json")
P.HERE, P.WORK = d8, w8
P.stage_features()
F = np.load(d8 / "features.npz")
X8, Y8, C8 = F["X"], F["Y"], F["C"]
m8 = C8[:, 2].astype(int) == c8["i"]
assert json.loads((w8 / "features_meta.json").read_text())["inputs"] == inputs
X8, Y8 = X8[m8], Y8[m8]
lr_m = json.loads((HERE / "model_logreg.json").read_text())
hg_m = json.loads((HERE / "model_hgb.json").read_text())
cell8 = {"session_start": c8["start"], "rows": int(len(X8)), "hitch_seconds": int(Y8[:, -1].sum()), "k": {}}
for k in (1, 2, 3):
    ki = k - 1
    lab = ~np.isnan(Y8[:, ki])
    e = {}
    for m, cls, model in (("logreg", HP.LogReg, lr_m), ("hgb", HP.Trees, hg_m)):
        sc = cls(model, k)
        s = np.array([sc.score(list(map(float, x))) for x in X8])
        for opn, th in (("hashed", sc.threshold), ("strict", res["k"][str(k)][f"{m}_strict"]["threshold"]),
                        ("duty_matched", res["k"][str(k)][f"{m}_duty_matched"]["threshold"])):
            al = s >= th
            e[f"{m}_{opn}"] = {"alarm_s_per_10min": round(float(al.sum() / (len(al) / 600)), 2),
                               "fa_seconds_per_10min": round(fa_seconds(al[lab], Y8[lab, ki]), 2)}
    for H in (250, 950):
        al = X8[:, col["ctrl_max_in_sec"]] >= H / 1000
        e[f"silence_{H}"] = {"alarm_s_per_10min": round(float(al.sum() / (len(al) / 600)), 2),
                             "fa_seconds_per_10min": round(fa_seconds(al[lab], Y8[lab, ki]), 2)}
    cell8["k"][str(k)] = e
res["cell8_frozen"] = cell8
(OUT / "supplement.json").write_text(json.dumps(res, indent=1, default=str) + "\n")


def pc(x):
    return "—" if x is None or x != x else f"{100 * x:.1f} %"


L = ["# ML-R1 POST-HOC SUPPLEMENT (not pre-registered; the frozen run; nothing refit)", ""]
for k in ("1", "2", "3"):
    L += [f"## k = {k}", "", "| operating point | set | recall (hitch s) | onset recall | lead median s | alarm s / 10 min | FA s / 10 min, train clean | FA s / 10 min, held-out clean |",
          "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for name, o in res["k"][k].items():
        for g in ("heldout_evenings", "heldout_ux_r1", "heldout_ux_r2", "heldout_bench5", "train_oof"):
            e = o[g]
            L.append(f"| {name}{' θ=' + format(o['threshold'], '.4g') if 'threshold' in o and g == 'heldout_evenings' else ''} | {g} | {pc(e['recall'])} | {pc(e['onset_recall'])} | "
                     f"{e['lead_median']} | {e['alarm_s_per_10min']:.1f} | {e.get('fa_seconds_per_10min_train_clean', '—')} | {e.get('fa_seconds_per_10min_heldout_clean', '—')} |")
    L += ["", "Moments:", "```", json.dumps({n: o["moments"] for n, o in res["k"][k].items()}, indent=1), "```", ""]
L += ["## BENCH-R1 cell 8 (none + hold), the frozen models, the session forced eligible", "", "```", json.dumps(cell8, indent=1), "```"]
(OUT / "supplement.md").write_text("\n".join(L) + "\n")
print(json.dumps({k: {n: {g: (round(o[g]["recall"], 3), round(o[g]["alarm_s_per_10min"], 1)) for g in ("heldout_evenings", "heldout_ux_r2", "heldout_bench5")}
                      for n, o in v.items()} for k, v in res["k"].items()}, indent=0))
print(json.dumps(cell8["k"]["2"]))
print(json.dumps({n: o["moments"] for n, o in res["k"]["2"].items()}))
