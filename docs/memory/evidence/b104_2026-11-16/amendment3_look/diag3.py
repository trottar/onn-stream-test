import sys, json, csv, numpy as np
sys.path.insert(0,'tools'); import h7_endscreen as E
from PIL import Image
FR=E.Path('runtime/h7_frames'); LL=json.loads((FR/'h7v2_20261116_run/labels.json').read_text())
spec,arr,rep=E.learn(FR,LL)
M,O,refs=arr['screen_mask'],arr['outcome_mask'],arr['refs']
rows=list(csv.DictReader(open(FR/'h7v2_20261116_run/index.csv')))
lab=LL['runs']['h7v2_20261116_run']
print('classes',spec['classes'],'thr',spec['class_thresholds'])
for r in rows:
    t=float(r['seconds']); l=[x['label'] for x in lab if x['from']-1e-6<=t<=x['to']+1e-6]; l=l[0] if l else '-'
    if l not in ('start','end_P1','end_P2'): continue
    with Image.open(FR/'h7v2_20261116_run'/r['file']) as im: a=E.reduce(im)
    rk,f=E.ranks(a,M); d=E._class_dists(rk,f,O,refs)
    own=d[spec['classes'].index(l)]; oth=min(d[i] for i,c in enumerate(spec['classes']) if c!=l)
    if own>0.05 or oth<0.12: print(f'{t:6.1f} {l:7} own {own:.3f} nearest-other {oth:.3f}', np.round(d,3))
