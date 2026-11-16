import sys, json, numpy as np, pickle, os
sys.path.insert(0,'tools'); import h7_endscreen as E
from PIL import Image
FR=E.Path('runtime/h7_frames'); V1L=json.loads((FR/'t88/labels.json').read_text()); LL=json.loads((FR/'h7v2_20261116_run/labels.json').read_text())
cache=os.path.expanduser('~/.cache/b_q26an_tmp/red_cache.pkl')
def red(ps):
    out=[]
    for p in ps:
        with Image.open(p) as im: out.append(E.reduce(im))
    return out
def match(n):
    m=LL['matches'][n]; return {'classes':LL['classes'],'runs':{'h7v2_20261116_run':[r for r in LL['runs']['h7v2_20261116_run'] if r['from']>=m['from'] and r['to']<=m['to']]}}
def v1runs(*rs): return {'classes':V1L['classes'],'runs':{r:V1L['runs'][r] for r in rs}}
if os.path.exists(cache): C=pickle.load(open(cache,'rb'))
else:
    C={}
    C['v1']={c:red(ps) for c,ps in E.labelled_frames(FR/'t88',V1L).items()}
    C['m1']={c:red(ps) for c,ps in E.labelled_frames(FR,match('M1')).items()}
    C['m2']={c:red(ps) for c,ps in E.labelled_frames(FR,match('M2')).items()}
    C['v1p1']={c:red(ps) for c,ps in E.labelled_frames(FR/'t88',v1runs('end_p1')).items()}
    C['v1p2']={c:red(ps) for c,ps in E.labelled_frames(FR/'t88',v1runs('end_p2')).items()}
    pickle.dump(C,open(cache,'wb'))
def merge(*ds):
    o={}
    for d in ds:
        for c,v in d.items(): o.setdefault(c,[]).extend(v)
    return {c:v for c,v in o.items() if v}
def learn(srcs, SEP, OWNQ):
    frames=merge(*srcs)
    screens=['start']+sorted(c for c in frames if c not in('other','start'))
    st={c:np.stack(frames[c]) for c in frames}
    M=E._learn_screen_mask(np.concatenate([st[c] for c in screens]))
    rk={c:[E.ranks(a,M) for a in st[c]] for c in frames}
    rs={c:np.stack([r for r,_ in rk[c]]) for c in frames}
    sref=np.concatenate([rs[c] for c in screens]).mean(0)[M]
    spread=np.stack([np.percentile(rs[c],90,axis=0)-np.percentile(rs[c],10,axis=0) for c in screens]).max(0)
    means={c:rs[c].mean(0) for c in screens}
    apart=np.zeros(M.shape)
    for sf in srcs:
        sm={c:np.stack([E.ranks(a,M)[0] for a in sf[c]]).mean(0) for c in screens if sf.get(c)}
        ks=list(sm)
        for i,a in enumerate(ks):
            for b in ks[i+1:]: apart=np.maximum(apart,np.abs(sm[a]-sm[b]))
    O=(apart>E.DIFFER_R)&(apart>SEP*spread)
    refs=np.stack([means[c][O] for c in screens])
    sd=lambda c:[E._screen_dist(r,f,M,sref) for r,f in rk[c]]
    own=[d for c in screens for d in sd(c)]; fo=min(sd('other'))
    ownq=float(max(own)) if OWNQ=='nearest' else float(np.percentile(own,OWNQ)); sthr=ownq+0.5*(fo-ownq) if fo>ownq else None
    dist={c:np.stack([E._class_dists(r,f,O,refs) for r,f in rk[c]]) for c in screens}
    thr={}; margins=[]; global L_unlike; L_unlike={}
    for i,c in enumerate(screens):
        like=dist[c][np.argmin(dist[c],axis=1)==i][:,i] if OWNQ=='nearest' else dist[c][:,i]
        o=float(like.max()) if OWNQ=='nearest' else float(np.percentile(dist[c][:,i],OWNQ)); f=min(float(dist[d][:,i].min()) for d in screens if d!=c)
        L_unlike[c]=int(len(dist[c])-len(like))
        thr[c]=o+0.5*(f-o) if f>o else None
        for dd in dist[c]:
            if np.argmin(dd)==i: margins.append(np.sort(dd)[1]-dd[i])
    need=0.5*float(min(margins) if OWNQ=='nearest' else np.percentile(margins,100-OWNQ)) if margins else None
    return dict(M=M,O=O,sref=sref,refs=refs,screens=screens,sthr=sthr,thr=thr,need=need)
def score(L,frames):
    res={}; other_scr=0
    for c,fs in frames.items():
        cnt={}
        for a in fs:
            r,f=E.ranks(a,L['M']); s=E._screen_dist(r,f,L['M'],L['sref'])
            if L['sthr'] is None or s>L['sthr']: k='other'
            else:
                dd=E._class_dists(r,f,L['O'],L['refs']); o=np.argsort(dd); b=o[0]; cc=L['screens'][b]
                k=cc if (L['thr'][cc] is not None and dd[b]<=L['thr'][cc] and dd[o[1]]-dd[b]>=L['need']) else 'unknown'
            cnt[k]=cnt.get(k,0)+1
            if c=='other' and k!='other': other_scr+=1
        res[c]=cnt
    return res,other_scr
for SEP,OWNQ in ((3,'nearest'),):
    print('=== SEP',SEP,'OWNQ',OWNQ)
    LV=merge(C['m1'],C['m2'])
    for tag,lf,sf in (('1a',[C['v1']],LV),('1b',[LV],C['v1']),('2a',[C['m1'],C['v1p2']],C['m2']),('2b',[C['m2'],C['v1p1']],C['m1']),('3',[C['v1'],LV],merge(C['v1'],LV))):
        sep=SEP if SEP else 0
        if SEP is None:
            pass
        L=learn(lf, sep if SEP else 0, OWNQ) if SEP else None
        if SEP is None:
            # B102-like within std<0.05 rule for comparison
            continue
        r,o=score(L,sf)
        print(tag,'O',int(L['O'].sum()),'thr',{k:(round(v,3) if v else v) for k,v in L['thr'].items()},'sthr',round(L['sthr'],3),'need',round(L['need'],3),'| other_as_screen',o,'|',r,'unlike',L_unlike)
