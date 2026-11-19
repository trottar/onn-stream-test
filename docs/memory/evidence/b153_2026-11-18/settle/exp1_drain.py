# Stand-in for the audio capture's stop: real ffmpeg 7.1, lavfi silence paced at the real rate (-re) in place of the
# pulse monitor, s16le 48 kHz stereo to a pipe. A reader drains the pipe like _linux_reader_loop; at "stop" it quits
# after its next read (stop event), then SIGTERM, wait <= 2 s, SIGKILL -- today's order. Variant B: SIGKILL at once.
import subprocess, threading, time, os, sys, random, json
mode = sys.argv[1]; n = int(sys.argv[2])
cmd = ["ffmpeg","-hide_banner","-loglevel","warning","-nostdin","-re","-f","lavfi","-i","anullsrc=r=48000:cl=stereo",
       "-ac","2","-ar","48000","-c:a","pcm_s16le","-f","s16le","pipe:1"]
res = []
for i in range(n):
    p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
    stop = threading.Event()
    def rd():
        fd = p.stdout.fileno()
        while True:
            c = os.read(fd, 16384)
            if not c: break
    t = threading.Thread(target=rd, daemon=True); t.start()
    time.sleep(1.0 + random.random())
    t0 = time.monotonic(); stop.set()
    if mode == "today":
        p.terminate()
        try: p.wait(timeout=2); killed = False
        except subprocess.TimeoutExpired: p.kill(); p.wait(); killed = True
    else:
        p.kill(); p.wait(); killed = None
    dt = time.monotonic() - t0
    p.stdout.close(); t.join(1.0)
    res.append([round(dt*1000), killed])
print(json.dumps({"mode": mode, "n": n, "ms": [r[0] for r in res], "sigkill_after_2s": sum(1 for r in res if r[1])}))
