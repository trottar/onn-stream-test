#!/bin/bash
# D-BASE-T3, added during the run: the onn's kernel counters below the
# socket, every 10 s -- /proc/net/snmp Udp (InDatagrams, InErrors,
# RcvbufErrors, InCsumErrors) and /proc/net/dev wlan0 (rx packets, errs,
# drop). Numbers only (the wlan0 line carries no identifier; the interface
# name is dropped). usage: t3_onn_stack_sample.sh <out.jsonl>; stop: touch <out>.stop
OUT="$1"
while [ ! -f "$OUT.stop" ]; do
  NOW=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  adb shell 'grep -E "^Udp:" /proc/net/snmp | tail -1; grep -E "wlan0:" /proc/net/dev' 2>/dev/null \
    | NOW="$NOW" python3 -c "
import sys,os,json
l=sys.stdin.read().splitlines()
u=l[0].split()[1:] if l else []
w=l[1].split(':',1)[1].split() if len(l)>1 else []
r={'at_utc':os.environ['NOW']}
if len(u)>=7: r.update(udp_in=int(u[0]),udp_inerrors=int(u[2]),udp_rcvbuferrors=int(u[4]),udp_incsumerrors=int(u[6]))
if len(w)>=4: r.update(wlan_rx_packets=int(w[1]),wlan_rx_errs=int(w[2]),wlan_rx_drop=int(w[3]))
print(json.dumps(r))" >> "$OUT"
  sleep 10
done
