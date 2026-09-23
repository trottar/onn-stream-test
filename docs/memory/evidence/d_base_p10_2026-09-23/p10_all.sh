#!/bin/bash
# D-BASE-P10: W (off, 12 min, not scored) then A1 off / B1 on / A2 off /
# B2 on, 10 min each, each a minute after the previous; 12/17 from the
# profile; redundancy through the user manager's environment per arm
# (A: PRIVYHUB_AUDIO_REDUNDANCY_COPIES=1, B: =2, offset from the profile, 4);
# t2_sample.py (10 s) across the whole run for the warm state. p9_run.sh and
# t2_sample.py copied byte-for-byte. Restores: no PRIVYHUB_* at the end.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/runs"; mkdir -p "$OUT"
SAMP="$HERE/t2_samples.jsonl"
log() { echo "[p10 $(date -u +%H:%M:%SZ)] $*"; }
onn_c() { tail -3 "$SAMP" | python3 -c "
import sys,json
v=[json.loads(l).get('onn',{}).get('cpu_thermal_c') for l in sys.stdin]
v=[x for x in v if x]; print(round(max(v),1) if v else 0)"; }
restore() {
  touch "$SAMP.stop"
  systemctl --user unset-environment PRIVYHUB_AUDIO_REDUNDANCY_COPIES PRIVYHUB_AUDIO_REDUNDANCY_OFFSET_PACKETS
  curl -s -X POST localhost:8765/plugins/games/stop >/dev/null; sleep 4
  systemctl --user restart privyhub-companion; sleep 6
  MP=$(systemctl --user show -p MainPID --value privyhub-companion)
  log "restore: MainPID $MP; 8765 $(ss -lntp | grep ':8765 ' | grep -oP 'pid=\K[0-9]+'); PRIVYHUB_* environ $(tr '\0' '\n' < /proc/$MP/environ | grep -c PRIVYHUB_) manager $(systemctl --user show-environment | grep -c PRIVYHUB_)"
  curl -s localhost:8765/plugins/games/native-stream-status | python3 -c "import sys,json;d=json.load(sys.stdin);c=d['audio_cushion'];r=d['audio_redundancy'];print('[p10] cushion',c['queue_target_packets'],c['queue_capacity_packets'],c['source'],'redundancy',r['copies'],r['offset_packets'],r['source'],'any_override',d['encoder_overrides']['any_override'])"
}
trap restore EXIT
rm -f "$SAMP.stop"
nohup python3 "$HERE/t2_sample.py" "$SAMP" 10 > "$HERE/t2_sampler.log" 2>&1 &
sleep 25
arm() {  # name copies hold
  systemctl --user set-environment PRIVYHUB_AUDIO_REDUNDANCY_COPIES="$2"
  log "$1 copies=$2 onn cpu before start $(onn_c) C"
  echo "prestart $1 onn_cpu_c $(onn_c)" >> "$OUT/index.txt"
  "$HERE/p9_run.sh" "$1" "$3" "$OUT"
}
arm W 1 720
n=0
while [ "$(python3 -c "print(1 if $(onn_c) >= 67 else 0)")" = 0 ] && [ $n -lt 2 ]; do
  n=$((n+1)); log "onn $(onn_c) C < 67 after warm-up: extending (W$n, 300 s)"
  arm "W$n" 1 300
done
arm A1 1 600
arm B1 2 600
arm A2 1 600
arm B2 2 600
sleep 30
log "sampler rows $(wc -l < "$SAMP")"
log done
