#!/bin/bash
# D-BASE-P8: the three arms in order, then the companion restored to its
# defaults (no PRIVYHUB_HEARTBEAT_MS) and confirmed with one status read.
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/runs"; mkdir -p "$OUT"
SAMPLER=on  "$HERE/p8_run.sh" A 1200 "$OUT"
SAMPLER=off "$HERE/p8_run.sh" B 1200 "$OUT"
PRIVYHUB_HEARTBEAT_MS=10000 SAMPLER=off "$HERE/p8_run.sh" C 1200 "$OUT"
# restore: companion without the diagnostic interval
cd /home/privyhub/Projects/onn-stream-test
curl -s -X POST localhost:8765/plugins/games/stop >/dev/null; sleep 4
OLD=$(ps -eo pid,comm,args --no-headers | awk '$2=="python3" && /privyhub_service\.py/ {print $1; exit}')
[ -n "$OLD" ] && kill "$OLD"; sleep 3
env -u PRIVYHUB_HEARTBEAT_MS DISPLAY=:0 nohup python3 ./companion/privyhub_service.py > logs/companion_p8_restored.log 2>&1 &
sleep 6
NEWPID=$(ss -lntp 2>/dev/null | grep ':8765 ' | grep -oP 'pid=\K[0-9]+' | head -1)
echo "[restore] companion $NEWPID; PRIVYHUB_HEARTBEAT_MS in environ: $(tr '\0' '\n' < /proc/$NEWPID/environ | grep -c PRIVYHUB_HEARTBEAT_MS)"
python3 -c "import sys; sys.path.insert(0,'companion'); from plugins.games import GamesPlugin" 2>/dev/null
curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;d=json.load(sys.stdin);print('[restore] status active',d['active'])"
echo "[all] done"
