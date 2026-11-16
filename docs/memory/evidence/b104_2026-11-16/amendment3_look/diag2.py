import sys, json, numpy as np
sys.path.insert(0,'tools'); import h7_endscreen as E
from PIL import Image
FR=E.Path('runtime/h7_frames'); V1L=json.loads((FR/'t88/labels.json').read_text()); LL=json.loads((FR/'h7v2_20261116_run/labels.json').read_text())
def red(ps):
    out=[]
    for p in ps:
        with Image.open(p) as im: out.append(E.reduce(im))
    return out
lv={c:red(ps) for c,ps in E.labelled_frames(FR,LL).items()}
v1={c:red(ps[::2]) for c,ps in E.labelled_frames(FR/'t88',V1L).items()}
orig=E.learn_arrays
import types
src=open('tools/h7_endscreen.py').read()
for out_steady in (0.05,0.08,0.1,0.15):
    # patch: the within test only
    E.learn_arrays.__globals__['STEADY_R']=0.05
    code=src.replace("within = np.stack([rstack[c].std(axis=0) for c in screens]).max(axis=0) < STEADY_R","within = np.stack([rstack[c].std(axis=0) for c in screens]).max(axis=0) < OUT_STEADY")
    ns={}; exec(compile(code,'x','exec'),ns); ns['OUT_STEADY']=out_steady
    for name,F in (('live-only',lv),('v1-only',v1)):
        spec,arr,rep=ns['learn_arrays'](F,1.2)
        print(out_steady,name,'O px',rep['outcome_mask']['px'],'bbox',rep['outcome_mask']['bbox_160x120'],{c:(v['gap'],v['verdict'][:9]) for c,v in rep['classes'].items()},'margin need',rep['margin_needed'])
