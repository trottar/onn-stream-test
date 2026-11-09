#!/usr/bin/env python3
"""H2-P1 redact check: every file under <root> against the paths file's values, the GameCube titles' file names,
stems and words, the titles' game ids (from the hub's state-file names), IPv4-like strings and mount paths.
Prints OK / HIT per file (the hit's class only, never the value)."""
import json, os, re, sys

root = sys.argv[1]
R = os.path.expanduser('~/Projects/onn-stream-test')
P = {}
for ln in open(f'{R}/runtime/h3_p1_paths.txt'):
    if '=' in ln:
        k, v = ln.rstrip('\n').split('=', 1)
        P[k] = v
T = json.load(open(f'{R}/data/games/gamecube/probe/titles.json'))
generic = {'usa', 'rvz', 'iso', 'the', 'and', 'ntsc', 'pal', 'rev', 'disc', 'europe', 'japan', 'game'}
words = set()
vals = [v for v in P.values() if v]
for k in ('T1', 'T2'):
    stem = os.path.splitext(os.path.basename(T[k]))[0]
    vals += [T[k], stem]
    words |= {w.lower() for w in re.findall(r'[A-Za-z]{3,}', stem) if w.lower() not in generic}
ids = set()
sd = f'{R}/data/games/gamecube/user/StateSaves'
if os.path.isdir(sd):
    ids |= {f.split('.')[0] for f in os.listdir(sd)}
ip = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
bad = 0
for dp, _, fs in os.walk(root):
    for f in sorted(fs):
        p = os.path.join(dp, f)
        t = open(p, errors='replace').read()
        low = t.lower()
        hits = []
        if any(v in t for v in vals):
            hits.append('a paths-file / title-file value')
        wh = [w for w in words if re.search(r'\b' + re.escape(w) + r'\b', low)]
        if wh:
            hits.append(f'{len(wh)} title word(s)')
        if any(i and i in t for i in ids):
            hits.append('a game id')
        if ip.search(t):
            hits.append('an IPv4-like string')
        if re.search(r'/mnt/|/media/', t):
            hits.append('a mount path')
        print(('HIT  ' if hits else 'OK   ') + os.path.relpath(p, root) + ('  (' + ', '.join(hits) + ')' if hits else ''))
        bad += bool(hits)
print('files with hits:', bad, '| title words checked:', len(words), '| game ids checked:', len(ids))
