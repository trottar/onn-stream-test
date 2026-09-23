#!/bin/bash
# D-BASE-T2 Part 1: one run -- S-a (cold, >= 40 min after the last stream),
# S-b (1 min later), 30 min idle (companion up, nothing streaming), S-c,
# S-d (1 min later). 20-minute holds, adopted profile, 12/17 from the
# PROFILE (no PRIVYHUB_* set: TARGET/CAPACITY unset -> p9_run.sh unsets the
# manager variables before each systemd restart, as P9a restarted per arm).
# t2_sample.py runs across the whole timeline (sessions AND idle), 10 s.
# p9_run.sh is copied byte-for-byte from d_base_p9_2026-09-23/.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO=/home/privyhub/Projects/onn-stream-test
OUT="$HERE/runs"; mkdir -p "$OUT"
SAMP="$HERE/t2_samples.jsonl"
HOLD="${HOLD:-1200}"
log() { echo "[t2 $(date -u +%H:%M:%SZ)] $*"; }

rm -f "$SAMP.stop"
nohup python3 "$HERE/t2_sample.py" "$SAMP" 10 > "$HERE/t2_sampler.log" 2>&1 &
SPID=$!
log "sampler pid $SPID"
trap 'touch "$SAMP.stop"' EXIT

# cold start: >= 40 min since the last session_ended in the recovery log
LAST=$(grep '"session_ended"' "$REPO/logs/games/native_stream_recovery.log" | tail -1 \
       | python3 -c "import sys,json;print(json.loads(sys.stdin.read())['at_utc'])")
READY=$(python3 -c "
from datetime import datetime,timedelta
t=datetime.strptime('$LAST'[:19],'%Y-%m-%dT%H:%M:%S')+timedelta(minutes=41)
print(int((t-datetime(1970,1,1)).total_seconds()))")
log "last session_ended $LAST; S-a not before $(date -u -d @$READY +%H:%M:%SZ)"
while [ "$(date +%s)" -lt "$READY" ]; do sleep 20; done
echo "cold_start_last_session_ended $LAST" >> "$OUT/index.txt"

"$HERE/p9_run.sh" Sa "$HOLD" "$OUT"
"$HERE/p9_run.sh" Sb "$HOLD" "$OUT"
log "idle 1800 s begins (companion up, nothing streaming)"
echo "idle_begin $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT/index.txt"
sleep 1800
echo "idle_end $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT/index.txt"
log "idle ends"
"$HERE/p9_run.sh" Sc "$HOLD" "$OUT"
"$HERE/p9_run.sh" Sd "$HOLD" "$OUT"
sleep 120
touch "$SAMP.stop"; sleep 12
log "sampler rows $(wc -l < "$SAMP")"
MP=$(systemctl --user show -p MainPID --value privyhub-companion)
log "MainPID $MP; 8765 owner $(ss -lntp | grep ':8765 ' | grep -oP 'pid=\K[0-9]+'); PRIVYHUB_* environ $(tr '\0' '\n' < /proc/$MP/environ | grep -c PRIVYHUB_) manager $(systemctl --user show-environment | grep -c PRIVYHUB_)"
curl -s localhost:8765/plugins/games/native-stream-status | python3 -c "import sys,json;d=json.load(sys.stdin);c=d['audio_cushion'];print('[t2] cushion',c['queue_target_packets'],c['queue_capacity_packets'],c['source'],'any_override',d['encoder_overrides']['any_override'])"
curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print('[t2] game active',json.load(sys.stdin)['active'])"
log "done"
