#!/bin/bash
# H3: after installing the unit (and after a reboot), from an SSH shell:
# the unit state, the companion pid and its DISPLAY, the 8765 listener,
# native-stream-status, tmux. Writes h3_verify_<UTC time>.txt beside itself;
# every dotted quad is replaced before it reaches the file.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/h3_verify_$(date -u +%Y%m%dT%H%M%SZ).txt"
red() { sed -E 's/[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(:[0-9]+)?/<redacted>/g'; }
{
echo "===== when"; date -u +%Y-%m-%dT%H:%M:%SZ; uptime
echo "===== unit"
echo "enabled: $(systemctl --user is-enabled privyhub-companion.service 2>&1)"
echo "active:  $(systemctl --user is-active privyhub-companion.service 2>&1)"
systemctl --user show privyhub-companion.service -p MainPID -p NRestarts -p ActiveEnterTimestamp -p ExecMainStatus 2>&1
echo "===== companion process"
PIDS=$(ps -eo pid,comm,args --no-headers | awk '$2=="python3" && /privyhub_service\.py/ {print $1}')
echo "companion pids: ${PIDS:-none} (exactly one expected)"
for p in $PIDS; do tr '\0' '\n' < "/proc/$p/environ" | grep -E '^(DISPLAY|PRIVYHUB_[A-Z_]*)=' | sed "s/^/  pid $p: /"; done
echo "===== listener"
ss -lntp 2>/dev/null | grep ':8765 ' | awk '{print $1, $4, $6}'
echo "===== native-stream-status"
curl -s -m 5 localhost:8765/plugins/games/native-stream-status | python3 -c "
import sys, json
d = json.load(sys.stdin); eo = d.get('encoder_overrides', {})
print('ready', d.get('ready'), '| capture_backend', d.get('capture_backend'))
print('max_frame_size_bytes', eo.get('max_frame_size_bytes'), 'source', eo.get('max_frame_size_source'), 'any_override', eo.get('any_override'))
" 2>&1
echo "===== journal (last 8 lines)"
journalctl --user -u privyhub-companion.service -n 8 --no-pager 2>&1
echo "===== tmux"
tmux ls 2>&1
} 2>&1 | red > "$OUT"
cat "$OUT"
