#!/bin/bash
# C5-M5B section 4 -- C5-M5's c5_m5_sessions.sh (copied) running ONE named session per call (S2b or S3b) through
# c5_m5b_hold.sh: usage c5_m5b_sessions.sh <name> <dir> <start epoch> <window end epoch> <secs>.
# C5-M5 section 4 -- S3 (the night: one 7200-s attract session starting 01:00-06:00 local) and S2 (a 1800-s
# daytime hold, 09:00-17:00 local), each with PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p for that session only (set by
# c5_m5_hold.sh before the run, unset and checked by its teardown), live by default, T2 on, no injection.
# A session whose hold log has no index line is retried at most twice, 5 min apart, inside its window.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
log() { echo "[sessions $(date -u +%Y-%m-%dT%H:%M:%SZ) / $(date +%H:%M%Z)] $*" | tee -a "$HERE/sessions.log"; }
one() {  # name dir start end secs
  local N="$1" D="$HERE/$2" START="$3" END="$4" SECS="$5"
  mkdir -p "$D"
  while [ "$(date +%s)" -lt "$START" ]; do sleep 20; done
  for try in 0 1 2; do
    if grep -q "^$N H " "$D/index.txt" 2>/dev/null; then break; fi
    if [ "$try" -gt 0 ]; then
      [ "$(date +%s)" -lt "$END" ] || { log "$N: window over; NOT RUN after $try tries"; break; }
      log "$N: no index line; retry $try of 2 in 5 min"; sleep 300
    fi
    { echo "# $N try $try at $(date -u +%Y-%m-%dT%H:%M:%SZ)"; timedatectl; } >> "$D/clock_$N.txt"
    log "$N try $try begins (local hour $(date +%H)), $SECS s"
    SESSION_FLAGS='PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p' COLD_MIN=10 "$HERE/c5_m5b_hold.sh" "$D" "$N" "$SECS" > "$D/hold_${N}_try$try.log" 2>&1
    log "$N try $try exit $?"
  done
  grep -q "^$N H " "$D/index.txt" 2>/dev/null || echo "$N NOT_RUN" >> "$D/index.txt"
}
one "$1" "$2" "$3" "$4" "$5"
log "$1 done"
