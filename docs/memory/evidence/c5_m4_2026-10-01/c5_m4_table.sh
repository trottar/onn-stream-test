#!/bin/bash
# C5-M4 section 2 -- the host table. For each scale given (e.g. 1x 2x 4x), in order:
#   a_<s>: c5_m4_hold_a.sh (no stream), b_<s>: c5_m4_run.sh with the adopted profile (7000, live default),
#   c_<s>: c5_m4_run.sh with ARM_PROFILE=native_game_1080p60_c3_80pct_cap90 (the selector for that hold only),
# each HOLD_S (default 300) s, after c5_m4_source.sh set <s> (window 1920x1080, internal resolution <s>).
# After each c hold: the selector unset, the companion restarted, env logged. T2 sampler (10 s) for the run.
# Teardown on EVERY exit path (trap): the measurement source files cleared, selector unset, companion
# restarted, manager none / environ the drop-in's one name / live, stream 7000, game ended, APK confirmed,
# banner cleared. Derived from c3_l4_d1_night.sh (the D1 pattern). usage: c5_m4_table.sh <runs dir> <scale>...
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO=/home/privyhub/Projects/onn-stream-test
OUT="$1"; shift; SCALES=("$@"); mkdir -p "$OUT"
HOLD_S="${HOLD_S:-300}"
C3=native_game_1080p60_c3_80pct_cap90
EXPECT_SHA=de072762e55122c3060086f6f10b1bff54633d9165d0c475f17699127841835e
UNIT=privyhub-companion
SAMP="$OUT/t2_samples.jsonl"
log() { echo "[table $(date -u +%H:%M:%SZ)] $*"; }
cd "$REPO" || exit 1
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
  "$HERE/c5_m4_source.sh" clear
  systemctl --user unset-environment PRIVYHUB_NATIVE_PROFILE_ID PRIVYHUB_FEC_SCHEME
  stop_game
  restart_unit
  env_line "teardown"
  log "measurement source files: $(ls "$HOME/.config/retroarch/config/Beetle PSX HW" | grep -c '^Tekken 3') (want 0)"
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
systemctl --user cat "$UNIT" | grep -q '^Environment=PRIVYHUB_ADAPTIVE_BITRATE_MODE=live$' || { log "FAILED: no live drop-in"; exit 1; }
adb devices | awk 'NR>1 && $2=="device"' | grep -q . || { log "adb unavailable: NOT RUN"; exit 1; }
trap 'teardown; log "table done"' EXIT
env_line "start"
rm -f "$SAMP.stop"
nohup python3 "$HERE/t2_sample.py" "$SAMP" 10 >> "$OUT/t2_sampler.log" 2>&1 &
log "T2 sampler started (10 s); scales: ${SCALES[*]}; hold ${HOLD_S}s"
for S in "${SCALES[@]}"; do
  "$HERE/c5_m4_source.sh" set "$S" || exit 1
  log "a_$S begins (no stream, scale $S)"
  "$HERE/c5_m4_hold_a.sh" "a_$S" "$S" "$HOLD_S" "$OUT"; log "a_$S exit $?"
  sleep 20
  adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  "$HERE/c5_m4_source.sh" set "$S" || exit 1
  log "b_$S begins (adopted 7000, scale $S)"
  ARM_PROFILE= "$HERE/c5_m4_run.sh" "b_$S" H "$HOLD_S" "$OUT"; log "b_$S exit $?"
  adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  "$HERE/c5_m4_source.sh" set "$S" || exit 1
  log "c_$S begins ($C3, scale $S)"
  ARM_PROFILE="$C3" "$HERE/c5_m4_run.sh" "c_$S" H "$HOLD_S" "$OUT"; log "c_$S exit $?"
  systemctl --user unset-environment PRIVYHUB_NATIVE_PROFILE_ID
  stop_game; restart_unit; env_line "after c_$S (selector unset)"
  sleep 20
done
