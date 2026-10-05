#!/bin/bash
# C5-M5B -- C5-M5's c5_m5_hold.sh (copied) with two changes: PRIVYHUB_PS1_LOOK is among the session flags
# the teardown unsets; the adopted PS1 files (the seven .opt and Beetle PSX HW.cfg) are checked against
# adopted_ps1_sha256.txt at the start and at the teardown ("ADOPTED PS1 FILES BYTE-IDENTICAL").
# C5-M5 -- C5-M4A's c5_m4a_hold.sh (copied from evidence/c5_m4a_2026-10-01/) with these changes: the hold's
# name, duration, SESSION_FLAGS and HOLD_HOOK come from the caller; the flags are set in the user manager
# (set-environment) before the run (which restarts the unit) and UNSET on every exit path by the
# teardown (unset-environment, restart), which then checks the manager carries no PRIVYHUB_* and the
# environ exactly the live default; the cold start is LINK-L1's (COLD_MIN minutes after the last
# session_ended, default 0). The hold runs through c5_m5_run.sh. C5-M4A's header follows.
# C5-M4A V5 -- one 20-min attract hold of Tekken 3 on the adopted 7000 stream carrying the ADOPTED 4x PS1 source
# (the core override + the 4x line are the real config now). Derived from C5-M4's c5_m4_table.sh (the D1
# pattern): no selector, no source files written; the only measurement file is the counter-only game override
# (c5_m4a_counter.sh), set before the hold and cleared on every exit path. T2 sampler at 10 s.
# usage: SESSION_FLAGS="..." HOLD_HOOK=<script> c5_m5_hold.sh <runs dir> <name> [hold_s=1200]
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO=/home/privyhub/Projects/onn-stream-test
OUT="$1"; mkdir -p "$OUT"
NAME="${2:?name}"
HOLD_S="${3:-1200}"
FLAG_NAMES="PRIVYHUB_ADAPTIVE_BITRATE_INJECT PRIVYHUB_ADAPTIVE_BITRATE_TOP PRIVYHUB_PS1_LOOK"
EXPECT_SHA=de072762e55122c3060086f6f10b1bff54633d9165d0c475f17699127841835e
UNIT=privyhub-companion
SAMP="$OUT/t2_samples.jsonl"
log() { echo "[table $(date -u +%H:%M:%SZ)] $*"; }
cd "$REPO" || exit 1
ps1_files() {
  if (cd "$HOME/.config/retroarch/config/Beetle PSX HW" && sha256sum -c --quiet "$HERE/adopted_ps1_sha256.txt") >/dev/null 2>&1; then
    log "$1: ADOPTED PS1 FILES BYTE-IDENTICAL (8 of 8)"
  else
    log "$1: ADOPTED PS1 FILES CHANGED: $(cd "$HOME/.config/retroarch/config/Beetle PSX HW" && sha256sum -c "$HERE/adopted_ps1_sha256.txt" 2>&1 | grep -v ': OK$' | tr '\n' ';')"
  fi
}
restart_unit() {
  systemctl --user restart "$UNIT"
  for i in $(seq 1 30); do ss -lnt 2>/dev/null | grep -q ':8765 ' && break; sleep 1; done; sleep 2
}
env_line() {
  local MP; MP=$(systemctl --user show -p MainPID --value "$UNIT")
  log "$1: manager PRIVYHUB_* '$(systemctl --user show-environment | grep '^PRIVYHUB_' | tr '\n' ' ' | sed 's/ $//')'; MainPID $MP; 8765 $(ss -lntp | grep ':8765 ' | grep -oP 'pid=\K[0-9]+'); environ PRIVYHUB_* '$(tr '\0' '\n' < /proc/$MP/environ | grep '^PRIVYHUB_' | tr '\n' ' ' | sed 's/ $//')'"
  curl -s localhost:8765/plugins/games/native-stream-status | python3 -c "import sys,json;d=json.load(sys.stdin);a=d['adaptive_bitrate'];o=d['encoder_overrides'];print('[table] adaptive_bitrate mode',a.get('mode'),'configured',a.get('configured_mode'),'acts',a.get('acts'),'| bitrate',d.get('bitrate_kbps'),'profile',d.get('profile_id'),d.get('width'),d.get('height'),'any_override',o.get('any_override'),'profile_id_override',o.get('profile_id_override'),'fec_scheme_override',o.get('fec_scheme_override'),'active',d.get('active'))"
}
stop_game() {
  curl -s -X POST localhost:8765/plugins/games/stop >/dev/null
  for i in $(seq 1 20); do
    sleep 1
    A=$(curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print(json.load(sys.stdin)['active'])" 2>/dev/null)
    [ "$A" = "False" ] && break
  done
}
teardown() {
  touch "$SAMP.stop"
  "$HERE/c5_m4a_counter.sh" clear
  systemctl --user unset-environment PRIVYHUB_NATIVE_PROFILE_ID PRIVYHUB_FEC_SCHEME $FLAG_NAMES
  stop_game
  restart_unit
  env_line "teardown"
  MP=$(systemctl --user show -p MainPID --value "$UNIT")
  if [ "$(systemctl --user show-environment | grep -c '^PRIVYHUB_')" = 0 ] \
     && [ "$(tr '\0' '\n' < /proc/$MP/environ | grep '^PRIVYHUB_' | tr '\n' ' ' | sed 's/ $//')" = "PRIVYHUB_ADAPTIVE_BITRATE_MODE=live" ]; then
    log "FLAGS UNSET AND ABSENT: manager none, environ exactly the live default"
  else
    log "FLAGS NOT CLEAN after teardown"
  fi
  curl -s localhost:8765/plugins/games/native-stream-status | python3 -c "import sys,json;d=json.load(sys.stdin);print('[table] teardown stream',d.get('bitrate_kbps'),d.get('width'),d.get('height'),'level size',(d.get('adaptive_bitrate') or {}).get('level_size'))"
  ps1_files "teardown"
  log "measurement files: $(ls "$HOME/.config/retroarch/config/Beetle PSX HW" | grep -c '^Tekken 3') (want 0)"
  P=$(adb shell pm path com.safeiot.privyhub | tr -d '\r' | sed 's/^package://')
  DEV=$(adb shell sha256sum "$P" 2>/dev/null | awk '{print $1}')
  if [ "$DEV" = "$EXPECT_SHA" ]; then log "ADOPTED APK CONFIRMED (device hash $DEV)"; else log "APK MISMATCH: device $DEV"; fi
  adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
  sleep 6
  adb shell uiautomator dump /sdcard/c5m4end.xml >/dev/null 2>&1
  NP=$(adb shell cat /sdcard/c5m4end.xml 2>/dev/null | grep -c 'NOW PLAYING')
  log "teardown: game active $A; NOW PLAYING on the launcher: $NP"
  if [ "$A" = "False" ] && [ "${NP:-0}" != "0" ]; then
    adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1; sleep 1
    adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1; sleep 7
    adb shell uiautomator dump /sdcard/c5m4end.xml >/dev/null 2>&1
    log "stale banner: force-stop + relaunch; NOW PLAYING now: $(adb shell cat /sdcard/c5m4end.xml 2>/dev/null | grep -c 'NOW PLAYING')"
  fi
  adb shell rm -f /sdcard/c5m4end.xml /sdcard/s1chk.xml >/dev/null 2>&1
}
[ "$(systemctl --user show-environment | grep -c '^PRIVYHUB_')" = 0 ] || { log "FAILED: PRIVYHUB_* already in the manager"; exit 1; }
trap 'teardown; log "table done"' EXIT
ps1_files "start"
systemctl --user cat "$UNIT" | grep -q '^Environment=PRIVYHUB_ADAPTIVE_BITRATE_MODE=live$' || { log "FAILED: no live drop-in"; exit 1; }
adb devices | awk 'NR>1 && $2=="device"' | grep -q . || { log "adb unavailable: NOT RUN"; exit 1; }
LAST=$(grep '"session_ended"' "$REPO/logs/games/native_stream_recovery.log" | tail -1 \
       | python3 -c "import sys,json;print(json.loads(sys.stdin.read())['at_utc'])")
READY=$(python3 -c "
from datetime import datetime,timedelta,timezone
t=datetime.strptime('$LAST'[:19],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)+timedelta(minutes=int('${COLD_MIN:-0}'))
print(int(t.timestamp()))")
log "last session_ended $LAST; $NAME not before $(date -u -d @$READY +%H:%M:%SZ)"
while [ "$(date +%s)" -lt "$READY" ]; do sleep 20; done
for kv in ${SESSION_FLAGS:-}; do systemctl --user set-environment "$kv"; done
log "session flags set in the manager: '$(systemctl --user show-environment | grep '^PRIVYHUB_' | sort | tr '\n' ' ' | sed 's/ $//')'"
env_line "start"
rm -f "$SAMP.stop"
nohup python3 "$HERE/t2_sample.py" "$SAMP" 10 >> "$OUT/t2_sampler.log" 2>&1 &
log "T2 sampler started (10 s); one hold, ${HOLD_S}s"
"$HERE/c5_m4a_counter.sh" set
adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
log "$NAME begins (adopted 7000, the 4x PS1 source, flags '${SESSION_FLAGS:-}', hook '${HOLD_HOOK:-none}')"
ARM_PROFILE= SESSION_FLAGS="${SESSION_FLAGS:-}" HOLD_HOOK="${HOLD_HOOK:-}" "$HERE/c5_m5_run.sh" "$NAME" H "$HOLD_S" "$OUT"; log "$NAME exit $?"
