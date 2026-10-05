#!/bin/bash
# C5-CLOSE section 1 -- the short injection check's plan, run by c5_m5_run.sh at PLAYING (TOP=1080p and INJECT=1 for
# this session only): read native-stream-status at +20 s and +60 s and record the rung window's rule field
# (`window_rule`), the skipped count (`skipped_not_playing`) and the window; no class injected (no injected class
# exercises report counting; the rule's field is what is checked). usage: c5_close_inj_hook.sh <scratch> <arm>
set -u
S="$1"; A="$2"; B=localhost:8765
st() { curl -s "$B/plugins/games/native-stream-status" > "$S/close_status_${A}_$1.json"; python3 -c "
import json;d=json.load(open('$S/close_status_${A}_$1.json'));a=d.get('adaptive_bitrate') or {};p=a.get('policy') or {};r=p.get('rung_1080p') or {}
print('[$A] status $1: bitrate',d.get('bitrate_kbps'),'size',d.get('width'),'x',d.get('height'),'| mode',a.get('mode'),'inject',a.get('inject_enabled'),'ladder',a.get('validated_ladder_kbps'),'| rung window',r.get('window'),'| window_rule',repr(r.get('window_rule')),'| skipped_not_playing',r.get('skipped_not_playing'),'| any_override',(d.get('encoder_overrides') or {}).get('any_override'))"; }
sleep 20; st p20
sleep 40; st p60
