#!/bin/bash
# C5-M5B -- the PS1 look on the TV, one command per look (for the user's hand, in an SSH window).
#
#   tools/ps1_look.sh 4x               the adopted config (4x internal resolution), 720p stream
#   tools/ps1_look.sh remaster         the "remaster" preset (only if offered: see TOOLS.md), 720p stream
#   tools/ps1_look.sh remaster-1080p   the "remaster" preset at the 1080p rung (entry injected)
#   THE DEFAULT (the plain route, the one the user's looks of 2026-10-04/05 used): start a PS1 game on the TV
#   as usual once the helper says so (a title WITHOUT its own per-title core options: the six multitap titles
#   keep their own file, so the look does not apply to them).
#   add --attract to have the helper start the attract title (Tekken 3) and open the stream on the onn itself
#   (C5-CLOSE: the hold harness's route -- a fresh launcher, its NOW PLAYING preview, RESUME PLAYING; if the
#   stream does not open, the helper says exactly what to press on the TV and waits).
#
# What it does: sets the session flags in the user manager (PRIVYHUB_PS1_LOOK=<preset>; for -1080p also
# PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p and PRIVYHUB_ADAPTIVE_BITRATE_INJECT=1), restarts the companion through
# its unit, waits for PLAYING, for -1080p injects the rung's entry and confirms 1920x1080 in the status, prints
# what to look at and waits for Enter. On Enter (or Ctrl-C) it ends the session, unsets every flag, restarts
# the companion and verifies the adopted state: flags absent, live, 7000 at 1280x720, the PS1 .opt / .cfg
# hashes unchanged. Kill switch at any time: Ctrl-C (the same teardown runs).
#
# Every line it prints is also appended to logs/games/ps1_look_helper.log (PS1_LOOK_LOG), UTC-stamped.
#
# Test hooks (tools/test_ps1_look_helper.py fake-runs it): PS1_LOOK_PROC (default /proc), PS1_LOOK_OPT_DIR,
# PS1_LOOK_WAIT_S (PLAYING wait, default 600), PS1_LOOK_SETTLE_S (seconds at PLAYING before the -1080p entry,
# default 90), PS1_LOOK_STEP_S (poll step, default 2), PS1_LOOK_OPEN_S (--attract: seconds for the launcher
# to draw, default 7), PS1_LOOK_LOG, PS1_LOOK_TEST_OFFERED / PS1_LOOK_TEST_AT_RUNG (the
# offered presets, read from companion/games/ps1_look.py when unset); systemctl / curl / adb come from PATH.
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
UNIT=privyhub-companion
API=localhost:8765
TITLE=game_ps1_b0a5986638f61a11
APP=com.safeiot.privyhub
FLAGS="PRIVYHUB_PS1_LOOK PRIVYHUB_ADAPTIVE_BITRATE_TOP PRIVYHUB_ADAPTIVE_BITRATE_INJECT"
PROC="${PS1_LOOK_PROC:-/proc}"
OPT_DIR="${PS1_LOOK_OPT_DIR:-$HOME/.config/retroarch/config/Beetle PSX HW}"
WAIT_S="${PS1_LOOK_WAIT_S:-600}"; SETTLE_S="${PS1_LOOK_SETTLE_S:-90}"; STEP="${PS1_LOOK_STEP_S:-2}"
OPEN_S="${PS1_LOOK_OPEN_S:-7}"
LOG="${PS1_LOOK_LOG:-$REPO/logs/games/ps1_look_helper.log}"
mkdir -p "$(dirname "$LOG")" 2>/dev/null
say() { echo "[ps1_look] $*"; echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG" 2>/dev/null; }
LOOK="${1:-}"; ATTRACT=0; [ "${2:-}" = "--attract" ] && ATTRACT=1
say "---- tools/ps1_look.sh ${*:-}"
case "$LOOK" in
  4x) PRESET=4x; RUNG=0 ;;
  remaster) PRESET=remaster; RUNG=0 ;;
  remaster-1080p) PRESET=remaster; RUNG=1 ;;
  *) echo "usage: tools/ps1_look.sh 4x|remaster|remaster-1080p [--attract]"; exit 2 ;;
esac
OFFERED=${PS1_LOOK_TEST_OFFERED:-$(cd "$REPO/companion" && python3 -c "from games import ps1_look; print(' '.join(sorted(ps1_look.PRESETS)))")}
case " $OFFERED " in *" $PRESET "*) ;; *) say "the preset '$PRESET' is not offered (offered: $OFFERED); nothing changed"; exit 3 ;; esac
AT_RUNG=${PS1_LOOK_TEST_AT_RUNG:-$(cd "$REPO/companion" && python3 -c "from games import ps1_look; print(int(ps1_look.REMASTER_AT_RUNG_OFFERED))")}
if [ "$RUNG" = 1 ] && [ "$AT_RUNG" != 1 ]; then
  say "remaster-1080p is not offered (the full preset did not hold 60 at the rung); nothing changed"; exit 3
