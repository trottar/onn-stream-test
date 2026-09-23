#!/bin/bash
# D-BASE-P9: A2 (3/8), B (12/17, profile), B' (12/24), then the companion
# restored through systemd with no PRIVYHUB_AUDIO_QUEUE_* in the manager.
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/runs"; mkdir -p "$OUT"
restore() {
  systemctl --user unset-environment PRIVYHUB_AUDIO_QUEUE_TARGET_PACKETS \
    PRIVYHUB_AUDIO_QUEUE_CAPACITY_PACKETS
  curl -s -X POST localhost:8765/plugins/games/stop >/dev/null; sleep 4
  systemctl --user restart privyhub-companion; sleep 6
  MP=$(systemctl --user show -p MainPID --value privyhub-companion)
  echo "[restore] MainPID $MP; 8765 owner $(ss -lntp | grep ':8765 ' | grep -oP 'pid=\K[0-9]+')"
  echo "[restore] PRIVYHUB_* in environ: $(tr '\0' '\n' < /proc/$MP/environ | grep -c PRIVYHUB_)"
  curl -s localhost:8765/plugins/games/native-stream-status | python3 -c "import sys,json;d=json.load(sys.stdin);print('[restore] audio_cushion',d['audio_cushion']['queue_target_packets'],d['audio_cushion']['queue_capacity_packets'],d['audio_cushion']['source'],'any_override',d['encoder_overrides']['any_override'])"
  curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print('[restore] game active',json.load(sys.stdin)['active'])"
}
trap restore EXIT
TARGET=3 CAPACITY=8   "$HERE/p9_run.sh" A2 "${HOLD:-1200}" "$OUT"
                      "$HERE/p9_run.sh" B  "${HOLD:-1200}" "$OUT"
TARGET=12 CAPACITY=24 "$HERE/p9_run.sh" Bp "${HOLD:-1200}" "$OUT"
echo "[all] done"
