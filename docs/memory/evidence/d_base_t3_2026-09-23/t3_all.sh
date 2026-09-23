#!/bin/bash
# D-BASE-T3: one cold 25-minute session with every end sampled.
#   onn   P5's p5_socket_sample.py at 2 s (p9_run.sh SAMPLER=on): the audio
#         (48101) and video (48100) rows of /proc/net/udp{,6}, rx_queue, drops
#   host  t3_host_sample.py at 2 s: sender sent/errors/underflows, kernel UDP
#         SndbufErrors, eno1, sender-thread CPU, encoder CPU
#   heat  t2_sample.py at 10 s (onn cpu-thermal, Opal SoC, host temps)
# p9_run.sh and t2_sample.py copied byte-for-byte; 12/17 from the profile.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO=/home/privyhub/Projects/onn-stream-test
OUT="$HERE/runs"; mkdir -p "$OUT"
log() { echo "[t3 $(date -u +%H:%M:%SZ)] $*"; }
LAST=$(grep '"session_ended"' "$REPO/logs/games/native_stream_recovery.log" | tail -1 \
       | python3 -c "import sys,json;print(json.loads(sys.stdin.read())['at_utc'])")
AGE=$(python3 -c "
from datetime import datetime,timezone
t=datetime.strptime('$LAST'[:19],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
print(int((datetime.now(timezone.utc)-t).total_seconds()//60))")
log "last session_ended $LAST, $AGE min ago"
[ "$AGE" -ge 40 ] || { log "FAILED precondition: < 40 min idle"; exit 1; }
echo "cold_start_last_session_ended $LAST age_min $AGE" >> "$OUT/index.txt"
rm -f "$HERE"/t2_samples.jsonl.stop "$HERE"/t3_host.jsonl.stop
nohup python3 "$HERE/t2_sample.py" "$HERE/t2_samples.jsonl" 10 > "$HERE/t2_sampler.log" 2>&1 &
nohup python3 "$HERE/t3_host_sample.py" "$HERE/t3_host.jsonl" 2 > "$HERE/t3_host_sampler.log" 2>&1 &
trap 'touch "$HERE/t2_samples.jsonl.stop" "$HERE/t3_host.jsonl.stop"' EXIT
sleep 30
SAMPLER=on "$HERE/p9_run.sh" T3 "${HOLD:-1500}" "$OUT"
sleep 40
touch "$HERE/t2_samples.jsonl.stop" "$HERE/t3_host.jsonl.stop"; sleep 12
log "rows: thermal $(wc -l < "$HERE/t2_samples.jsonl"), host $(wc -l < "$HERE/t3_host.jsonl"), onn socket $(wc -l < "$OUT/socket_T3.jsonl")"
MP=$(systemctl --user show -p MainPID --value privyhub-companion)
log "MainPID $MP; 8765 $(ss -lntp | grep ':8765 ' | grep -oP 'pid=\K[0-9]+'); PRIVYHUB_* environ $(tr '\0' '\n' < /proc/$MP/environ | grep -c PRIVYHUB_) manager $(systemctl --user show-environment | grep -c PRIVYHUB_)"
curl -s localhost:8765/plugins/games/native-stream-status | python3 -c "import sys,json;d=json.load(sys.stdin);c=d['audio_cushion'];print('[t3] cushion',c['queue_target_packets'],c['queue_capacity_packets'],c['source'],'any_override',d['encoder_overrides']['any_override'])"
log done