fi
[ "$(systemctl --user show-environment | grep -c '^PRIVYHUB_')" = 0 ] \
  || { say "a PRIVYHUB_* flag is already set in the user manager; nothing changed"; systemctl --user show-environment | grep '^PRIVYHUB_'; exit 4; }

opt_hashes() { (cd "$OPT_DIR" && sha256sum ./*.opt ./*.cfg 2>/dev/null) | sort -k2; }
status_json() { curl -s "$API/plugins/games/native-stream-status"; }
playing() { curl -s "$API/plugins/games/status" | python3 -c "import sys,json;print((json.load(sys.stdin).get('recovery') or {}).get('state'))" 2>/dev/null; }
game_active() { curl -s "$API/plugins/games/status" | python3 -c "import sys,json;print(json.load(sys.stdin).get('active'))" 2>/dev/null; }
# C5-CLOSE: --attract opens the stream the way the hold harness does (c5_m5_run.sh). The launcher must be
# drawn AFTER the game is active: an already-open launcher does not refresh on `am start`, so it shows no
# NOW PLAYING (the user's first attempt, 2026-10-04 22:28 local: the launch went through and the TV made no
# request in 2.7 min). So: force-stop the app (no stream is open yet), wake, start it, find the NOW PLAYING
# preview in a uiautomator dump, tap its centre (RESUME PLAYING), confirm NativeStreamActivity; two attempts.
open_stream() {
  local attempt XML XY TOP
  for attempt in 1 2; do
    adb shell am force-stop "$APP" > /dev/null 2>&1
    adb shell input keyevent KEYCODE_WAKEUP > /dev/null 2>&1
    adb shell am start -n "$APP/.MainActivity" > /dev/null 2>&1
    sleep "$OPEN_S"
    adb shell uiautomator dump /sdcard/ps1_look.xml > /dev/null 2>&1
    XML=$(adb shell cat /sdcard/ps1_look.xml 2>/dev/null)
    if ! grep -q now_playing_preview_host <<< "$XML"; then
      say "attract: attempt $attempt -- no NOW PLAYING preview on the launcher"; continue
    fi
    XY=$(python3 -c "
import re, sys
m = re.search(r'now_playing_preview_host[^>]*?bounds=\"\[(\d+),(\d+)\]\[(\d+),(\d+)\]', sys.stdin.read())
print('%d %d' % ((int(m[1]) + int(m[3])) // 2, (int(m[2]) + int(m[4])) // 2) if m else '1008 298')" <<< "$XML")
    adb shell input tap $XY > /dev/null 2>&1
    sleep $(( OPEN_S < 3 ? OPEN_S : 3 ))
    TOP=$(adb shell dumpsys activity activities 2>/dev/null | grep -m1 topResumedActivity)
    case "$TOP" in
      *NativeStreamActivity*) adb shell rm -f /sdcard/ps1_look.xml > /dev/null 2>&1
                              say "attract: RESUME PLAYING tapped ($XY); the stream is open on the TV"; return 0 ;;
    esac
    say "attract: attempt $attempt -- RESUME PLAYING tapped ($XY), the stream did not open"
  done
  adb shell rm -f /sdcard/ps1_look.xml > /dev/null 2>&1
  return 1
}
restart() {
  systemctl --user restart "$UNIT"
  for _ in $(seq 1 30); do curl -s -o /dev/null "$API/plugins/games/status" && break; sleep 1; done
}
environ() { local MP; MP=$(systemctl --user show -p MainPID --value "$UNIT"); tr '\0' '\n' < "$PROC/$MP/environ" 2>/dev/null | grep '^PRIVYHUB_' | sort | tr '\n' ' ' | sed 's/ $//'; }

BEFORE=$(opt_hashes)
TORN=0; OPENED=0
teardown() {
  [ "$TORN" = 1 ] && return; TORN=1
  echo; say "ending the session and restoring the adopted state..."
  # --attract opened the stream: BACK first, as on the TV (it posts the decoder report and stops the stream).
  if [ "$OPENED" = 1 ]; then adb shell input keyevent KEYCODE_BACK > /dev/null 2>&1; sleep "$STEP"; fi
  curl -s -X POST "$API/plugins/games/stop" > /dev/null
  systemctl --user unset-environment $FLAGS
  restart
  local MGR ENV ST AFTER ok=1
  MGR=$(systemctl --user show-environment | grep -c '^PRIVYHUB_')
  ENV=$(environ)
  ST=$(status_json | python3 -c "import sys,json;d=json.load(sys.stdin);a=d.get('adaptive_bitrate') or {};print(a.get('mode'),d.get('bitrate_kbps'),'%sx%s'%(d.get('width'),d.get('height')),(d.get('encoder_overrides') or {}).get('any_override'))" 2>/dev/null)
  AFTER=$(opt_hashes)
  # --attract: the launcher keeps a stale NOW PLAYING bar after the stop (seen on the dry pass, and cleared at
  # every hold-harness teardown the same way): the stream is closed, so force-stop and start it fresh.
  if [ "$OPENED" = 1 ]; then
    adb shell am force-stop "$APP" > /dev/null 2>&1
    adb shell am start -n "$APP/.MainActivity" > /dev/null 2>&1
    say "launcher restarted (no stale NOW PLAYING)"
  fi
  say "manager PRIVYHUB_*: $MGR (want 0)"; [ "$MGR" = 0 ] || ok=0
  say "companion environ: '$ENV' (want PRIVYHUB_ADAPTIVE_BITRATE_MODE=live)"; [ "$ENV" = "PRIVYHUB_ADAPTIVE_BITRATE_MODE=live" ] || ok=0
  say "stream: mode / kbps / size / any_override = $ST (want live 7000 1280x720 False)"; [ "$ST" = "live 7000 1280x720 False" ] || ok=0
  if [ "$BEFORE" = "$AFTER" ]; then say "PS1 .opt / .cfg hashes unchanged ($(echo "$AFTER" | grep -c .) files)"; else say "PS1 .opt / .cfg hashes CHANGED"; ok=0; fi
  if [ "$ok" = 1 ]; then say "ADOPTED STATE VERIFIED"; else say "ADOPTED STATE NOT VERIFIED -- see the lines above"; fi
}
trap 'teardown; exit 130' INT TERM

if [ "$PRESET" != 4x ]; then systemctl --user set-environment "PRIVYHUB_PS1_LOOK=$PRESET"; fi
if [ "$RUNG" = 1 ]; then
  systemctl --user set-environment PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p PRIVYHUB_ADAPTIVE_BITRATE_INJECT=1
fi
say "flags for this look: '$(systemctl --user show-environment | grep '^PRIVYHUB_' | tr '\n' ' ' | sed 's/ $//')' (none for 4x)"
restart
say "companion restarted; its environ: '$(environ)'"

if [ "$ATTRACT" = 1 ]; then
  curl -s -X POST "$API/plugins/games/launch?id=$TITLE" > /dev/null
  T=0
  until [ "$(game_active)" = True ]; do
    sleep "$STEP"; T=$((T + STEP)); [ "$T" -ge 30 ] && break
  done
  say "the attract title is launched (game active: $(game_active)); opening the stream on the TV..."
  if open_stream; then
    OPENED=1
  else
    say "the stream did not open by itself. ON THE TV, with the remote: press HOME, open PrivyHub, then select"
    say "RESUME PLAYING in the NOW PLAYING bar at the top of its home screen (or GAMES -> Tekken 3 -> Resume)."
    say "If PrivyHub was already open, press BACK until it closes and open it again so NOW PLAYING appears."
  fi
else
  say "start a PS1 game on the TV as usual (Tekken 3 is the reference title)"
fi
say "waiting for PLAYING (up to ${WAIT_S}s)..."
T=0
until [ "$(playing)" = PLAYING ]; do
  sleep "$STEP"; T=$((T + STEP))
  [ "$T" -ge "$WAIT_S" ] && { say "PLAYING not reached"; teardown; exit 5; }
done
say "PLAYING"

if [ "$RUNG" = 1 ]; then
  say "settling ${SETTLE_S}s at 720p before the 1080p entry (the session-age guard and the blackout)"
  sleep "$SETTLE_S"
  curl -s -X POST "$API/plugins/games/adaptive-bitrate/inject?class=INCREASE_1080P" > /dev/null
  SIZE=
  for _ in $(seq 1 10); do
    sleep "$STEP"
    SIZE=$(status_json | python3 -c "import sys,json;d=json.load(sys.stdin);print('%sx%s'%(d.get('width'),d.get('height')))" 2>/dev/null)
    [ "$SIZE" = 1920x1080 ] && break
  done
  if [ "$SIZE" = 1920x1080 ]; then say "the stream is at the 1080p rung: 12,600 kbps, 1920x1080"
  else say "the rung was NOT reached (status reads $SIZE); the look below is at 720p"; fi
fi

cat <<TXT

  What to look at (${LOOK}):
   - edges: the outlines of the fighters and the stage against the background (stair-steps / shimmer);
   - textures up close: faces, clothes, the floor -- blocky texels (nearest) or smoothed by the filter;
   - the dither pattern in gradients: skies and shaded walls -- a fine checkerboard (dithered) or smooth
     steps / banding (dither off);
   - polygon wobble: textures swimming and vertices jittering as the camera moves (PGXP reduces it);
TXT
[ "$RUNG" = 1 ] && echo "   - at 1080p: the IDR pulse every 250 ms in flat areas (a 4-per-second shimmer or blockiness on flat colours)."
cat <<TXT

  Tell Claude what you saw, in your own words. Nothing you see is a gate.

TXT
read -r -p "[ps1_look] press Enter to end this look and restore the adopted state " _ || true
teardown
