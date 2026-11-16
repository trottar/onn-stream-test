import sys, json, numpy as np
sys.path.insert(0,'tools'); import h7_endscreen as E
from PIL import Image
FR=E.Path('runtime/h7_frames'); V1L=json.loads((FR/'t88/labels.json').read_text()); LL=json.loads((FR/'h7v2_20261116_run/labels.json').read_text())
def red(ps): 
    out=[]
    for p in ps:
        with Image.open(p) as im: out.append(E.reduce(im))
    return np.stack(out)
v1=E.labelled_frames(FR/'t88',V1L); lv=E.labelled_frames(FR,LL)
spec,arr,_=E.learn(FR/'t88',V1L)
M=arr['screen_mask']; O=arr['outcome_mask']
for name,src in (('v1',v1),('live',lv)):
    for c in ('start','end_P1','end_P2'):
        st=red(src[c][::3]); R=np.stack([E.ranks(a,M)[0] for a in st])
        print(name,c,len(st),'O ranks mean',np.round(R[:,O].mean(),3),'std-within at O: median',np.round(np.median(R[:,O].std(axis=0)),3),'max',np.round(R[:,O].std(axis=0).max(),3), 'whole-grid within std<0.05 share', np.round((R.std(axis=0)<0.05).mean(),3))
print('---')
import csv
rows=list(csv.DictReader(open(FR/'h7v2_20261116_run/index.csv')))
def at(t0,t1): return [FR/'h7v2_20261116_run'/r['file'] for r in rows if t0<=float(r['seconds'])<=t1]
for nm,(a,b) in {'M1 start':(0,48.5),'M2 start':(297,320.5),'M1 end early':(151,200),'M1 end late':(200,267.5)}.items():
    st=red(at(a,b)); R=np.stack([E.ranks(x,M)[0] for x in st])
    print(nm,len(st),'O std-within median',np.round(np.median(R[:,O].std(axis=0)),3),'O mean',np.round(R[:,O].mean(),3),
          'consecutive-frame |diff| at O median',np.round(np.median(np.abs(np.diff(R[:,O],axis=0))),3))
# raw grey std at O in live start (no ranks)
st=red(at(0,48.5)); print('raw grey std at O median',np.round(np.median(st[:,O].std(axis=0)),2),'raw grey mean at O',np.round(st[:,O].mean(),1))
st=red(v1['start'][::3]); print('v1 raw grey std at O median',np.round(np.median(st[:,O].std(axis=0)),2),'mean',np.round(st[:,O].mean(),1))
