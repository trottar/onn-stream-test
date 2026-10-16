#!/usr/bin/env python3
"""E3: the adopted state (since G-A1, seven: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2; the list is e1_suite.ADOPTED) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
import sys, json, importlib.util
spec=importlib.util.spec_from_file_location('s','/home/privyhub/Projects/onn-stream-test/tools/e1_suite.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
mp=m.mainpid()
d={"at_utc":m.utc(),"preflight":m.preflight(),"ps1_files_identical":m.ps1_files_identical(),"apk":"CONFIRMED" if m.apk_hash()==m.EXPECT_APK else "MISMATCH","retroarch":len(m.retroarch_pids()),"encoder":len(m.encoder_pids()),"mainpid_serves_8765":mp==m.serving_pid()}
d["ok"]=d["preflight"]["ok"] and d["ps1_files_identical"] and d["apk"]=="CONFIRMED" and not d["preflight"]["game_active"] and d["retroarch"]==0 and d["encoder"]==0
print(json.dumps(d))
