import numpy as np
d=np.load('/tmp/b_explore/reduced.npz')
def zz(a,m):
    v=a[m]; s=v.std(); return (a-v.mean())/max(s,1e-3)
scr=np.concatenate([d['v1_start'],d['v1_end_P1'],d['v1_end_P2']])
m=np.ones(scr[0].shape,bool)
for _ in range(3):
    Z=np.stack([zz(a,m) for a in scr]); m=Z.std(axis=0)<0.1
ref=np.stack([zz(a,m) for a in scr]).mean(axis=0)
def sd(a): return float(np.median(np.abs(zz(a,m)[m]-ref[m])))
T={'id':lambda a:a,'+30':lambda a:np.clip(a+30,0,255),'-30':lambda a:np.clip(a-30,0,255),'g0.8':lambda a:np.clip(a*.8,0,255),'g1.2':lambda a:np.clip(a*1.2,0,255),
   'gam0.8':lambda a:255*(a/255)**0.8,'gam1.25':lambda a:255*(a/255)**1.25,'g1.2+30':lambda a:np.clip(a*1.2+30,0,255),'g0.8-30':lambda a:np.clip(a*.8-30,0,255),
   'gam1.25-30':lambda a:np.clip(255*(a/255)**1.25-30,0,255),'gam0.8+30':lambda a:np.clip(255*(a/255)**0.8+30,0,255)}
for k,f in T.items():
    s=[sd(f(a)) for key in ('live_start','live_end_P1','live_end_P2') for a in d[key]]
    o=[sd(f(a)) for key in ('live_other','v1_other') for a in d[key]]
    print(f'{k:11} live screens max {max(s):.3f} p95 {np.percentile(s,95):.3f}  others min {min(o):.3f}')
