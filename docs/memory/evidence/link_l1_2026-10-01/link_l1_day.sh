#!/bin/bash
# LINK-L1 A3 -- the day's six holds, one per local 4-hour block, 4 h apart, adaptive off.
# Each hold is one invocation of CL-B1's night driver (cl_b1_night.sh, byte-identical copy):
# EXPECT_SHA = the adopted APK, COLD_MIN = 30, one hold spec Hk:, RUNS=runs (shared index.txt
# and t2_samples.jsonl). Beside each hold: link_l1_air.py snapshot (before launch) and a 30 s
# loop; between holds (start + 2 h): one snapshot. A hold with no index line after its night is
# retried at most twice, 5 min apart, inside its block. Everything is read-only on the Opal.
# usage: link_l1_day.sh <H1 start epoch> [first hold number=1]
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
RUNS="$HERE/runs"; mkdir -p "$RUNS"
AIR="$HERE/air.jsonl"
EXPECT=de072762e55122c3060086f6f10b1bff54633d9165d0c475f17699127841835e
T1="${1:?usage: link_l1_day.sh <H1 start epoch> [first]}"; FIRST="${2:-1}"
log() { echo "[day $(date -u +%Y-%m-%dT%H:%M:%SZ) / $(date +%H:%M%Z)] $*" | tee -a "$HERE/day.log"; }
wait_until() { while [ "$(date +%s)" -lt "$1" ]; do sleep 20; done; }

log "LINK-L1 day driver; H1 at $(date -d @"$T1" '+%Y-%m-%d %H:%M %Z'); first hold H$FIRST"
[ "$FIRST" = "1" ] && python3 "$HERE/link_l1_air.py" snapshot "$AIR" B0_before_H1 && log "air snapshot B0_before_H1"
for k in $(seq "$FIRST" 6); do
  START=$(( T1 + (k - 1) * 14400 ))
  BLOCK_END=$(( START + 3 * 3600 ))
  wait_until "$START"
  for try in 0 1 2; do
    if grep -q "^H$k H " "$RUNS/index.txt" 2>/dev/null; then break; fi
    if [ "$try" -gt 0 ]; then
      [ "$(date +%s)" -lt "$BLOCK_END" ] || { log "H$k: block over; NOT RUN after $try tries"; break; }
      log "H$k: no index line; retry $try of 2 in 5 min"; sleep 300
    fi
    { echo "# H$k try $try at $(date -u +%Y-%m-%dT%H:%M:%SZ)"; timedatectl; } >> "$RUNS/clock_H$k.txt"
    python3 "$HERE/link_l1_air.py" snapshot "$AIR" "H${k}_start"
    python3 "$HERE/link_l1_air.py" loop "$HERE/air_loop.jsonl" "H$k" 30 &
    ALOOP=$!
    log "H$k try $try begins (local hour $(date +%H))"
    EXPECT_SHA="$EXPECT" COLD_MIN=30 RUNS=runs "$HERE/cl_b1_night.sh" "H$k:" > "$RUNS/night_H${k}_try${try}.log" 2>&1
    log "H$k try $try night exit $?"
    touch "$HERE/air_loop.jsonl.stop"; wait "$ALOOP"
  done
  grep -q "^H$k H " "$RUNS/index.txt" 2>/dev/null || echo "H$k NOT_RUN" >> "$RUNS/index.txt"
  if [ "$k" -lt 6 ]; then
    wait_until $(( START + 7200 ))
    python3 "$HERE/link_l1_air.py" snapshot "$AIR" "between_H${k}_H$((k+1))"
    log "air snapshot between_H${k}_H$((k+1))"
  fi
done
python3 "$HERE/link_l1_air.py" snapshot "$AIR" after_H6
rm -f /tmp/link_l1_air_prev_set /tmp/link_l1_air_salt
log "day done"
