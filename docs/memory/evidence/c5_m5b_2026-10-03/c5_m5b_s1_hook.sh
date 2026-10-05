#!/bin/bash
# C5-M5B S1b -- C5-M5's S1 hook, copied unchanged: no rung_loss was selected (c5_m5b_selection.txt), so the leave is the kept CAPACITY_MILD.
# C5-M5 S1 -- the injection session's plan, run by c5_m5_run.sh at PLAYING (TOP=1080p and INJECT=1 for this
# session): SurfaceFlinger every 5 s; after 90 s inject INCREASE_1080P (the policy's own entry decision, every
# gate but the window); 140 s after it (>= 63 reports: the blackout and the 60-report hold-down a decrease waits
# after an up) inject CAPACITY_MILD (a synthetic mild bar through every gate) -> the leave; then 60 s more.
# The times file uses R0's names (inject_up_utc / inject_down_utc) so the R0 scorer reads it.
# usage: c5_m5_s1_hook.sh <scratch> <arm>
set -u
S="$1"; A="$2"; B=localhost:8765
log() { echo "[$A hook $(date -u +%H:%M:%S.%3NZ)] $*"; }
SF="$S/sf_series_${A}.txt"; rm -f "$SF.stop"
( while [ ! -f "$SF.stop" ]; do
    L=$(adb shell dumpsys SurfaceFlinger 2>/dev/null | grep 'SurfaceView\[com.safeiot.privyhub' | grep -o 'w/h:[0-9]*x[0-9]*' | sort | uniq -c | tr -s ' ' | tr '\n' ';')
    echo "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ) $L" >> "$SF"; sleep 5
  done ) &
SFPID=$!
st() { curl -s "$B/plugins/games/native-stream-status" > "$S/r0_status_${A}_$1.json"; python3 -c "
import json;d=json.load(open('$S/r0_status_${A}_$1.json'));a=d.get('adaptive_bitrate') or {};p=a.get('policy') or {}
print('[$A] status $1: bitrate',d.get('bitrate_kbps'),'size',d.get('width'),'x',d.get('height'),'| controller level',a.get('level'),a.get('level_size'),'state',a.get('state'),'transitions',a.get('transitions_this_session'),'holds',p.get('hold_down_remaining_reports'),'| any_override',(d.get('encoder_overrides') or {}).get('any_override'))"; }
inj() { curl -s -X POST "$B/plugins/games/adaptive-bitrate/inject?class=$1" > "$S/s1_inject_${A}_$1.json"
  log "inject $1 -> $(python3 -c "import json;d=json.load(open('$S/s1_inject_${A}_$1.json'));e=(d.get('events') or [{}])[0];print(d.get('ok'),e.get('event'),e.get('from_kbps'),'->',e.get('to_kbps'),e.get('reason'),e.get('trigger'))")"; }
sleep 90
st pre
T_UP=$(date +%s.%N); inj INCREASE_1080P; echo "inject_up_utc $(date -u -d @${T_UP} +%Y-%m-%dT%H:%M:%S.%3NZ)" >> "$S/r0_times_${A}.txt"
sleep 3; st up3
sleep 52; st up55
sleep $(python3 -c "import time;print(max(0.0, ${T_UP} + 140 - time.time()))")
st up140
T_DN=$(date +%s.%N); inj CAPACITY_MILD; echo "inject_down_utc $(date -u -d @${T_DN} +%Y-%m-%dT%H:%M:%S.%3NZ)" >> "$S/r0_times_${A}.txt"
sleep 3; st down3
sleep 52; st down55
sleep $(python3 -c "import time;print(max(0.0, ${T_DN} + 60 - time.time()))")
touch "$SF.stop"; wait "$SFPID"; rm -f "$SF.stop"
log "hook done; SurfaceFlinger samples: $(wc -l < "$SF")"
