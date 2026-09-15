#!/usr/bin/env bash
set -u

ROOT="/home/privyhub/Projects/onn-stream-test"
cd "$ROOT" || { echo "PROBE_FAILED: project root unavailable"; exit 1; }

PACKAGE="com.safeiot.privyhub"
ACTIVITY=".diagnostics.UdpTransportProbeActivity"
PORT=48120
DURATION=20
STAMP="$(date +%Y%m%d_%H%M%S)"
SESSION="logs/transport_probe/opal_netdev_counters_${STAMP}"
mkdir -p "$SESSION"

GW="$(ip route show default 2>/dev/null | awk 'NR==1 {print $3}')"
HOST_IFACE="$(ip route show default 2>/dev/null | awk 'NR==1 {print $5}')"
HOST_IP="$(ip -4 addr show dev "$HOST_IFACE" 2>/dev/null | sed -n 's/.*inet \([0-9.]*\)\/.*/\1/p' | head -n1)"

mapfile -t DEVICES < <(adb devices | awk 'NR>1 && $2=="device" && $1 !~ /^emulator-/ {print $1}')
if [ "${#DEVICES[@]}" -ne 1 ]; then
    echo "PROBE_FAILED: expected one physical onn ADB target; found ${#DEVICES[@]}"
    exit 1
fi

ONN="${DEVICES[0]}"
ONN_IP=""
case "$ONN" in
    [0-9]*.[0-9]*.[0-9]*.[0-9]*:*) ONN_IP="${ONN%%:*}" ;;
esac

if [ -z "$ONN_IP" ]; then
    WIFI_IFACE="$(adb -s "$ONN" shell getprop wifi.interface 2>/dev/null | tr -d '\r' | head -n1)"
    [ -n "$WIFI_IFACE" ] || WIFI_IFACE="wlan0"
    ONN_IP="$(
        adb -s "$ONN" shell "ip -4 addr show dev '$WIFI_IFACE' 2>/dev/null || ip addr show '$WIFI_IFACE' 2>/dev/null" |
        tr -d '\r' |
        sed -n 's/.*inet \([0-9.]*\)\/.*/\1/p' |
        head -n1
    )"
fi

if ! python3 - "$GW" "$HOST_IP" "$ONN_IP" <<'PY' >/dev/null
import ipaddress, sys
for value in sys.argv[1:]:
    a = ipaddress.ip_address(value)
    if a.version != 4:
        raise SystemExit(1)
PY
then
    echo "PROBE_FAILED: local address discovery failed"
    exit 1
fi

KNOWN_HOSTS="$(mktemp)"
trap 'rm -f "$KNOWN_HOSTS"' EXIT

REMOTE_SETUP="$(
python3 <<'PY'
import shlex
script = r'''
OUT="/tmp/privyhub_netdev_counters.csv"
STATE="/tmp/privyhub_netdev_counter_state"

for IFACE in wlan0 wlan1 br-lan; do
    [ -d "/sys/class/net/$IFACE/statistics" ] || {
        echo "counter_setup=FAILED:missing_$IFACE"
        exit 1
    }
done

SAMPLER="/tmp/privyhub_netdev_counter_sampler.sh"
LOG="/tmp/privyhub_netdev_counter_sampler.log"

rm -f "$OUT" "$STATE" "$SAMPLER" "$LOG"

cat > "$SAMPLER" <<'EOS'
#!/bin/sh
OUT="/tmp/privyhub_netdev_counters.csv"

exec > "$OUT" 2>/tmp/privyhub_netdev_counter_sampler.log

echo "sample,wlan0_rx_packets,wlan0_tx_packets,wlan0_rx_bytes,wlan0_tx_bytes,wlan0_rx_dropped,wlan0_tx_dropped,wlan1_rx_packets,wlan1_tx_packets,wlan1_rx_bytes,wlan1_tx_bytes,wlan1_rx_dropped,wlan1_tx_dropped,br-lan_rx_packets,br-lan_tx_packets,br-lan_rx_bytes,br-lan_tx_bytes,br-lan_rx_dropped,br-lan_tx_dropped"

I=0
while [ "$I" -le 31 ]; do
    line="$I"
    for IFACE in wlan0 wlan1 br-lan; do
        for FIELD in rx_packets tx_packets rx_bytes tx_bytes rx_dropped tx_dropped; do
            V="$(cat "/sys/class/net/$IFACE/statistics/$FIELD" 2>/dev/null)"
            [ -n "$V" ] || V=0
            line="$line,$V"
        done
    done
    echo "$line"
    I=$((I + 1))
    [ "$I" -le 31 ] && sleep 1
done
EOS

chmod 700 "$SAMPLER" || {
    echo "counter_setup=FAILED:sampler_chmod_failed"
    exit 1
}

nohup "$SAMPLER" >/dev/null 2>&1 </dev/null &
PID=$!
printf 'PID=%s\n' "$PID" > "$STATE"

sleep 1
kill -0 "$PID" 2>/dev/null || {
    echo "counter_setup=FAILED:sampler_not_running"
    rm -f "$SAMPLER" "$LOG"
    exit 1
}

LINES="$(wc -l < "$OUT" 2>/dev/null)"
[ -n "$LINES" ] || LINES=0
[ "$LINES" -ge 2 ] || {
    echo "counter_setup=FAILED:sampler_no_initial_rows"
    kill "$PID" 2>/dev/null || true
    rm -f "$OUT" "$STATE" "$SAMPLER" "$LOG"
    exit 1
}

echo "counter_setup=OK"
echo "interfaces=wlan0,wlan1,br-lan"
echo "sample_interval_seconds=1"
echo "sample_count_planned=32"
'''
print("sh -c " + shlex.quote(script))
PY
)"

