#!/usr/bin/env python3
"""B105: what keep=1 costs — no game, no RetroArch, no display; synthetic pictures only.

1. Per picture: the watcher's own `MiniGame._keep` (the real code: JPEG quality 90 + the index row) on a synthetic
   1920 x 1080 RGB window picture (bars, panels, noise), 60 times: wall ms and CPU ms (process time).
2. A fixture's frames over 60 s: a child process drawing 1920 x 1080 frames with numpy, paced to 60 a second, counts
   the frames it finished; beside it, in this process, the watcher's work once a second through the real modules — a
   B104 `Reader.read` of the picture (a spec learnt here on synthetic tallies) — once without keeping, once with
   `_keep`. The two counts, and the CPU this process used.
Everything written goes to a temp dir removed at the end.

usage: keep_cost.py <repo>
"""
import json
import multiprocessing as mp
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

REPO = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO / "companion"))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tests" / "art_systems"))
sys.path.insert(0, str(REPO / "tests" / "b102_h7_endscreen"))
import h7_endscreen as E  # noqa: E402
import test_b102 as b102  # noqa: E402


def window_picture(rng) -> Image.Image:
    game = b102.screen(1, "10", rng).convert("RGB").resize((1330, 1080), Image.BILINEAR)
    a = np.asarray(game, dtype=np.int16) + rng.integers(-6, 7, size=(1080, 1330, 3))
    canvas = Image.new("RGB", (1920, 1080), (0, 0, 0))
    canvas.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB"), (295, 0))
    ImageDraw.Draw(canvas).rectangle((400, 900, 1500, 1000), fill=(30, 90, 200))
    return canvas


def game_loop(seconds: float, q) -> None:
    """The fixture 'game': 1920 x 1080 frames drawn with numpy, paced to 60 a second."""
    rng = np.random.default_rng(1)
    base = rng.integers(0, 255, size=(1080, 1920), dtype=np.uint8)
    frames, t0 = 0, time.perf_counter()
    nxt = t0
    while time.perf_counter() - t0 < seconds:
        f = np.roll(base, frames % 1920, axis=1)
        f[::8, :] = 255 - f[::8, :]
        frames += 1
        nxt += 1 / 60
        d = nxt - time.perf_counter()
        if d > 0:
            time.sleep(d)
    q.put(frames)


def main() -> None:
    import h7_minigame as M
    tmp = Path(tempfile.mkdtemp(prefix="b105_keep_"))
    try:
        rng = np.random.default_rng(105)
        runs, labels = b102.write_runs(tmp)
        spec, arrays, _ = E.learn(runs, labels)
        pic = window_picture(rng)
        keep_dir = tmp / "keep"
        keep_dir.mkdir()
        (keep_dir / "index.csv").write_text("seconds,utc,file,class,screen,margin,distances,keep_ms\n")
        m = M.MiniGame.__new__(M.MiniGame)
        m._lock = threading.Lock()
        tok = object()
        m._watch = {"token": tok, "state": "watching", "game": "fixture", "_keep_dir": keep_dir,
                    "keep": {"folder": "keep", "pictures": 0}}
        m._row = lambda fields: None
        reader = E.Reader(spec, arrays)
        r = reader.read(pic)
        walls, cpus = [], []
        for i in range(60):
            w0, c0 = time.perf_counter(), time.process_time()
            m._keep(tok, keep_dir, pic, float(i), r)
            walls.append((time.perf_counter() - w0) * 1000)
            cpus.append((time.process_time() - c0) * 1000)
        size = sum(p.stat().st_size for p in keep_dir.glob("*.jpg")) / 60
        print(json.dumps({"per_picture": {"wall_ms_median": round(float(np.median(walls)), 2),
                                          "wall_ms_worst": round(max(walls), 2),
                                          "cpu_ms_median": round(float(np.median(cpus)), 2),
                                          "jpeg_kb": round(size / 1024, 1), "kept": m._watch["keep"]["pictures"],
                                          "read_class": r["class"]}}), flush=True)
        for keep in (False, True, False, True):
            q = mp.Queue()
            g = mp.Process(target=game_loop, args=(60.0, q))
            g.start()
            c0, t0, n = time.process_time(), time.perf_counter(), 0
            while time.perf_counter() - t0 < 60.0:
                rr = reader.read(pic)
                if keep:
                    m._keep(tok, keep_dir, pic, time.perf_counter() - t0, rr)
                n += 1
                time.sleep(max(0.0, t0 + n - time.perf_counter()))
            frames = q.get(timeout=30)
            g.join(timeout=30)
            print(json.dumps({"fixture_60s": {"keep": keep, "game_frames": frames, "watcher_reads": n,
                                              "watcher_cpu_ms": round((time.process_time() - c0) * 1000, 1)}}),
                  flush=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps({"temp_dir_removed": not tmp.exists()}))


if __name__ == "__main__":
    main()
