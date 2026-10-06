#!/usr/bin/env bash
# E3-S2 probe: the companion with PRIVYHUB_MEM_PROBE=1 (drop-in for the probe only), stream idle.
# start tracemalloc -> snap -> forced grab 1 -> snap -> 60 s -> snap -> forced grab 2 -> snap -> malloc_trim -> snap
# (+ gc -> snap). Each snap = /plugins/epg/memprobe (tracemalloc traced MB, gc objects by type, smaps_rollup).
set -u
OUT=$1; CH=${2:-NBC.us@East}
DI=~/.config/systemd/user/privyhub-companion.service.d/e3_flag.conf
B=http://localhost:8765
printf '[Service]\nEnvironment=PRIVYHUB_MEM_PROBE=1\n' > $DI
systemctl --user daemon-reload; systemctl --user restart privyhub-companion; sleep 8
snap() { echo "{\"label\":\"$1\",\"at\":\"$(date -u +%H:%M:%SZ)\",\"probe\":$(curl -s "$B/plugins/epg/memprobe?op=$2")}" >> $OUT; }
grab() { echo "{\"label\":\"$1\",\"at\":\"$(date -u +%H:%M:%SZ)\",\"grab\":$(curl -s -X POST "$B/plugins/epg/refresh?channel_id=${CH/@/%40}" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(json.dumps({k:d.get(k) for k in ("ok","programme_count","attempts")}))')}" >> $OUT; }
: > $OUT
snap start start
sleep 2; snap before_grab1 snap
grab grab1; snap after_grab1 snap
sleep 60; snap after_grab1_60s snap
grab grab2; snap after_grab2 snap
snap after_trim trim
snap after_gc gc
rm -f $DI; systemctl --user daemon-reload; systemctl --user restart privyhub-companion; sleep 8
echo "{\"label\":\"teardown\",\"environ\":\"$(tr '\0' '\n' < /proc/$(systemctl --user show -p MainPID --value privyhub-companion)/environ | grep ^PRIVYHUB_ | tr '\n' ' ')\",\"dropin_absent\":$([ -e $DI ] && echo false || echo true)}" >> $OUT
