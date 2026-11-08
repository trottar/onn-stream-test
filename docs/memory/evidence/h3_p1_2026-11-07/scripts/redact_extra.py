import os,re,sys
root=sys.argv[1]
P={}
for ln in open(os.path.expanduser('~/Projects/onn-stream-test/runtime/h3_p1_paths.txt')):
    if '=' in ln: k,v=ln.rstrip('\n').split('=',1); P[k]=v
generic={'usa','chd','iso','the','and','v1','01','v1.01','ntsc','pal'}
words=set()
for k in ('T1','T2'):
    stem=os.path.splitext(P[k])[0]
    words|={w.lower() for w in re.findall(r'[A-Za-z]{3,}',stem) if w.lower() not in generic}
vals=[P['BIOS_DIR'],P['GAMES_DIR'],P['T1'],P['T2'],os.path.basename(P['BIOS_DIR'].rstrip('/')),os.path.splitext(P['T1'])[0],os.path.splitext(P['T2'])[0]]
ip=re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
bad=0
for dp,_,fs in os.walk(root):
    for f in sorted(fs):
        p=os.path.join(dp,f); t=open(p,errors='replace').read(); low=t.lower()
        hits=[]
        if any(v and v in t for v in vals): hits.append('a paths-file value')
        wh=[w for w in words if re.search(r'\b'+re.escape(w)+r'\b',low)]
        if wh: hits.append(f'{len(wh)} title word(s)')
        if ip.search(t): hits.append('an IPv4-like string')
        if re.search(r'/mnt/|/media/',t): hits.append('a mount path')
        print(('HIT  ' if hits else 'OK   ')+os.path.relpath(p,root)+('  ('+', '.join(hits)+')' if hits else ''))
        bad+=bool(hits)
print('files with hits:',bad)
