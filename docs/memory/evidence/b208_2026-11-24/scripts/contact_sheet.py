import sys
from pathlib import Path
from PIL import Image, ImageDraw
d = Path(sys.argv[1]); outp = sys.argv[2]
fs = sorted(p for p in d.glob("end_*.png"))
ims = [Image.open(p).convert("RGB") for p in fs]
W = max(i.size[0] for i in ims) + 160; H = sum(i.size[1] + 6 for i in ims)
s = Image.new("RGB", (W, H), (0, 0, 0)); dr = ImageDraw.Draw(s); y = 0
for p, i in zip(fs, ims):
    s.paste(i, (160, y)); dr.text((4, y + 10), p.stem, fill=(255, 255, 255)); y += i.size[1] + 6
s.save(outp)
