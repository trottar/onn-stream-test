#!/bin/bash
# D-BASE-R3b fault-injection harness.
#
# Authorized by docs/memory/handoffs/D-BASE-R3B_TASK.md. Creates one nftables
# table named `privyhub_fault` on this host, drops the host's own outbound
# stream packets to the client for a bounded interval, then deletes the table.
# The table is removed on every exit path by the trap below, and the script
# deletes any stale copy before it starts.
#
# usage: r3b_run.sh <LABEL> <HOOK output|input> <PORTSET> <FAULT_S> <POST_WAIT_S> [SETTLE_S] [KEEP_RULE]
#   LABEL       run name; artifacts land in <this dir>/<LABEL>/
#   HOOK        output (host -> onn video/audio) or input (onn -> host controller)
#   PORTSET     comma-separated UDP destination ports, e.g. 48100,48101
#   FAULT_S     seconds to hold the fault
#   POST_WAIT_S seconds to observe after the rule is deleted
#   SETTLE_S    seconds of settled play before the fault (default 25)
#   KEEP_RULE   1 leaves the rule in place (E30); default 0 deletes it
set -u
REPO=/home/privyhub/Projects/onn-stream-test
HERE="$(cd "$(dirname "$0")" && pwd)"
LABEL="$1"; HOOK="$2"; PORTS="$3"; FAULT_S="$4"; POST_WAIT="$5"; SETTLE="${6:-25}"; KEEP="${7:-0}"
SESSDIR="$REPO/logs/games/decoder_sessions"
RECLOG="$REPO/logs/games/native_stream_recovery.log"
HBLOG="$REPO/logs/games/native_stream_heartbeat.log"
GAME=game_ps1_b0a5986638f61a11
OUT="$HERE/$LABEL"
mkdir -p "$OUT"

nft_down() { sudo -n /usr/sbin/nft delete table inet privyhub_fault 2>/dev/null; true; }
nft_up() {
  sudo -n /usr/sbin/nft add table inet privyhub_fault || return 1
  sudo -n /usr/sbin/nft add chain inet privyhub_fault flt "{ type filter hook $HOOK priority 0; }" || return 1
  sudo -n /usr/sbin/nft add rule inet privyhub_fault flt udp dport "{$PORTS}" drop || return 1
  return 0
}
trap 'nft_down' EXIT
nft_down

BEFORE=$(ls "$SESSDIR" | wc -l)
REC_OFFSET=$( [ -f "$RECLOG" ] && wc -l < "$RECLOG" || echo 0 )
HB_OFFSET=$( [ -f "$HBLOG" ] && wc -l < "$HBLOG" || echo 0 )

# ---- fresh session -------------------------------------------------------
adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
curl -s -X POST "localhost:8765/plugins/games/stop" >/dev/null
sleep 4
curl -s -X POST "localhost:8765/plugins/games/launch?id=$GAME" >/dev/null

OPENED=0
for attempt in 1 2 3; do
  adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
  adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
  sleep 7
  adb shell uiautomator dump /sdcard/r3bchk.xml >/dev/null 2>&1
  if adb shell cat /sdcard/r3bchk.xml | grep -q "now_playing_preview_host"; then
    adb shell input tap 1008 298
    sleep 3
    TOP=$(adb shell dumpsys activity activities 2>/dev/null | grep -m1 topResumedActivity)
    case "$TOP" in *NativeStreamActivity*) OPENED=1; break;; esac
  fi
done
[ "$OPENED" = "1" ] || { echo "[$LABEL] FAILED to open stream"; exit 1; }

