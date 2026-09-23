#!/bin/bash
# H2 check 5: after a second reboot with nothing attached but the dummy plug,
# re-run check 2's items and write them to check5_postboot.txt. Read-only
# except for starting the companion (per TOOLS.md) and, with --session, one
# 120 s attract-mode session through h2_session.sh as S2.
#
# usage (from SSH, after the reboot):
#   ONN=<onn-address> ./h2_check5.sh [--session]
# The address is taken from the environment only and never written: every
# dotted quad in the output is replaced before it reaches the file.
set -u
REPO=/home/privyhub/Projects/onn-stream-test
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/check5_postboot.txt"
export DISPLAY=:0
red() { sed -E 's/[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(:[0-9]+)?/<redacted>/g'; }

{
echo "===== when ====="
date -u +%Y-%m-%dT%H:%M:%SZ; uptime
journalctl --list-boots --no-pager 2>/dev/null | tail -3 | awk '{print $1, $3, $4, $5, $6}'

echo "===== session (must be x11 / lightdm-autologin / active, not the greeter) ====="
for s in $(loginctl list-sessions --no-legend | awk '{print $1}'); do
  echo "--- session $s"; loginctl show-session "$s" -p Type -p Service -p State -p Display -p Desktop
done
ps -eo pid,cmd | grep -E "[l]ightdm-gtk-greeter|[x]fce4-session|[l]ight-locker" | awk '{print $2}' | sort | uniq -c

echo "===== display (must be DisplayPort-1 1920x1080 60.00*+) ====="
xrandr 2>&1 | grep -E "connected|\*"
for c in /sys/class/drm/card0-DP-*; do echo "$(basename "$c") $(cat "$c/status")"; done
xset q 2>&1 | grep -E "DPMS is|timeout:"

echo "===== adb ====="
adb start-server >/dev/null 2>&1
if [ -n "${ONN:-}" ]; then echo "cmd: adb connect <onn-address>:5555"; adb connect "$ONN:5555" 2>&1 | red; sleep 2; fi
adb devices 2>&1 | red

echo "===== companion ====="
cd "$REPO"
EXIST=$(ps -eo pid,cmd | awk '/[p]ython3 \.\/companion\/privyhub_service\.py/{print $1}')
if [ -z "$EXIST" ] && ! ss -lnt | grep -q ':8765 '; then
  DISPLAY=:0 nohup python3 ./companion/privyhub_service.py > logs/companion_h2_check5.log 2>&1 &
  sleep 6
fi
COMP=$(ps -eo pid,cmd | awk '/[p]ython3 \.\/companion\/privyhub_service\.py/{print $1}' | head -1)
echo "companion pid ${COMP:-none} (pre-existing: ${EXIST:-no})"
[ -n "$COMP" ] && tr '\0' '\n' < "/proc/$COMP/environ" | grep -E "^DISPLAY="
ss -lntp 2>/dev/null | grep 8765 | awk '{print $1, $4, $6}'
curl -s localhost:8765/plugins/games/native-stream-status | python3 -c "
import sys, json
d = json.load(sys.stdin); eo = d.get('encoder_overrides', {})
print('capture_backend', d.get('capture_backend'))
print('max_frame_size_bytes', eo.get('max_frame_size_bytes'), 'source', eo.get('max_frame_size_source'), 'any_override', eo.get('any_override'))
" 2>&1

echo "===== tmux ====="
tmux ls 2>&1
} 2>&1 | red > "$OUT"
cat "$OUT"

if [ "${1:-}" = "--session" ]; then
  "$HERE/h2_session.sh" S2 120
  python3 "$HERE/h2_analyze.py" > "$HERE/h2_analysis.txt" 2>&1
  grep -A8 "B2 range vs H2" "$HERE/h2_analysis.txt"
fi
