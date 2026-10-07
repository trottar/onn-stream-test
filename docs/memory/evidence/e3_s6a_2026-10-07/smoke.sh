#!/usr/bin/env bash
# E3-S6A smoke on the adopted state (not data): no flag set beyond the adopted drop-ins, stream idle.
# 1) the index file's state before; 2) one forced refresh of each of the six suite channels (the first builds the
# index), timed, the companion's PSS after each; 3) the index file's size, sha256 and mtime after.
set -u
OUT=$1
B=http://localhost:8765
IDX=data/epg/metadata/guides_index.json
CH="ComedyCentral.us@East CNBCUK.uk@SD 10Bold.au@Sydney FoxSports1.us@HD NBC.us@East FilmBox.nl@Netherlands"
P=$(systemctl --user show -p MainPID --value privyhub-companion)
pss() { awk '/^Pss:/{print $2}' /proc/$P/smaps_rollup; }
echo "{\"label\":\"start\",\"at_utc\":\"$(date -u +%FT%T.%3NZ)\",\"pss_kb\":$(pss),\"index_file_before\":$([ -e $IDX ] && echo true || echo false)}" > $OUT
for c in $CH; do
  a=$(date -u +%FT%T.%3NZ); t0=$(date +%s.%N)
  r=$(curl -s -X POST "$B/plugins/epg/refresh?channel_id=${c/@/%40}" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(json.dumps({k:d.get(k) for k in ("ok","programme_count","source")}))')
  t1=$(date +%s.%N)
  echo "{\"label\":\"refresh\",\"channel\":\"$c\",\"start_utc\":\"$a\",\"s\":$(echo "$t1 - $t0" | bc),\"pss_kb\":$(pss),\"index_file\":$([ -e $IDX ] && echo true || echo false),\"reply\":$r}" >> $OUT
done
echo "{\"label\":\"after\",\"at_utc\":\"$(date -u +%FT%T.%3NZ)\",\"pss_kb\":$(pss),\"index_file_bytes\":$(stat -c %s $IDX 2>/dev/null || echo 0),\"index_sha256\":\"$(sha256sum $IDX 2>/dev/null | cut -c1-64)\",\"index_mtime_utc\":\"$(date -u -r $IDX +%FT%T.%3NZ 2>/dev/null)\"}" >> $OUT