for i in $(seq 1 45); do
  sleep 1
  STATE=$(curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print(json.load(sys.stdin)['recovery']['state'])" 2>/dev/null)
  [ "$STATE" = "PLAYING" ] && break
done
[ "${STATE:-}" = "PLAYING" ] || { echo "[$LABEL] FAILED to reach PLAYING (${STATE:-none})"; exit 1; }

echo "[$LABEL] PLAYING at $(date -u +%H:%M:%S.%3N); settling ${SETTLE}s"
sleep "$SETTLE"

# ---- fault on ------------------------------------------------------------
if ! nft_up; then
  echo "[$LABEL] NFT WRITE REFUSED"
  exit 2
fi
T_ON=$(date -u +%s.%N)
echo "[$LABEL] FAULT ON hook=$HOOK ports=$PORTS at $(date -u -d "@$T_ON" +%H:%M:%S.%3N) for ${FAULT_S}s"
sudo -n /usr/sbin/nft list table inet privyhub_fault > "$OUT/nft_table_active.txt" 2>&1

( END=$(python3 -c "print(int($FAULT_S*2))")
  for i in $(seq 1 "$END"); do
    S=$(curl -s --max-time 1 localhost:8765/plugins/games/status \
        | python3 -c "import sys,json;d=json.load(sys.stdin)['recovery'];print(d['state'],d.get('restarts'))" 2>/dev/null)
    echo "$(date -u +%H:%M:%S.%3N) ${S:-nostatus}"
    sleep 0.5
  done ) > "$OUT/state_during_fault.txt" 2>/dev/null &
POLLER=$!

sleep "$FAULT_S"

if [ "$KEEP" = "1" ]; then
  echo "[$LABEL] FAULT LEFT IN PLACE at $(date -u +%H:%M:%S.%3N)"
  T_OFF=""
else
  sudo -n /usr/sbin/nft delete table inet privyhub_fault
  T_OFF=$(date -u +%s.%N)
  echo "[$LABEL] FAULT OFF at $(date -u -d "@$T_OFF" +%H:%M:%S.%3N)"
fi
wait $POLLER 2>/dev/null

# ---- observe after the clear --------------------------------------------
RESUMED_AT=""
TICKS=$(python3 -c "print(int($POST_WAIT*4))")
for i in $(seq 1 "$TICKS"); do
  S=$(curl -s --max-time 1 localhost:8765/plugins/games/status \
      | python3 -c "import sys,json;d=json.load(sys.stdin)['recovery'];print(d['state'],d.get('restarts'))" 2>/dev/null)
  echo "$(date -u +%H:%M:%S.%3N) ${S:-nostatus}" >> "$OUT/state_after_clear.txt"
  case "${S:-}" in PLAYING*) [ -z "$RESUMED_AT" ] && RESUMED_AT=$(date -u +%s.%N);; esac
  sleep 0.25
done
{ echo "t_on=$T_ON"; echo "t_off=$T_OFF"; echo "t_resumed_poll=$RESUMED_AT"; } > "$OUT/timings.txt"

curl -s localhost:8765/plugins/games/status > "$OUT/status_end.json"

# ---- end the session -----------------------------------------------------
adb shell input keyevent KEYCODE_BACK
for i in $(seq 1 30); do
  sleep 1
  AFTER=$(ls "$SESSDIR" | wc -l)
  if [ "$AFTER" -gt "$BEFORE" ]; then
    NEW=$(ls -t "$SESSDIR" | head -1)
    echo "[$LABEL] report: $NEW"
    cp "$SESSDIR/$NEW" "$OUT/"
    echo "$NEW" > "$OUT/report_name"
    break
  fi
done

tail -n +$((REC_OFFSET+1)) "$RECLOG" 2>/dev/null > "$OUT/recovery_lines.jsonl"
tail -n +$((HB_OFFSET+1)) "$HBLOG" 2>/dev/null > "$OUT/heartbeat_lines.jsonl"
echo "[$LABEL] --- recovery log ---"
python3 -c "
import json
for l in open('$OUT/recovery_lines.jsonl'):
    r=json.loads(l)
    extra={k:v for k,v in r.items() if k not in ('schema','at_utc','event') and v is not None}
    print('   ',r['at_utc'],r['event'],extra if extra else '')
"
nft_down
