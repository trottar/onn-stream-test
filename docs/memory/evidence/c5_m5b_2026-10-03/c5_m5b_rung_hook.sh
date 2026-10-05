#!/bin/bash
# C5-M5B section 5 -- the full look preset at the rung, run by c5_m5_run.sh at PLAYING (PS1_LOOK=measure-full,
# TOP=1080p and INJECT=1 for this session): after 90 s inject INCREASE_1080P (the policy's own entry decision,
# every gate but the window), confirm 1920x1080 in the status, then hold 300 s at the rung. The 1080p window is
# [inject + 10 s, inject + 300 s] (rung_times_<arm>.txt) for the scorer.
# usage: c5_m5b_rung_hook.sh <scratch> <arm>
set -u
S="$1"; A="$2"; B=localhost:8765
log() { echo "[$A hook $(date -u +%H:%M:%S.%3NZ)] $*"; }
st() { curl -s "$B/plugins/games/native-stream-status" > "$S/rung_status_${A}_$1.json"; python3 -c "
import json;d=json.load(open('$S/rung_status_${A}_$1.json'));a=d.get('adaptive_bitrate') or {}
print('[$A] status $1: bitrate',d.get('bitrate_kbps'),'size',d.get('width'),'x',d.get('height'),'| controller level',a.get('level'),a.get('level_size'),'state',a.get('state'),'| any_override',(d.get('encoder_overrides') or {}).get('any_override'))"; }
sleep 90
st pre
T_UP=$(date +%s.%N)
curl -s -X POST "$B/plugins/games/adaptive-bitrate/inject?class=INCREASE_1080P" > "$S/rung_inject_${A}.json"
log "inject INCREASE_1080P -> $(python3 -c "import json;d=json.load(open('$S/rung_inject_${A}.json'));e=(d.get('events') or [{}])[0];print(d.get('ok'),e.get('event'),e.get('from_kbps'),'->',e.get('to_kbps'),e.get('reason'))")"
echo "inject_up_utc $(date -u -d @${T_UP} +%Y-%m-%dT%H:%M:%S.%3NZ)" >> "$S/rung_times_${A}.txt"
sleep 5; st up5
sleep $(python3 -c "import time;print(max(0.0, ${T_UP} + 150 - time.time()))"); st up150
sleep $(python3 -c "import time;print(max(0.0, ${T_UP} + 300 - time.time()))"); st up300
echo "rung_end_utc $(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" >> "$S/rung_times_${A}.txt"
log "hook done"
