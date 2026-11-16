import sys, json, numpy as np, time
sys.path.insert(0,'tools')
import h7_endscreen as E
from PIL import Image
BAR=16; SHARE=0.05
def area(g):
    a=np.asarray(g)
    h,w=a.shape
    c=a.max(axis=0); r=a.max(axis=1)
    def m(v):
        n=len(v); i=0
        while i<n and v[i]<=BAR: i+=1
        j=0
        while j<n and v[n-1-j]<=BAR: j+=1
        return min(i,j)
    mx,my=m(c),m(r)
    if mx>=my and mx>=SHARE*w and mx<w//2: return g.crop((mx,0,w-mx,h))
    if my>mx and my>=SHARE*h and my<h//2: return g.crop((0,my,w,h-my))
    return g
def red(p):
    with Image.open(p) as im: g=im.convert('L')
    return np.asarray(area(g).resize(E.MID,Image.BILINEAR).resize(E.SIZE,Image.BOX),dtype=np.float32)
def z(a,m):
    v=a[m]; s=v.std(); return (a-v.mean())/max(s,1e-6), s
L1=E.load_labels('runtime/h7_frames/t88/labels.json')
P1=E.labelled_frames('runtime/h7_frames/t88',L1)
L2=E.load_labels('runtime/h7_frames/h7v2_20261116_run/labels.json')
P2=E.labelled_frames('runtime/h7_frames',L2)
t=time.time()
F1={c:[red(p) for p in ps] for c,ps in P1.items()}
F2={c:[red(p) for p in ps] for c,ps in P2.items()}
print('reduced',round(time.time()-t,1),{c:len(v) for c,v in F1.items()},{c:len(v) for c,v in F2.items()})
def learn(F, STEADY_Z):
    scr=[a for c in F if c!='other' for a in F[c]]
    m=np.ones(scr[0].shape,bool)
    for it in range(3):
        Z=np.stack([z(a,m)[0] for a in scr]); m=Z.std(axis=0)<STEADY_Z
    Z=np.stack([z(a,m)[0] for a in scr]); ref=Z.mean(axis=0)
    return m,ref
def sd(a,m,ref):
    za,s=z(a,m); return float(np.median(np.abs(za[m]-ref[m]))), s
for SZ in (0.1,0.15):
    m,ref=learn(F1,SZ)
    print('STEADY_Z',SZ,'mask px',int(m.sum()))
    for name,F in (('V1',F1),('live',F2)):
        for c,fs in F.items():
            d=[sd(a,m,ref)[0] for a in fs]
            print(f'  {name:4} {c:7} n={len(d):4} min {min(d):.3f} med {np.median(d):.3f} max {max(d):.3f}')
    print('  std of screens over mask V1', np.median([sd(a,m,ref)[1] for a in F1['start']]), 'live', np.median([sd(a,m,ref)[1] for a in F2['start']]))
np.savez_compressed('/tmp/b_explore/reduced.npz', **{f'v1_{c}':np.stack(v) for c,v in F1.items()}, **{f'live_{c}':np.stack(v) for c,v in F2.items()})
