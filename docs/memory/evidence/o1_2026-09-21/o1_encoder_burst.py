#!/usr/bin/env python3
"""O1, third pass: is the loss locked to the content rather than the clock?

The two sessions restart the same title from scratch, so the attract loop
replays identically. If the per-minute loss series of two separate sessions
agree, the loss is a function of the session's own elapsed time -- which no
environmental account (air, interference, the Opal) predicts.

This also reads the host encoder's own progress line out of
`logs/games/native_video_alpha.log` (cumulative `size=NNNKiB time=HH:MM:SS`,
emitted about twice a second) to separate two candidates:
  * average bitrate -- the encoder is CBR, so this is flat by construction;
  * sub-second burstiness -- the spread of the ~0.5 s rate inside a minute,
    which is the coarsest visible proxy for the per-frame micro-burst that
    `D-BASE-P3` tried and failed to pace away.

usage: o1_encoder_burst.py <scratch_dir_or_evidence_dir> <alpha_log>
"""
import json, os, re, sys, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from o1_analyze import pearson, spearman  # noqa: E402

PROG = re.compile(
    r"frame=\s*(\d+) fps=[^q]*q=[^s]*size=\s*(\d+)KiB time=(\d+):(\d+):([\d.]+)")


def encoder_runs(path):
    """The last two >18-minute encoder runs in the log, oldest first."""
    out = []
    for run in open(path, errors="replace").read().split("Exiting normally"):
        pts = [(int(m.group(1)), int(m.group(2)),
                int(m.group(3)) * 3600 + int(m.group(4)) * 60 + float(m.group(5)))
               for m in PROG.finditer(run)]
        if len(pts) > 100 and pts[-1][2] > 1100:
            out.append(pts)
    return out[-2:]


def main():
    d, alpha = sys.argv[1], sys.argv[2]
    rows = json.load(open(os.path.join(d, "per_minute_all.json")))

    def series(label, key):
        return [r[key] for r in
                sorted((x for x in rows if x["session"] == label),
                       key=lambda r: r["minute"])]

    A, B = series("A", "lost_packets"), series("B", "lost_packets")
    print("per-minute loss, session A: %s" % A)
    print("per-minute loss, session B: %s" % B)
    print("A vs B: pearson %.3f  spearman %.3f  n=%d"
          % (pearson(A, B), spearman(A, B)[0], len(A)))
    fa, fb = series("A", "forward_gap_events"), series("B", "forward_gap_events")
    print("forward gaps A vs B: pearson %.3f  spearman %.3f"
          % (pearson(fa, fb), spearman(fa, fb)[0]))

    runs = encoder_runs(alpha)
    if len(runs) < 2:
        print("\nencoder log: fewer than two long runs found; skipping")
        return
    mx, sd, loss, fg = [], [], [], []
    for label, pts in zip(["A", "B"], runs):
        inst = {}
        for (_, s0, t0), (_, s1, t1) in zip(pts, pts[1:]):
            dt = t1 - t0
            if 0.3 < dt < 1.5:
                inst.setdefault(int(t0 // 60), []).append(8 * (s1 - s0) / dt)
        mean = {m: sum(v) / len(v) for m, v in inst.items()}
        ks = sorted(set(inst) & set(range(len(series(label, "minute")))))
        l = series(label, "lost_packets")
        print("\nsession %s: mean encoded rate %.0f..%.0f kbps over %d minutes"
              % (label, min(mean[k] for k in ks), max(mean[k] for k in ks), len(ks)))
        print("  mean rate vs loss:  pearson %.3f"
              % pearson([mean[k] for k in ks], [l[k] for k in ks]))
        mx += [max(inst[k]) for k in ks]
        sd += [st.pstdev(inst[k]) for k in ks]
        loss += [l[k] for k in ks]
        fg += [series(label, "forward_gap_events")[k] for k in ks]
    n = len(loss) // 2
    print("\npooled n=%d" % len(loss))
    print("  loss vs peak 0.5 s rate : pearson %.3f  spearman %.3f"
          % (pearson(mx, loss), spearman(mx, loss)[0]))
    print("  loss vs 0.5 s rate sd   : pearson %.3f  spearman %.3f"
          % (pearson(sd, loss), spearman(sd, loss)[0]))
    print("  forward gaps vs sd      : pearson %.3f  spearman %.3f"
          % (pearson(sd, fg), spearman(sd, fg)[0]))
    print("  burstiness is itself reproducible: sd A vs B pearson %.3f"
          % pearson(sd[:n], sd[n:]))


if __name__ == "__main__":
    main()
