#!/bin/bash
# LINK-L2 -- the day's six holds on the 40 MHz link, one per local 4-hour block, 4 h apart, at the same
# local :40 slots as LINK-L1, adaptive bitrate switched to shadow per session. Derived from LINK-L1's
# link_l1_day.sh. Each hold is one invocation of link_l2_hold.sh (C5-M4A's hold + the disable after PLAYING
# + LINK-L1's 30-min cold start), RUNS=runs (shared index.txt and t2_samples.jsonl). Beside each hold:
# link_l2_air.py snapshot (before launch) and a 30 s loop; between holds (start + 2 h, or after the hold if
# later): one snapshot. A hold with no index line is retried at most twice, 5 min apart, inside its block
# (launch before start + 3 h). A hold that ran but is EXCLUDED by link_l2_valid.py (the controller acted, or
# shadow not confirmed) is re-run ONCE as H<k>r, inside its block; that re-run counts against the same
# two-retry limit. Everything is read-only on the Opal.
# usage: link_l2_day.sh <H1 start epoch> [first hold number=1]
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
RUNS="$HERE/runs"; mkdir -p "$RUNS"
AIR="$HERE/air.jsonl"
T1="${1:?usage: link_l2_day.sh <H1 start epoch> [first]}"; FIRST="${2:-1}"
log() { echo "[day $(date -u +%Y-%m-%dT%H:%M:%SZ) / $(date +%H:%M%Z)] $*" | tee -a "$HERE/day.log"; }
wait_until() { while [ "$(date +%s)" -lt "$1" ]; do sleep 20; done; }
run_hold() {  # $1 = hold name, $2 = try label
  { echo "# $1 try $2 at $(date -u +%Y-%m-%dT%H:%M:%SZ)"; timedatectl; } >> "$RUNS/clock_$1.txt"
  python3 "$HERE/link_l2_air.py" snapshot "$AIR" "${1}_start"
  python3 "$HERE/link_l2_air.py" loop "$HERE/air_loop.jsonl" "$1" 30 &
  local ALOOP=$!
  log "$1 try $2 begins (local hour $(date +%H))"
  COLD_MIN=30 "$HERE/link_l2_hold.sh" "$RUNS" "$1" 1200 > "$RUNS/hold_$1_try$2.log" 2>&1
  log "$1 try $2 hold exit $?"
  touch "$HERE/air_loop.jsonl.stop"; wait "$ALOOP"
}

log "LINK-L2 day driver; H1 at $(date -d @"$T1" '+%Y-%m-%d %H:%M %Z'); first hold H$FIRST"
for k in $(seq "$FIRST" 6); do
  START=$(( T1 + (k - 1) * 14400 ))
  BLOCK_END=$(( START + 3 * 3600 ))
  wait_until "$START"
  NAME="H$k"; tries=0; rerun=0
  while :; do
    if grep -q "^$NAME H " "$RUNS/index.txt" 2>/dev/null; then
      V=$(python3 "$HERE/link_l2_valid.py" "$RUNS" "$NAME"); VRC=$?
      log "validity: $V"
      echo "$V" >> "$RUNS/validity.txt"
      [ "$VRC" = "0" ] && break
      if [ "$rerun" = "0" ] && [ "$tries" -lt 2 ] && [ "$(date +%s)" -lt "$BLOCK_END" ]; then
        rerun=1; tries=$((tries + 1)); echo "$NAME EXCLUDED" >> "$RUNS/index.txt"; NAME="H${k}r"
        log "H$k excluded; one re-run as $NAME (try $tries of 2)"
        run_hold "$NAME" "$tries"; continue
      fi
      echo "$NAME EXCLUDED" >> "$RUNS/index.txt"; log "$NAME excluded; no re-run left"; break
    fi
    if [ "$tries" -ge 1 ] || [ -f "$RUNS/hold_${NAME}_try0.log" ]; then
      if [ "$tries" -ge 2 ] || [ "$(date +%s)" -ge "$BLOCK_END" ]; then log "$NAME: NOT RUN after $tries retries"; echo "$NAME NOT_RUN" >> "$RUNS/index.txt"; break; fi
      tries=$((tries + 1)); log "$NAME: no index line; retry $tries of 2 in 5 min"; sleep 300
      run_hold "$NAME" "$tries"; continue
    fi
    run_hold "$NAME" 0
  done
  if [ "$k" -lt 6 ]; then
    wait_until $(( START + 7200 ))
    python3 "$HERE/link_l2_air.py" snapshot "$AIR" "between_H${k}_H$((k+1))"
    log "air snapshot between_H${k}_H$((k+1))"
  fi
done
python3 "$HERE/link_l2_air.py" snapshot "$AIR" after_H6
rm -f /tmp/link_l2_air_prev_set /tmp/link_l2_air_salt /tmp/link_l2_onn_endpoint
log "day done"
