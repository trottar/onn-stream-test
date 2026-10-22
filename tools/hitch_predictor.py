#!/usr/bin/env python3
"""ML-R1: the hitch early-warning detector's scorer, pure python (no numpy, no scikit-learn).

Reads the fitted models as plain numbers (docs/memory/evidence/ml_r1_2026-10-22/model_logreg.json, model_hgb.json) and
scores one per-second feature row (the columns in features_columns.txt, in order; missing = NaN):

    logreg:  p = sigmoid(intercept + sum(coef_i * ((x_i if x_i == x_i else 0) - mean_i) / scale_i))
    hgb:     p = sigmoid(baseline + sum over trees of the leaf reached: x <= thr -> left, NaN -> left iff `ml`)
    alarm:   p >= the threshold chosen on the training clean references (<= 1 false alarm / 10 min)

    python3 tools/hitch_predictor.py --selftest [--dir docs/memory/evidence/ml_r1_2026-10-22] [--per-set 4000]
        reads features.npz with zipfile + a .npy reader of its own, rescores the held-out rows (an every-n-th sample of at
        most --per-set rows per held-out set), and compares with the pipeline's scores_heldout.npz (max |diff| < 1e-5).
A detector, not a controller: nothing in the companion imports this.
"""
import argparse
import ast
import json
import math
import struct
import sys
import zipfile
from array import array
from pathlib import Path

DEFAULT_DIR = Path(__file__).resolve().parents[1] / "docs/memory/evidence/ml_r1_2026-10-22"


def sigmoid(z):
    return 1.0 / (1.0 + math.exp(-z)) if z >= 0 else math.exp(z) / (1.0 + math.exp(z))


class LogReg:
    def __init__(self, model, k):
        m = model["k"][str(k)]
        self.mean, self.scale = model["standardize"]["mean"], model["standardize"]["scale"]
        self.coef, self.b, self.threshold = m["coef"], m["intercept"], m["threshold"]

    def score(self, x):
        z = self.b
        for xi, mu, sd, c in zip(x, self.mean, self.scale, self.coef):
            z += c * (((xi if xi == xi else 0.0) - mu) / sd)
        return sigmoid(z)


class Trees:
    def __init__(self, model, k):
        m = model["k"][str(k)]
        self.trees, self.base, self.threshold = m["trees"], m["baseline"], m["threshold"]

    def score(self, x):
        z = self.base
        for t in self.trees:
            n = t[0]
            while not n["leaf"]:
                v = x[n["f"]]
                go_left = n["ml"] if v != v else v <= n["thr"]
                n = t[n["l"] if go_left else n["r"]]
            z += n["v"]
        return sigmoid(z)


def read_npy(raw):
    """A C-order .npy array -> (flat array, shape). dtypes: <f4, <f8, |i1, |b1."""
    assert raw[:6] == b"\x93NUMPY", "not a .npy"
    major = raw[6]
    hl, off = (struct.unpack("<H", raw[8:10])[0], 10) if major == 1 else (struct.unpack("<I", raw[8:12])[0], 12)
    hdr = ast.literal_eval(raw[off:off + hl].decode("latin1"))
    assert not hdr["fortran_order"]
    code = {"<f4": "f", "<f8": "d", "|i1": "b", "|b1": "b"}[hdr["descr"]]
    a = array(code)
    a.frombytes(raw[off + hl:])
    if sys.byteorder != "little" and code in "fd":
        a.byteswap()
    return a, hdr["shape"]


def read_npz(path, names):
    with zipfile.ZipFile(path) as z:
        return {n: read_npy(z.read(n + ".npy")) for n in names}


def selftest(d, per_set):
    lr_m = json.loads((d / "model_logreg.json").read_text())
    hg_m = json.loads((d / "model_hgb.json").read_text())
    F = read_npz(d / "features.npz", ["X", "S"])
    (X, xs), (S, _) = F["X"], F["S"]
    ncol = xs[1]
    assert ncol == len(lr_m["inputs"]), "the column count differs from the model's"
    Sc = read_npz(d / "scores_heldout.npz", ["heldout"] + [f"{m}_k{k}" for m in ("logreg", "hgb") for k in (1, 2, 3)])
    held = Sc["heldout"][0]
    rows = {}
    for i in range(xs[0]):
        if held[i]:
            rows.setdefault(S[i], []).append(i)
    pick = []
    for s, ix in sorted(rows.items()):
        step = max(1, len(ix) // per_set)
        pick += ix[::step][:per_set]
    worst, n = 0.0, 0
    lines = []
    for k in (1, 2, 3):
        for name, cls, model in (("logreg", LogReg, lr_m), ("hgb", Trees, hg_m)):
            sc = cls(model, k)
            ref = Sc[f"{name}_k{k}"][0]
            w = 0.0
            for i in pick:
                x = X[i * ncol:(i + 1) * ncol]
                w = max(w, abs(sc.score(x) - ref[i]))
            worst = max(worst, w)
            n += len(pick)
            lines.append(f"k={k} {name}: {len(pick)} held-out rows rescored, max |diff| {w:.2e}, threshold {sc.threshold}")
    ok = worst < 1e-5
    lines.append(f"SELFTEST {'OK' if ok else 'FAIL'}: {n} scores, max |diff| {worst:.2e} (bar 1e-5)")
    print("\n".join(lines))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    ap.add_argument("--per-set", type=int, default=4000)
    a = ap.parse_args()
    if a.selftest:
        return selftest(a.dir, a.per_set)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
