#!/bin/bash
# O1 -- the Opal's own view of the air, sampled beside a stream session.
#
# READ-ONLY ON THE OPAL, WITHOUT EXCEPTION. Every command below is a read:
# iw (dev/info/station dump/survey dump), cat of /proc and /sys, logread,
# uptime. Nothing is installed, nothing is written, no uci set/commit, no
# wifi/reboot/opkg. Do not add a write to this script.
#
# Identifiers never leave the Opal: MACs/BSSIDs become stable per-run labels
# (sta-A, sta-B...), SSIDs, WPA keys and addresses are replaced, before
# anything is printed or stored. o1_redact.py runs on every byte.
#
# usage: ./o1_opal_sample.sh <outfile.jsonl> [interval_s] [iface]
#   e.g. ./o1_opal_sample.sh air.jsonl 10 wlan1
# stop with Ctrl-C, or: touch <outfile.jsonl>.stop
set -u
OUT="${1:?usage: o1_opal_sample.sh <outfile.jsonl> [interval_s] [iface]}"
INTERVAL="${2:-10}"
IFACE="${3:-wlan1}"
STOP="$OUT.stop"
HERE="$(cd "$(dirname "$0")" && pwd)"
SSH="ssh -o BatchMode=yes -o ConnectTimeout=8 opal"

echo "sampling Opal interface $IFACE every ${INTERVAL}s -> $OUT" >&2

# --- inventory, once -----------------------------------------------------
$SSH "
  echo '===IWDEV==='    ; iw dev
  echo '===IWINFO==='   ; iw dev $IFACE info
  echo '===STA0LINK===' ; iw dev sta0 link
  echo '===STA1LINK===' ; iw dev sta1 link
  echo '===IWLIST==='   ; iw list
  echo '===UCI==='      ; uci show wireless
  echo '===SURVEY==='   ; iw dev $IFACE survey dump
  echo '===STATION===' ; iw dev $IFACE station dump
  echo '===IWINFOBIN==='; iwinfo $IFACE info; iwinfo $IFACE assoclist
  echo '===LOAD==='     ; cat /proc/loadavg; uptime; date -u
" 2>&1 | python3 "$HERE/o1_redact.py" > "$OUT.inventory.txt"

# --- rounds --------------------------------------------------------------
rm -f "$STOP"
SEQ=0
LOGMARK=$($SSH "logread | wc -l" 2>/dev/null || echo 0)

while [ ! -f "$STOP" ]; do
  T0=$(date +%s%N)
  NOW=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)

  # One connection per round. `iw dev <if> info` carries this driver's live
  # airtime figure ("channel utilization"); `survey dump` carries the same
  # measurement as its 30 ms active/busy pair. Both are kept: the survey
  # pair is the raw numerator/denominator, the info line is the driver's
  # own rounding of it.
  RAW=$($SSH "
    echo '===INFO==='     ; iw dev $IFACE info
    echo '===SURVEY==='   ; iw dev $IFACE survey dump
    echo '===STATION===' ; iw dev $IFACE station dump
    echo '===NETDEV==='   ; cat /proc/net/dev
    echo '===STATS==='    ; for i in $IFACE br-lan eth0 eth0.1 eth0.2; do
                              for f in rx_packets tx_packets rx_dropped \
                                       tx_dropped rx_errors tx_errors; do
                                v=\$(cat /sys/class/net/\$i/statistics/\$f 2>/dev/null)
                                [ -n \"\$v\" ] && echo \"\$i \$f \$v\"
                              done
                            done
    echo '===LOAD==='     ; cat /proc/loadavg
    echo '===MEM==='      ; head -3 /proc/meminfo
    echo '===LOG==='      ; logread | tail -n +$((LOGMARK+1)) \
                            | grep -iE 'wifi|hostapd|deauth|disassoc|DFS|channel|beacon' \
                            | tail -20
    echo '===LOGLINES===' ; logread | wc -l
  " 2>&1)

  COST_MS=$(( ( $(date +%s%N) - T0 ) / 1000000 ))
  NEWMARK=$(printf '%s' "$RAW" | awk '/===LOGLINES===/{getline; print; exit}')
  case "$NEWMARK" in ''|*[!0-9]*) ;; *) LOGMARK="$NEWMARK" ;; esac

  printf '%s' "$RAW" | python3 "$HERE/o1_redact.py" \
    | SEQ="$SEQ" NOW="$NOW" COST_MS="$COST_MS" IFACE="$IFACE" \
      python3 "$HERE/o1_parse.py" >> "$OUT"

  SEQ=$((SEQ+1))
  SPENT=$(( ( $(date +%s%N) - T0 ) / 1000000 ))
  SLEEP=$(( INTERVAL*1000 - SPENT ))
  [ "$SLEEP" -gt 0 ] && sleep "$(awk "BEGIN{print $SLEEP/1000}")"
done
echo "stopped after $SEQ rounds" >&2
