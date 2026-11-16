import numpy as np
d=np.load('/tmp/b_explore/reduced.npz')
def zstd(v): return (v-v.mean())/max(v.std(),1e-3)
def zrob(v):
    q1,q2,q3=np.percentile(v,[25,50,75]); return (v-q2)/max(q3-q1,1e-3)
def zrank(v):
    o=np.argsort(v,kind='stable'); r=np.empty(len(v)); r[o]=np.arange(len(v))
    # average ties
    u,inv=np.unique(v,return_inverse=True); s=np.bincount(inv,weights=r); c=np.bincount(inv)
    return (s/c)[inv]/len(v)*3.46
scr=np.concatenate([d['v1_start'],d['v1_end_P1'],d['v1_end_P2']])
m=np.ones(scr[0].shape,bool)
for _ in range(3):
    Z=np.stack([zstd(a[m]) if False else (a-a[m].mean())/a[m].std() for a in scr]); m=Z.std(axis=0)<0.1
T={'id':lambda a:a,'-30':lambda a:np.clip(a-30,0,255),'g0.8-30':lambda a:np.clip(a*.8-30,0,255),'gam1.25':lambda a:255*(a/255)**1.25,'gam1.25-30':lambda a:np.clip(255*(a/255)**1.25-30,0,255),'gam0.8+30':lambda a:np.clip(255*(a/255)**0.8+30,0,255)}
for name,f in (('std',zstd),('robust',zrob),('rank',zrank)):
    ref=np.stack([f(np.round(a[m])) for a in scr]).mean(axis=0)
    sd=lambda a: float(np.median(np.abs(f(np.round(a[m]))-ref)))
    v1=[sd(a) for a in scr[::10]]
    print(name,'v1 screens max',round(max(v1),3))
    for k,t in T.items():
        s=[sd(t(a)) for key in ('live_start','live_end_P1','live_end_P2') for a in d[key]]
        o=[sd(t(a)) for key in ('live_other','v1_other') for a in d[key]]
        print(f'   {k:11} screens p95 {np.percentile(s,95):.3f} max {max(s):.3f} others min {min(o):.3f} ratio {min(o)/np.percentile(s,95):.1f}')
