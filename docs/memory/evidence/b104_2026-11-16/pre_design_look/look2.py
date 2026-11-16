import numpy as np, sys
from PIL import Image
for p in sys.argv[1:]:
    a=np.asarray(Image.open(p).convert('L'),dtype=np.float32)
    r=a.max(axis=1); c=a.max(axis=0)
    print(p[-20:], 'rowmax top10', r[:60:6].astype(int).tolist(), 'bottom', r[-30::3].astype(int).tolist())
    print('   colmax left', c[290:310:2].astype(int).tolist(), 'bar max', int(c[:290].max()) if a.shape[1]>1000 else int(c[:8].max()))
