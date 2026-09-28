#!/bin/bash
# CTRL-L1: three plain 20-minute holds -- C (cold, >= 40 min since the last
# session_ended), W1 and W2 (back to back after C) -- the adopted profile
# (no PRIVYHUB_*), zero input, attract mode. p9_run.sh and t2_sample.py are
# the close-out's, byte for byte. Beside them, read-only: t2_sample.py at 10 s
# (host + onn + Opal) and ctrl_l1_host_sample.py at 10 s (the controller
# socket's drops / rx_queue, /proc/net/snmp Udp, softnet, the NIC; status and
# the Opal's /proc/net/dev every 30 s). The onn's /proc/net/snmp Udp line is
# read over adb only BETWEEN holds.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO=/home/privyhub/Projects/onn-stream-test
OUT="$HERE/runs"; mkdir -p "$OUT"
SAMP="$HERE/t2_samples.jsonl"; HOST="$HERE/host_samples.jsonl"
log() { echo "[ctrl $(date -u +%H:%M:%SZ)] $*"; }
[ "$(systemctl --user show-environment | grep -c PRIVYHUB_)" = 0 ] || { log "FAILED: PRIVYHUB_* set in the manager"; exit 1; }
LAST=$(grep '"session_ended"' "$REPO/logs/games/native_stream_recovery.log" | tail -1 \
       | python3 -c "import sys,json;print(json.loads(sys.stdin.read())['at_utc'])")
READY=$(python3 -c "
from datetime import datetime,timedelta,timezone
t=datetime.strptime('$LAST'[:19],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)+timedelta(minutes=41)
print(int(t.timestamp()))")
log "last session_ended $LAST; C not before $(date -u -d @$READY +%H:%M:%SZ)"
echo "cold_start_last_session_ended $LAST" >> "$OUT/index.txt"
rm -f "$SAMP.stop" "$HOST.stop"
nohup python3 "$HERE/t2_sample.py" "$SAMP" 10 > "$HERE/t2_sampler.log" 2>&1 &
nohup python3 "$HERE/ctrl_l1_host_sample.py" "$HOST" 10 > "$HERE/host_sampler.log" 2>&1 &
trap 'touch "$SAMP.stop" "$HOST.stop"' EXIT
while [ "$(date +%s)" -lt "$READY" ]; do sleep 20; done
onn_udp() { echo "$1 $(date -u +%Y-%m-%dT%H:%M:%SZ) $(adb shell cat /proc/net/snmp 2>/dev/null | grep '^Udp:' | tail -1 | tr -d '\r')" >> "$OUT/onn_snmp_udp.txt"; }
for ARM in C W1 W2; do
  onn_udp "before_$ARM"
  "$HERE/p9_run.sh" "$ARM" "${HOLD:-1200}" "$OUT" || log "$ARM: p9_run.sh exited non-zero"
  onn_udp "after_$ARM"
done
sleep 30; touch "$SAMP.stop" "$HOST.stop"; sleep 12
MP=$(systemctl --user show -p MainPID --value privyhub-companion)
log "sampler rows t2 $(wc -l < "$SAMP") host $(wc -l < "$HOST"); MainPID $MP; 8765 $(ss -lntp | grep ':8765 ' | grep -oP 'pid=\K[0-9]+'); PRIVYHUB_* environ $(tr '\0' '\n' < /proc/$MP/environ | grep -c PRIVYHUB_) manager $(systemctl --user show-environment | grep -c PRIVYHUB_)"
curl -s localhost:8765/plugins/games/native-stream-status | python3 -c "import sys,json;d=json.load(sys.stdin);r=d['audio_redundancy'];c=d['audio_cushion'];o=d['encoder_overrides'];print('[ctrl] cap',o['max_frame_size_bytes'],o['max_frame_size_source'],'cushion',c['queue_target_packets'],c['queue_capacity_packets'],c['source'],'redundancy',r['copies'],r['offset_packets'],r['source'],'any_override',o['any_override'],'bitrate',d.get('bitrate_kbps'))"
curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print('[ctrl] game active',json.load(sys.stdin)['active'])"
log done
