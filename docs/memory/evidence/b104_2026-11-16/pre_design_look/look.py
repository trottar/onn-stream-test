import numpy as np, sys
from PIL import Image
def prof(p):
    a=np.asarray(Image.open(p).convert('L'),dtype=np.float32)
    rows=a.max(axis=1); cols=a.max(axis=0)
    rm=a.mean(axis=1); cm=a.mean(axis=0)
    def ext(v,t):
        idx=np.nonzero(v>t)[0]; return (int(idx[0]),int(idx[-1])) if len(idx) else None
    print(p.split('/')[-2][:8], a.shape, 'max>24 rows',ext(rows,24),'cols',ext(cols,24),'mean>8 rows',ext(rm,8),'cols',ext(cm,8), 'mean',round(a.mean(),1))
for p in sys.argv[1:]: prof(p)
