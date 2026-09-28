#!/bin/bash
# D6-R1 -- replay the preserved synthetic UDP suite, unchanged, on the post-B2
# path (host wired -> Opal -> onn 5 GHz). Probe steps as preserved:
#   forward: tools/run_opal_bridge_boundary_probe.sh's probe steps (D082): the
#            onn's UdpTransportProbeActivity (port 48120, 23 s, kernel_timestamp,
#            wifi lock none, priority default), 1 s later the host sender (20 s,
#            5 ms), 4 s later pull latest_summary/packets, then `compare`. The
#            runner's Opal steps (password ssh, opkg install, tcpdump on br-lan)
#            are NOT run: the Opal is read-only.
#   reverse: the archived Windows runner's sequence (Test B parameters): the host
#            receiver (25 s, expected 4000), 0.6 s later the onn's
#            UdpReverseTransportProbeActivity (20 s, urgent_audio), pull the
#            sender files, `compare`. PORT 48122 instead of the default 48102: the
#            companion owns 48102 (the controller input port) and nothing may be
#            stopped for this; the port is an argument on both ends, not code.
# usage: d6_r1_run.sh <fwd|rev> <label> <out_dir>
# Addresses live in this process's variables only and are never written.
set -u
REPO=/home/privyhub/Projects/onn-stream-test
DIR="$1"; LABEL="$2"; OUT="$3"; mkdir -p "$OUT"
PKG=com.safeiot.privyhub
cd "$REPO" || exit 1
snmp() { grep '^Udp:' /proc/net/snmp | tail -1; }
ONN_IP=$(adb shell ip -4 addr show wlan0 2>/dev/null | awk '/inet /{sub(/\/.*/,"",$2);print $2;exit}')
HOST_IP=$(ip -4 route get "$ONN_IP" 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1);exit}}')
[ -n "$ONN_IP" ] && [ -n "$HOST_IP" ] || { echo "FAILED: address discovery"; exit 1; }
# Retry runs (after the first pass): the onn's screensaver (Dreaming, 10-min
# screen-off timeout) ended the probe activities of fwd3/rev2/rev3, so every
# run now wakes the onn first, as p9_run.sh does before its launch.
adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1; sleep 2
snmp > "$OUT/udp_before.txt"
if [ "$DIR" = fwd ]; then
  adb shell run-as $PKG rm -f files/transport_probe/latest_summary.json files/transport_probe/latest_packets.csv >/dev/null 2>&1
  adb shell am start -n $PKG/.diagnostics.UdpTransportProbeActivity --ei udp_port 48120 --ei duration_seconds 23 \
    --es label "$LABEL" --es receiver_priority default --es receive_mode kernel_timestamp --es wifi_lock_mode none \
    > "$OUT/am_start.txt" 2>&1
  sleep 1
  python3 ./companion/diagnostics/udp_transport_probe.py send --target "$ONN_IP" --port 48120 \
    --duration-seconds 20 --interval-ms 5 --output-dir "$OUT" > "$OUT/sender_console.txt" 2>&1
  echo "sender rc $?" >> "$OUT/sender_console.txt"
  sleep 4
  for _ in $(seq 1 20); do
    adb shell run-as $PKG ls files/transport_probe/latest_summary.json >/dev/null 2>&1 && break; sleep 0.25
  done
  adb exec-out run-as $PKG cat files/transport_probe/latest_summary.json > "$OUT/android_summary.json"
  adb exec-out run-as $PKG cat files/transport_probe/latest_packets.csv > "$OUT/android_packets.csv"
  python3 ./companion/diagnostics/udp_transport_probe.py compare --host-csv "$OUT/host_packets.csv" \
    --android-csv "$OUT/android_packets.csv" --output-dir "$OUT" > "$OUT/compare_console.txt" 2>&1
else
  adb shell am force-stop $PKG >/dev/null 2>&1
  adb shell run-as $PKG rm -f files/transport_reverse/latest_sender.csv files/transport_reverse/latest_summary.json files/transport_reverse/latest_progress.json >/dev/null 2>&1
  python3 ./companion/diagnostics/udp_reverse_transport_probe.py receive --port 48122 --duration-seconds 25 \
    --expected-packets 4000 --output-dir "$OUT" > "$OUT/receiver_console.txt" 2>&1 &
  RPID=$!
  sleep 0.6
  adb shell am start -n $PKG/.diagnostics.UdpReverseTransportProbeActivity --es target_ip "$HOST_IP" \
    --ei udp_port 48122 --ei duration_seconds 20 --es label "$LABEL" --es sender_priority urgent_audio \
    2>&1 | sed "s/$HOST_IP/<host>/g" > "$OUT/am_start.txt"
  wait "$RPID"; echo "receiver rc $?" >> "$OUT/receiver_console.txt"
  sleep 2
  adb exec-out run-as $PKG cat files/transport_reverse/latest_summary.json > "$OUT/android_summary.json"
  adb exec-out run-as $PKG cat files/transport_reverse/latest_sender.csv > "$OUT/android_sender.csv"
  adb exec-out run-as $PKG cat files/transport_reverse/latest_progress.json > "$OUT/android_progress.json" 2>/dev/null
  python3 ./companion/diagnostics/udp_reverse_transport_probe.py compare --sender-csv "$OUT/android_sender.csv" \
    --host-csv "$OUT/host_packets.csv" --output-dir "$OUT" > "$OUT/compare_console.txt" 2>&1
  adb shell am force-stop $PKG >/dev/null 2>&1
fi
snmp > "$OUT/udp_after.txt"
for f in "$OUT"/*; do
  sed -i "s/$ONN_IP/<onn>/g; s/$HOST_IP/<host>/g" "$f" 2>/dev/null
done
echo "done $DIR $LABEL"
