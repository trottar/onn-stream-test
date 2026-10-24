#!/usr/bin/env python3
"""E3: the adopted state (since G-A3, nine: live, the guide index, Snes9x, recovery v2, the SNES capture fix output_rate, the overlay provider, session identity v2, the Opus audio path, the client's link report; the list and the drop-in checks are e1_suite's ADOPTED / preflight) as one JSON line (preflight -- since E4-S2 also no e4_constraint.conf --, PS1 files, APK, no game / RetroArch / encoder). Read-only."""
import sys, json, importlib.util
spec=importlib.util.spec_from_file_location('s','/home/privyhub/Projects/onn-stream-test/tools/e1_suite.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
mp=m.mainpid()
d={"at_utc":m.utc(),"preflight":m.preflight(),"ps1_files_identical":m.ps1_files_identical(),"apk":"CONFIRMED" if m.apk_hash()==m.EXPECT_APK else "MISMATCH","retroarch":len(m.retroarch_pids()),"encoder":len(m.encoder_pids()),"mainpid_serves_8765":mp==m.serving_pid()}
d["ok"]=d["preflight"]["ok"] and d["ps1_files_identical"] and d["apk"]=="CONFIRMED" and not d["preflight"]["game_active"] and d["retroarch"]==0 and d["encoder"]==0
# B20: the six PRIVYHUB_LINK_RECOVERY implies, as they will act -- only when the service's environ carries it (absent: no key)
if any(x.startswith("PRIVYHUB_LINK_RECOVERY=") for x in d["preflight"]["environ"]):
    sys.path.insert(0,'/home/privyhub/Projects/onn-stream-test/companion'); import link_recovery; d["link_recovery"]=link_recovery.describe(d["preflight"]["environ"])
print(json.dumps(d))
