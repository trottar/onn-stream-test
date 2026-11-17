#!/usr/bin/env python3
"""B133 settle 1 (made-up windows only, on the hub's display; no stream, no game): a full-screen window A (red — the
board's shape: Tk's -fullscreen, as Godot's --fullscreen) and a window B (blue) opened above it — (a) 960 x 720 at
(960, 384) (T89's shape), (b) full screen (T88's shape). Window A grabbed by its id with the stream's own grab
arguments (`ffmpeg -f x11grab -framerate 60 -draw_mouse 0 -window_id <A> -i <display>`, one frame), and the screen
at B's place grabbed as the watcher does (Pillow's X11 grab). Only each grab's mean colour is printed; nothing is
kept (the frames go to a scratch folder off the repo). usage: cover_probe.py <scratch dir>"""
import json, os, subprocess, sys, time, tkinter as tk
from PIL import Image, ImageGrab, ImageStat
D = os.environ.get("DISPLAY") or ":0"
S = sys.argv[1]
def mean(img, box=None):
    im = img.convert("RGB") if box is None else img.convert("RGB").crop(box)
    return [round(v) for v in ImageStat.Stat(im).mean]
def grab_by_id(wid, name):
    out = os.path.join(S, name + ".png")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "x11grab", "-framerate", "60",
                        "-draw_mouse", "0", "-window_id", str(wid), "-i", D, "-frames:v", "1", "-y", out],
                       capture_output=True, text=True, timeout=20)
    if r.returncode != 0:
        return {"error": r.stderr.strip()[-200:]}
    with Image.open(out) as im:
        return {"size": list(im.size), "mean_rgb": mean(im)}
def xid(title):
    r = subprocess.run(["xdotool", "search", "--name", title], capture_output=True, text=True, timeout=5)
    return [int(x) for x in r.stdout.split()]
root = tk.Tk(); root.title("b133_probe_A"); root.configure(bg="#ff0000"); root.attributes("-fullscreen", True)
root.update(); time.sleep(1.5); root.update()
res = {"A_ids": len(xid("b133_probe_A"))}
a = xid("b133_probe_A")[-1]
res["A_alone"] = grab_by_id(a, "a_alone")
for case, geo, full in (("B_window_960x720", "960x720+960+384", False), ("B_fullscreen", None, True)):
    b = tk.Toplevel(root); b.title("b133_probe_B"); b.configure(bg="#0000ff")
    if full:
        b.attributes("-fullscreen", True)
    else:
        b.geometry(geo)
    b.lift(); b.focus_force()
    for _ in range(15):
        root.update(); time.sleep(0.1)
    scr = ImageGrab.grab(xdisplay=D)
    box = (980, 420, 1900, 1060)
    res[case] = {"A_by_id": grab_by_id(a, "a_" + case), "screen_at_B": mean(scr, box), "screen_left_top": mean(scr, (20, 300, 500, 700))}
    b.destroy()
    for _ in range(5):
        root.update(); time.sleep(0.1)
root.destroy()
print(json.dumps(res))
