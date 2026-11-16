import numpy as np, csv, json
d=np.load('/tmp/b_explore/reduced.npz')
def zz(a,m):
    v=a[m]; return (a-v.mean())/v.std()
scr=np.concatenate([d['v1_start'],d['v1_end_P1'],d['v1_end_P2']])
m=np.ones(scr[0].shape,bool)
for _ in range(3):
    Z=np.stack([zz(a,m) for a in scr]); m=Z.std(axis=0)<0.1
Z=np.stack([zz(a,m) for a in scr]); ref=Z.mean(axis=0)
lab=json.load(open('runtime/h7_frames/h7v2_20261116_run/labels.json'))['runs']['h7v2_20261116_run']
rows=list(csv.DictReader(open('runtime/h7_frames/h7v2_20261116_run/index.csv')))
from PIL import Image
import sys; sys.path.insert(0,'/tmp/b_explore')
exec(open('/tmp/b_explore/explore.py').read().split("L1=")[0])
for r in rows:
    t=float(r['seconds'])
    l=[x['label'] for x in lab if x['from']-1e-6<=t<=x['to']+1e-6]
    l=l[0] if l else '-'
    a=red('runtime/h7_frames/h7v2_20261116_run/'+r['file'])
    s=float(np.median(np.abs(zz(a,m)[m]-ref[m])))
    if (l in('start','end_P1','end_P2') and s>0.1) or (l=='other' and s<0.6) or l in('-','ignore'):
        print(f'{t:7.2f} {l:7} {s:.3f}')
