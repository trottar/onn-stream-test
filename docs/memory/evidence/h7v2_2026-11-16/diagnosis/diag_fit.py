import sys, json, itertools
sys.path.insert(0, "tools")
import numpy as np, h7_endscreen as H
from PIL import Image
spec, arr = H.load_spec("<the rules folder>/<T88's id>.endscreen.json")
live = Image.open(sys.argv[1]).convert("L")
def rd(img):
    return H.read(spec, arr, img)
print("as-is:", rd(live))
c = live.crop((302, 54, 1619, 1053))
print("content box -> 640x525:", rd(c.resize((640, 525))))
best = None
# map: the content box placed in a 640x525 canvas at (0, top) with height h (width 640)
for h in range(440, 541, 4):
    for top in range(-40, 41, 4):
        cv = Image.new("L", (640, 525))
        cv.paste(c.resize((640, h)), (0, top))
        r = rd(cv); d = r["distances"]["screen"]
        if best is None or d < best[0]:
            best = (d, h, top, r)
print("best vertical fit:", best)
