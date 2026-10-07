#!/usr/bin/env bash
# E3-S6 smoke (not data): the companion with PRIVYHUB_EPG_GUIDE_INDEX=cached + PRIVYHUB_MEM_PROBE=1, stream idle.
# 1) one forced refresh of each of the six suite channels (the first builds the index), timed, PSS after each;
# 2) the candidate dump per channel by both paths (memprobe op=cands: today's parse vs the index) -> diff;
# 3) teardown: drop-in removed, daemon-reload, restart, environ checked.
set -u
OUT=$1
DI=~/.config/systemd/user/privyhub-companion.service.d/e3_flag.conf
B=http://localhost:8765
CH="ComedyCentral.us@East CNBCUK.uk@SD 10Bold.au@Sydney FoxSports1.us@HD NBC.us@East FilmBox.nl@Netherlands"
printf '[Service]\nEnvironment=PRIVYHUB_EPG_GUIDE_INDEX=cached\nEnvironment=PRIVYHUB_MEM_PROBE=1\n' > $DI
systemctl --user daemon-reload; systemctl --user restart privyhub-companion; sleep 8
P=$(systemctl --user show -p MainPID --value privyhub-companion)
pss() { awk '/^Pss:/{print $2}' /proc/$P/smaps_rollup; }
echo "{\"label\":\"start\",\"pss_kb\":$(pss),\"index_file_before\":$([ -e data/epg/metadata/guides_index.json ] && echo true || echo false)}" > $OUT
for c in $CH; do
  t0=$(date +%s.%N)
  r=$(curl -s -X POST "$B/plugins/epg/refresh?channel_id=${c/@/%40}" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(json.dumps({k:d.get(k) for k in ("ok","programme_count","source")}))')
  t1=$(date +%s.%N)
  echo "{\"label\":\"refresh\",\"channel\":\"$c\",\"s\":$(echo "$t1 - $t0" | bc),\"pss_kb\":$(pss),\"reply\":$r}" >> $OUT
done
for c in $CH; do
  echo "{\"label\":\"cands\",\"channel\":\"$c\",\"reply\":$(curl -s "$B/plugins/epg/memprobe?op=cands&channel_id=${c/@/%40}" | python3 -c 'import json,sys;print(json.dumps(json.load(sys.stdin)))')}" >> $OUT
done
echo "{\"label\":\"after_cands\",\"pss_kb\":$(pss),\"index_file_bytes\":$(stat -c %s data/epg/metadata/guides_index.json 2>/dev/null || echo 0)}" >> $OUT
rm -f $DI; systemctl --user daemon-reload; systemctl --user restart privyhub-companion; sleep 8
echo "{\"label\":\"teardown\",\"environ\":\"$(tr '\0' '\n' < /proc/$(systemctl --user show -p MainPID --value privyhub-companion)/environ | grep ^PRIVYHUB_ | tr '\n' ' ')\",\"dropin_absent\":$([ -e $DI ] && echo false || echo true)}" >> $OUT
