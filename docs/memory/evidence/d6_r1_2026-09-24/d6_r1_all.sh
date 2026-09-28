#!/bin/bash
# D6-R1: three forward and three reverse runs, interleaved; each direction's
# runs >= 5 min apart (fwd at 0, 5, 10 min; rev at 2.5, 7.5, 12.5 min).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
log() { echo "[d6 $(date -u +%H:%M:%SZ)] $*"; }
START=$(date +%s)
at() { while [ "$(date +%s)" -lt $((START + $1)) ]; do sleep 5; done; }
for i in 1 2 3; do
  at $(( (i - 1) * 300 ))
  log "fwd$i"; "$HERE/d6_r1_run.sh" fwd "d6_r1_fwd$i" "$HERE/fwd$i"
  at $(( (i - 1) * 300 + 150 ))
  log "rev$i"; "$HERE/d6_r1_run.sh" rev "d6_r1_rev$i" "$HERE/rev$i"
done
adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
log "stream active: $(curl -s localhost:8765/plugins/games/native-stream-status | python3 -c 'import sys,json;print(json.load(sys.stdin).get("active"))')"
log done
