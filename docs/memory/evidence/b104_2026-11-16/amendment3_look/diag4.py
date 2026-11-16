import sys, json, numpy as np
sys.path.insert(0,'tools'); import h7_endscreen as E
from PIL import Image
FR=E.Path('runtime/h7_frames'); V1L=json.loads((FR/'t88/labels.json').read_text()); LL=json.loads((FR/'h7v2_20261116_run/labels.json').read_text())
def red(ps):
    out=[]
    for p in ps:
        with Image.open(p) as im: out.append(E.reduce(im))
    return np.stack(out)
spec,arr,_=E.learn(FR/'t88',V1L); M=arr['screen_mask']; O=arr['outcome_mask']
v1={c:red(ps[::4]) for c,ps in E.labelled_frames(FR/'t88',V1L).items() if c!='other'}
lv={c:red(ps[3:-4]) for c,ps in E.labelled_frames(FR,LL).items() if c!='other'}
ys,xs=np.nonzero(O)
R={}
for nm,src in (('v1',v1),('lv',lv)):
    for c,st in src.items(): R[nm,c]=np.stack([E.ranks(a,M)[0] for a in st])[:,O]
for c in ('start','end_P1','end_P2'):
    sysd=np.abs(R['v1',c].mean(0)-R['lv',c].mean(0))
    print(c,'|v1 mean - live mean| per px: median',np.round(np.median(sysd),3),'p90',np.round(np.percentile(sysd,90),3),
      ' live std median',np.round(np.median(R['lv',c].std(0)),3),'p90',np.round(np.percentile(R['lv',c].std(0),90),3))
d=np.abs(R['v1','start'].mean(0)-R['v1','end_P1'].mean(0)); print('v1 start-endP1 diff median',np.round(np.median(d),3))
d=np.abs(R['lv','start'].mean(0)-R['lv','end_P1'].mean(0)); print('live start-endP1 diff median',np.round(np.median(d),3))
# raw: are live frames aligned? compare edges: correlate v1 start mean grey vs live start mean grey with shifts
a=np.stack([x for x in v1['start']]).mean(0); b=np.stack([x for x in lv['start']]).mean(0)
best=[]
for dy in range(-3,4):
  for dx in range(-3,4):
    bb=np.roll(np.roll(b,dy,0),dx,1)[5:-5,5:-5]; aa=a[5:-5,5:-5]
    best.append((np.corrcoef(aa.ravel(),bb.ravel())[0,1],dx,dy))
print('best shift corr',sorted(best)[-3:])
# live start, per-pixel rank std map at tally bbox rows
st=np.stack([E.ranks(x,M)[0] for x in lv['start']]).std(0)
print('live start std in tally bbox rows 84-92, cols 63-108 (x4 step):'); print(np.round(st[82:94,63:109:3],2))
