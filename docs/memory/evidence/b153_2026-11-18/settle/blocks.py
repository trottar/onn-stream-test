import re,sys,json
L=sys.argv[1]; rows=sys.argv[2]
lines=open(L,'rb').read().decode('utf-8','replace').split('\n')[59000:]
blocks=[];cur=None
for ln in lines:
    if ln.startswith('Starting PrivyHub Linux native-video backend'):
        cur={'start':None,'end_time':None,'exit':None};blocks.append(cur);continue
    if cur is None: continue
    m=re.search(r'Duration: N/A, start: ([0-9.]+)',ln)
    if m and cur['start'] is None: cur['start']=float(m.group(1))
    for m in re.finditer(r'time=(\d+):(\d+):([0-9.]+)',ln):
        cur['end_time']=int(m.group(1))*3600+int(m.group(2))*60+float(m.group(3))
    if 'Exiting' in ln or 'exit' in ln.lower() and 'signal' in ln: cur['exit']=ln.strip()[:60]
sw=[json.loads(l) for l in open(rows) if '"minigame_stream"' in l]
for s in sw:
    t1=s['time_unix'];t0=t1-s['seconds']
    # new block: first start after t0
    nb=[b for b in blocks if b['start'] and t0<b['start']<t1+1]
    ob=[b for b in blocks if b['start'] and b['start']<t0]
    o=ob[-1] if ob else None; n=nb[0] if nb else None
    oend=o['start']+o['end_time'] if o and o['end_time'] else None
    print(f"{s['window']:8s} {s['seconds']:.3f}  old_end-t0={oend-t0 if oend else None:+.3f}  new_start-t0={n['start']-t0 if n else float('nan'):+.3f}  t1-new_start={t1-n['start'] if n else float('nan'):+.3f}")

import glob,os,bisect
snaps=sorted(os.stat(p).st_mtime for p in glob.glob('logs/games/audio_timing/audio_pulseaudio_20261118_1[34]*.json'))
print("kind  seconds  t0->audio_stop_done  ->old_video_end  ->new_x11grab_start  ->row(t1)")
for s in sw:
    t1=s['time_unix'];t0=t1-s['seconds']
    n=[b for b in blocks if b['start'] and t0<b['start']<t1+1][0]
    o=[b for b in blocks if b['start'] and b['start']<t0][-1]
    oend=o['start']+o['end_time']; sn=snaps[bisect.bisect_left(snaps,t0)]
    print(f"{'LONG ' if s['seconds']>3 else 'short'} {s['seconds']:.3f}  {1000*(sn-t0):6.0f}  {1000*(oend-sn):6.0f}  {1000*(n['start']-oend):6.0f}  {1000*(t1-n['start']):6.0f}")
