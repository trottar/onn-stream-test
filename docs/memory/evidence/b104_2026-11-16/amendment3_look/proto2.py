exec(open('/home/privyhub/.cache/b_q26an_tmp/proto.py').read().split("for SEP,OWNQ")[0])
F=merge(C['v1'],C['m1'],C['m2'])
L=learn(F,3,98)
src={'v1':C['v1'],'m1':C['m1'],'m2':C['m2']}
for s,fr in src.items():
    for c in ('start','end_P1','end_P2'):
        if not fr.get(c): continue
        D=np.stack([E._class_dists(*E.ranks(a,L['M']),L['O'],L['refs']) for a in fr[c]])
        print(s,c,len(D),'to refs',L['screens'],'median',np.round(np.median(D,0),3),'max',np.round(D.max(0),3),'min',np.round(D.min(0),3))
O=L['O']; ys,xs=np.nonzero(O); print('O bbox',xs.min(),ys.min(),xs.max(),ys.max(), 'left half px',(xs<86).sum(),'right',(xs>=86).sum())
i=2
own=np.concatenate([np.stack([E._class_dists(*E.ranks(a,L['M']),L['O'],L['refs']) for a in fr['end_P2']])[:,2] for fr in src.values() if fr.get('end_P2')])
print('end_P2 own p98',np.percentile(own,98),'max',own.max(), 'n',len(own), 'sorted top', np.round(np.sort(own)[-8:],3))
