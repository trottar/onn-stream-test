import re,sys
from pathlib import Path
IP4=re.compile(r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])'); MAC=re.compile(r'\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b')
IP6=re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){4,7}[0-9a-fA-F]{1,4}\b')
for d in sys.argv[1:]:
    for p in sorted(Path(d).rglob('*')):
        if not p.is_file() or p.suffix=='.pyc': continue
        t=p.read_text(errors='replace'); hits=[]
        for name,rx in (('ipv4',IP4),('mac',MAC),('ipv6',IP6)):
            for m in rx.finditer(t):
                s=m.group(0)
                if name=='ipv4' and (s.startswith(('127.0.0.1','0.0.0.0')) or all(int(x)<10 for x in s.split('.')) ): continue
                hits.append(f"{name}@{t[:m.start()].count(chr(10))+1}")
        print(("OK   " if not hits else "HIT  ")+str(p)+("" if not hits else "  "+",".join(hits[:8])))
