import sys, os
sys.path.insert(0, "tools")
import numpy as np, h7_endscreen as H
from PIL import Image
spec, arr = H.load_spec("<the rules folder>/<T88's id>.endscreen.json")
print("arrays:", {k: v.shape for k, v in arr.items()})
mask = arr[[k for k in arr if "screen" in k and "mask" in k][0]].astype(bool)
ref = arr[[k for k in arr if "screen" in k and "ref" in k][0]]
live = Image.open(sys.argv[1]).convert("L")
a = H.reduce(live, spec["aspect"])
d = (a - ref)[mask]
print("live-ref over mask: mean %.1f median %.1f |d| median %.1f" % (d.mean(), np.median(d), np.median(abs(d))))
g, o = np.polyfit(ref[mask], a[mask], 1); print("live ~ %.2f*ref + %.1f" % (g, o))
fit = (a - (g * ref + o))[mask]; print("after gain/offset |d| median %.1f" % np.median(abs(fit)))
tr = sorted(os.listdir("runtime/h7_frames/t88/begin"))[40]
b = H.reduce(Image.open("runtime/h7_frames/t88/begin/" + tr).convert("L"), spec["aspect"])
print("a training begin frame |d| median %.1f" % np.median(abs((b - ref)[mask])))
# row/col profile of mismatch: where is it
D = np.zeros_like(a); D[mask] = abs(a - ref)[mask]
print("mismatch by row band (10 rows):", [round(float(D[i:i+12].sum() / max(1, mask[i:i+12].sum())), 1) for i in range(0, 120, 12)])
print("mismatch by col band:", [round(float(D[:, j:j+16].sum() / max(1, mask[:, j:j+16].sum())), 1) for j in range(0, 160, 16)])
Image.fromarray(np.clip(a, 0, 255).astype("uint8")).resize((640, 480)).save(os.path.expanduser("~/.cache/h7v2_tmp/diag_live_reduced.png"))
Image.fromarray(np.clip(ref, 0, 255).astype("uint8")).resize((640, 480)).save(os.path.expanduser("~/.cache/h7v2_tmp/diag_ref.png"))
