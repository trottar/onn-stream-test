#!/usr/bin/env python3
"""H2 check 4: summarise the 30 s x11grab -> framemd5 of the managed window.

Same counts as GROUP_A A3-live (frames, consecutive-duplicate hashes, PTS
deltas, per-second unique counts), plus a split of duplicates into
isolated repeats (a run of identical hashes 2-3 frames long -- the
59.94-on-60 beat, or a scene cut) and static stretches (runs >= 4 frames:
the content held still, a fade or a title card).
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
rows = [l.split(',') for l in open(os.path.join(HERE, 'h2_grab_framemd5.txt')) if l[0] != '#']
pts = [int(r[1]) for r in rows]; md = [r[-1].strip() for r in rows]
d = [b - a for a, b in zip(pts, pts[1:])]
dups = [i + 1 for i, (a, b) in enumerate(zip(md, md[1:])) if a == b]
runs, i = [], 0
while i < len(md):
    j = i
    while j + 1 < len(md) and md[j + 1] == md[i]:
        j += 1
    if j > i:
        runs.append((i, j - i + 1))
    i = j + 1
iso = [r for r in runs if r[1] <= 3]; static = [r for r in runs if r[1] >= 4]
per_s = [len(set(md[s:s + 60])) for s in range(0, len(md), 60)]
out = dict(
    frames=len(rows), dups_total=len(dups),
    pts_delta_min=min(d), pts_delta_max=max(d), pts_delta_mean=sum(d) / len(d),
    pts_intervals_not_1=sum(1 for x in d if x != 1),
    isolated_repeat_runs=[{"first_frame": a, "len": n} for a, n in iso],
    dups_in_isolated_repeats=sum(n - 1 for _, n in iso),
    static_runs=[{"first_frame": a, "len": n} for a, n in static],
    dups_in_static_runs=sum(n - 1 for _, n in static),
    unique_per_second=per_s,
    seconds_at_60_unique=sum(1 for u in per_s if u == 60),
)
print(json.dumps(out, indent=1))
json.dump(out, open(os.path.join(HERE, 'h2_grab_summary.json'), 'w'), indent=1)