echo "=== OPAL NETDEV-COUNTER SETUP ==="

ssh -tt \
    -o HostKeyAlgorithms=+ssh-rsa \
    -o PreferredAuthentications=password,keyboard-interactive \
    -o PubkeyAuthentication=no \
    -o ConnectTimeout=5 \
    -o ConnectionAttempts=1 \
    -o StrictHostKeyChecking=accept-new \
    -o UserKnownHostsFile="$KNOWN_HOSTS" \
    -o LogLevel=ERROR \
    root@"$GW" "$REMOTE_SETUP" | tee "$SESSION/router_counter_setup.txt"

SETUP_RC=${PIPESTATUS[0]}
if [ "$SETUP_RC" -ne 0 ] || ! grep -q '^counter_setup=OK' "$SESSION/router_counter_setup.txt"; then
    echo "PROBE_FAILED: router counter sampler setup failed"
    exit 1
fi

sleep 4

adb -s "$ONN" shell run-as "$PACKAGE" \
    rm -f files/transport_probe/latest_packets.csv files/transport_probe/latest_summary.json \
    >/dev/null 2>&1 || true

START_OUT="$(
    adb -s "$ONN" shell am start \
        -n "$PACKAGE/$ACTIVITY" \
        --ei udp_port "$PORT" \
        --ei duration_seconds "$((DURATION + 3))" \
        --es label "opal_netdev_counters" \
        --es receiver_priority "default" \
        --es receive_mode "kernel_timestamp" \
        --es wifi_lock_mode "none" \
        2>&1
)"

SENDER_RC=0
if printf '%s\n' "$START_OUT" | grep -Eq 'Error type|Activity class.*does not exist|Permission Denial'; then
    echo "PROBE_FAILED: Android diagnostic Activity could not start"
    SENDER_RC=1
else
    sleep 1
    python3 ./companion/diagnostics/udp_transport_probe.py send \
        --target "$ONN_IP" \
        --port "$PORT" \
        --duration-seconds "$DURATION" \
        --interval-ms 5 \
        --output-dir "$SESSION"
    SENDER_RC=$?
fi

sleep 5

READY=0
for _ in $(seq 1 20); do
    if adb -s "$ONN" shell run-as "$PACKAGE" \
        ls files/transport_probe/latest_summary.json >/dev/null 2>&1
    then
        READY=1
        break
    fi
    sleep 0.25
done

if [ "$READY" -eq 1 ]; then
    adb -s "$ONN" exec-out run-as "$PACKAGE" \
        cat files/transport_probe/latest_summary.json \
        > "$SESSION/android_summary.json"
    adb -s "$ONN" exec-out run-as "$PACKAGE" \
        cat files/transport_probe/latest_packets.csv \
        > "$SESSION/android_packets.csv"
fi

REMOTE_RETRIEVE="$(
python3 <<'PY'
import shlex
script = r'''
OUT="/tmp/privyhub_netdev_counters.csv"
STATE="/tmp/privyhub_netdev_counter_state"
SAMPLER="/tmp/privyhub_netdev_counter_sampler.sh"
LOG="/tmp/privyhub_netdev_counter_sampler.log"

[ -r "$STATE" ] || exit 21
. "$STATE"

for I in 1 2 3 4 5 6 7 8 9 10 11 12; do
    if ! kill -0 "$PID" 2>/dev/null; then
        break
    fi
    sleep 1
done

if kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null || true
    wait "$PID" 2>/dev/null || true
fi

[ -s "$OUT" ] || {
    rm -f "$STATE" "$SAMPLER" "$LOG"
    exit 22
}

LINES="$(wc -l < "$OUT" 2>/dev/null)"
[ -n "$LINES" ] || LINES=0
if [ "$LINES" -lt 25 ]; then
    rm -f "$OUT" "$STATE" "$SAMPLER" "$LOG"
    exit 23
fi

cat "$OUT"
RC=$?

rm -f "$OUT" "$STATE" "$SAMPLER" "$LOG"
exit "$RC"
'''
print("sh -c " + shlex.quote(script))
PY
)"

echo
echo "=== OPAL NETDEV-COUNTER RETRIEVE ==="

ssh -T \
    -o HostKeyAlgorithms=+ssh-rsa \
    -o PreferredAuthentications=password,keyboard-interactive \
    -o PubkeyAuthentication=no \
    -o ConnectTimeout=5 \
    -o ConnectionAttempts=1 \
    -o StrictHostKeyChecking=accept-new \
    -o UserKnownHostsFile="$KNOWN_HOSTS" \
    -o LogLevel=ERROR \
    root@"$GW" "$REMOTE_RETRIEVE" > "$SESSION/router_netdev_counters.csv"

RETRIEVE_RC=$?

if [ "$RETRIEVE_RC" -ne 0 ]; then
    echo "PROBE_FAILED: router counter retrieval failed with exit $RETRIEVE_RC"
    exit 1
fi

if [ "$SENDER_RC" -ne 0 ]; then
    echo "PROBE_FAILED: host sender returned $SENDER_RC"
    exit 1
fi

if [ "$READY" -ne 1 ]; then
    echo "PROBE_FAILED: Android summary was not written"
    exit 1
fi

if ! python3 ./companion/diagnostics/udp_transport_probe.py compare \
    --host-csv "$SESSION/host_packets.csv" \
    --android-csv "$SESSION/android_packets.csv" \
    --output-dir "$SESSION" >/dev/null
then
    echo "PROBE_FAILED: host/Android comparison failed"
    exit 1
fi

if ! python3 ./tools/analyze_opal_netdev_counter_probe.py --session "$SESSION"; then
    echo "PROBE_FAILED: netdev counter analysis failed"
    exit 1
fi

trap - EXIT
rm -f "$KNOWN_HOSTS"
exit 0
