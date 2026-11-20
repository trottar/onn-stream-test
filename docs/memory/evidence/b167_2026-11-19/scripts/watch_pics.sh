#!/bin/sh
# B167's diagnosis only: copy the scratch's pictures (made by the real capture) to a private folder off the repo once
# learn has made them (made_from.json), and the extra endings' runs. usage: watch_pics.sh <add_game title folder> <out> <s>
H="$1"; O="$2"; END=$(( $(date +%s) + $3 ))
while [ "$(date +%s)" -lt "$END" ]; do
  for d in "$H"/rehearse_*/home/*/pictures; do
    if [ -f "$d/made_from.json" ] && [ ! -d "$O/pictures" ]; then cp -a "$d" "$O/pictures"; fi
  done
  for d in "$H"/rehearse_*/extra/*; do
    [ -f "$d/index.csv" ] && [ ! -d "$O/extra/$(basename "$d")" ] && { mkdir -p "$O/extra"; sleep 1; cp -a "$d" "$O/extra/"; }
  done
  sleep 0.2
done
