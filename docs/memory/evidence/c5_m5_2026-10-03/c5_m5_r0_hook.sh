#!/bin/bash
# C5-M5 section 1 (R0) -- the hold's injection plan, run by c5_m5_run.sh at PLAYING in place of the sleep:
# SurfaceFlinger's stream SurfaceView buffer sizes every 5 s (counts per size only); after 90 s one raw
# test-only SIZE injection to 1080p (12,600 / 1920x1080), 60 s later one back to 720p (7000 / 1280x720),
# then 60 s more. native-stream-status is saved before, 3 s after and 55 s after each injection.
# usage: c5_m5_r0_hook.sh <scratch> <arm>
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
import json;d=json.load(open('$S/r0_status_${A}_$1.json'));a=d.get('adaptive_bitrate') or {};c=' '.join(d.get('encoder_command') or [])
import re;vf=re.search(r'scale=(\d+):(\d+)',c);br=re.search(r'-b:v (\d+)k',c);mr=re.search(r'-maxrate (\d+)k',c)
print('[$A] status $1: bitrate',d.get('bitrate_kbps'),'size',d.get('width'),'x',d.get('height'),'| argv scale',vf.groups() if vf else None,'b:v',br.group(1) if br else None,'maxrate',mr.group(1) if mr else None,'| controller level',a.get('level'),a.get('level_size'),'state',a.get('state'),'transitions',a.get('transitions_this_session'),'| any_override',(d.get('encoder_overrides') or {}).get('any_override'))"; }
inj() { curl -s -X POST "$B/plugins/games/adaptive-bitrate/inject?class=SIZE&size=$1" > "$S/r0_inject_${A}_$1.json"
  log "inject SIZE $1 -> $(python3 -c "import json;d=json.load(open('$S/r0_inject_${A}_$1.json'));e=(d.get('events') or [{}])[0];print(d.get('ok'),e.get('event'),e.get('from_kbps'),'->',e.get('to_kbps'),e.get('reason'))")"; }
sleep 90
st pre
T_UP=$(date +%s.%N); inj 1080p; echo "inject_up_utc $(date -u -d @${T_UP} +%Y-%m-%dT%H:%M:%S.%3NZ)" >> "$S/r0_times_${A}.txt"
sleep 3; st up3
sleep 52; st up55
sleep $(python3 -c "import time;print(max(0.0, ${T_UP} + 60 - time.time()))")
T_DN=$(date +%s.%N); inj 720p; echo "inject_down_utc $(date -u -d @${T_DN} +%Y-%m-%dT%H:%M:%S.%3NZ)" >> "$S/r0_times_${A}.txt"
sleep 3; st down3
sleep 52; st down55
sleep $(python3 -c "import time;print(max(0.0, ${T_DN} + 60 - time.time()))")
touch "$SF.stop"; wait "$SFPID"; rm -f "$SF.stop"
# the codec's own lines around the switches (redacted later with the rest; nothing else is kept)
adb logcat -d -v threadtime -t 20000 2>/dev/null | grep -iE "CCodec|MediaCodec|c2\.realtek|AvcLowLatency|output format|resolution|crop" \
  | tail -400 > "$S/logcat_codec_${A}.txt"
log "hook done; SurfaceFlinger samples: $(wc -l < "$SF")"
