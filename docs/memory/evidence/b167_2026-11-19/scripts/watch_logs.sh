#!/bin/sh
# B167's first run only: copy RetroArch's own log out of the capture's temp folder before the tool removes it.
# The copies stay off the repo (they name the game). usage: watch_logs.sh <temp root> <out dir> <seconds>
T="$1"; O="$2"; END=$(( $(date +%s) + $3 ))
while [ "$(date +%s)" -lt "$END" ]; do
  for f in "$T"/add_game_capture_*/retroarch.log; do
    [ -f "$f" ] && cp "$f" "$O/$(basename "$(dirname "$f")").log" 2>/dev/null
  done
  sleep 0.005
done
