#!/bin/bash
# D-BASE close-out: C (cold, >= 40 min since the last session_ended) and W
# (1 min after C), 20 min each, the profile as adopted (cap 90,000, cushion
# 12/17, redundancy 2/4, all source: profile, no PRIVYHUB_*), t2_sample.py
# at 10 s throughout. p9_run.sh and t2_sample.py copied byte-for-byte.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO=/home/privyhub/Projects/onn-stream-test
OUT="$HERE/runs"; mkdir -p "$OUT"
SAMP="$HERE/t2_samples.jsonl"
log() { echo "[close $(date -u +%H:%M:%SZ)] $*"; }
[ "$(systemctl --user show-environment | grep -c PRIVYHUB_)" = 0 ] || { log "FAILED: PRIVYHUB_* set in the manager"; exit 1; }
LAST=$(grep '"session_ended"' "$REPO/logs/games/native_stream_recovery.log" | tail -1 \
       | python3 -c "import sys,json;print(json.loads(sys.stdin.read())['at_utc'])")
READY=$(python3 -c "
from datetime import datetime,timedelta,timezone
t=datetime.strptime('$LAST'[:19],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)+timedelta(minutes=41)
print(int(t.timestamp()))")
log "last session_ended $LAST; C not before $(date -u -d @$READY +%H:%M:%SZ)"
echo "cold_start_last_session_ended $LAST" >> "$OUT/index.txt"
rm -f "$SAMP.stop"
nohup python3 "$HERE/t2_sample.py" "$SAMP" 10 > "$HERE/t2_sampler.log" 2>&1 &
trap 'touch "$SAMP.stop"' EXIT
while [ "$(date +%s)" -lt "$READY" ]; do sleep 20; done
"$HERE/p9_run.sh" C "${HOLD:-1200}" "$OUT"
"$HERE/p9_run.sh" W "${HOLD:-1200}" "$OUT"
sleep 30; touch "$SAMP.stop"; sleep 12
MP=$(systemctl --user show -p MainPID --value privyhub-companion)
log "sampler rows $(wc -l < "$SAMP"); MainPID $MP; 8765 $(ss -lntp | grep ':8765 ' | grep -oP 'pid=\K[0-9]+'); PRIVYHUB_* environ $(tr '\0' '\n' < /proc/$MP/environ | grep -c PRIVYHUB_) manager $(systemctl --user show-environment | grep -c PRIVYHUB_)"
curl -s localhost:8765/plugins/games/native-stream-status | python3 -c "import sys,json;d=json.load(sys.stdin);r=d['audio_redundancy'];c=d['audio_cushion'];o=d['encoder_overrides'];print('[close] cap',o['max_frame_size_bytes'],o['max_frame_size_source'],'cushion',c['queue_target_packets'],c['queue_capacity_packets'],c['source'],'redundancy',r['copies'],r['offset_packets'],r['source'],'any_override',o['any_override'])"
curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print('[close] game active',json.load(sys.stdin)['active'])"
log done
