#!/usr/bin/env bash
set -u

ROOT="/home/privyhub/Projects/onn-stream-test"
cd "$ROOT" || { echo "PROBE_FAILED: project root unavailable"; exit 1; }

PACKAGE="com.safeiot.privyhub"
ACTIVITY=".diagnostics.UdpTransportProbeActivity"
PORT=48120
DURATION=20
STAMP="$(date +%Y%m%d_%H%M%S)"
SESSION="logs/transport_probe/opal_bridge_${STAMP}"
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
python3 - "$HOST_IP" "$ONN_IP" "$PORT" <<'PY'
import shlex, sys
host, onn, port = sys.argv[1:4]
script = r'''
HOST_IP="$1"
ONN_IP="$2"
PORT="$3"
LISTDIR="/var/opkg-lists"
PKGBEFORE="/tmp/privyhub_bridge_pkgs_before"
STATE="/tmp/privyhub_bridge_probe_state"
PCAP="/tmp/privyhub_bridge.pcap"
LOG="/tmp/privyhub_bridge_tcpdump.log"
PID=""
INSTALLED=0

cleanup_failure() {
    [ -n "$PID" ] && kill -INT "$PID" 2>/dev/null || true
    if [ "$INSTALLED" -eq 1 ]; then
        opkg remove tcpdump-mini >/dev/null 2>&1 || true
    fi
    rm -f "$LISTDIR"/* 2>/dev/null
    rm -f "$PKGBEFORE" "$STATE" "$PCAP" "$LOG" \
          /tmp/privyhub_bridge_opkg_update.log \
          /tmp/privyhub_bridge_opkg_install.log
}

fail() {
    R="$1"
    cleanup_failure
    echo "router_setup=FAILED:$R"
    exit 1
}

[ "$(find "$LISTDIR" -type f 2>/dev/null | wc -l)" -eq 0 ] || fail "package_lists_not_empty"
command -v opkg >/dev/null 2>&1 || fail "opkg_missing"
command -v tcpdump >/dev/null 2>&1 && fail "tcpdump_already_installed"
[ -d /sys/class/net/br-lan ] || fail "br_lan_missing"

opkg list-installed | sort > "$PKGBEFORE" || fail "package_snapshot_failed"
opkg update >/tmp/privyhub_bridge_opkg_update.log 2>&1 || fail "opkg_update_failed"
opkg install tcpdump-mini >/tmp/privyhub_bridge_opkg_install.log 2>&1 || fail "tcpdump_install_failed"
INSTALLED=1
command -v tcpdump >/dev/null 2>&1 || fail "tcpdump_missing_after_install"

rm -f "$STATE" "$PCAP" "$LOG"

tcpdump -i br-lan -nn -s 0 -w "$PCAP" \
    "udp port $PORT and host $HOST_IP and host $ONN_IP" \
    >"$LOG" 2>&1 &
PID=$!

sleep 1
kill -0 "$PID" 2>/dev/null || fail "bridge_capture_not_running"

printf 'PID=%s\n' "$PID" > "$STATE"

echo "router_setup=OK"
echo "capture_interface=br-lan"
echo "tcpdump_package=tcpdump-mini"
echo "capture_ready=YES"
'''
print("sh -c " + shlex.quote(script) + " sh " + " ".join(map(shlex.quote, [host, onn, port])))
PY
)"

echo "=== OPAL BRIDGE-BOUNDARY SETUP ==="

ssh -tt \
    -o HostKeyAlgorithms=+ssh-rsa \
    -o PreferredAuthentications=password,keyboard-interactive \
    -o PubkeyAuthentication=no \
    -o ConnectTimeout=5 \
    -o ConnectionAttempts=1 \
    -o StrictHostKeyChecking=accept-new \
    -o UserKnownHostsFile="$KNOWN_HOSTS" \
    -o LogLevel=ERROR \
    root@"$GW" "$REMOTE_SETUP" | tee "$SESSION/router_setup.txt"

SETUP_RC=${PIPESTATUS[0]}
if [ "$SETUP_RC" -ne 0 ] || ! grep -q '^capture_ready=YES' "$SESSION/router_setup.txt"; then
    echo "PROBE_FAILED: router bridge capture setup failed"
    exit 1
fi

adb -s "$ONN" shell run-as "$PACKAGE" \
    rm -f files/transport_probe/latest_packets.csv files/transport_probe/latest_summary.json \
    >/dev/null 2>&1 || true

START_OUT="$(
    adb -s "$ONN" shell am start \
        -n "$PACKAGE/$ACTIVITY" \
        --ei udp_port "$PORT" \
        --ei duration_seconds "$((DURATION + 3))" \
        --es label "opal_bridge_boundary" \
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

sleep 4

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

REMOTE_RESTORE="$(
python3 <<'PY'
import shlex
script = r'''
LISTDIR="/var/opkg-lists"
PKGBEFORE="/tmp/privyhub_bridge_pkgs_before"
STATE="/tmp/privyhub_bridge_probe_state"
PCAP="/tmp/privyhub_bridge.pcap"

[ -r "$STATE" ] || exit 21
. "$STATE"

kill -INT "$PID" 2>/dev/null || true
wait "$PID" 2>/dev/null || true
sleep 1

STATUS=0

if [ ! -s "$PCAP" ]; then
    STATUS=22
else
    cat "$PCAP" || STATUS=23
fi

opkg remove tcpdump-mini >/tmp/privyhub_bridge_opkg_remove.log 2>&1
REMOVE_RC=$?

rm -f "$LISTDIR"/* 2>/dev/null
opkg list-installed | sort > /tmp/privyhub_bridge_pkgs_after
cmp -s "$PKGBEFORE" /tmp/privyhub_bridge_pkgs_after
PKG_RC=$?
LIST_COUNT="$(find "$LISTDIR" -type f 2>/dev/null | wc -l)"

[ "$REMOVE_RC" -eq 0 ] || [ "$STATUS" -ne 0 ] || STATUS=24
[ "$PKG_RC" -eq 0 ] || [ "$STATUS" -ne 0 ] || STATUS=25
[ "$LIST_COUNT" -eq 0 ] || [ "$STATUS" -ne 0 ] || STATUS=26

rm -f "$PKGBEFORE" "$STATE" "$PCAP" \
      /tmp/privyhub_bridge_pkgs_after \
      /tmp/privyhub_bridge_opkg_update.log \
      /tmp/privyhub_bridge_opkg_install.log \
      /tmp/privyhub_bridge_opkg_remove.log \
      /tmp/privyhub_bridge_tcpdump.log

exit "$STATUS"
'''
print("sh -c " + shlex.quote(script))
PY
)"

echo
echo "=== OPAL BRIDGE-BOUNDARY RETRIEVE + RESTORE ==="

ssh -T \
    -o HostKeyAlgorithms=+ssh-rsa \
    -o PreferredAuthentications=password,keyboard-interactive \
    -o PubkeyAuthentication=no \
    -o ConnectTimeout=5 \
    -o ConnectionAttempts=1 \
    -o StrictHostKeyChecking=accept-new \
    -o UserKnownHostsFile="$KNOWN_HOSTS" \
    -o LogLevel=ERROR \
    root@"$GW" "$REMOTE_RESTORE" > "$SESSION/router_bridge.pcap"

RESTORE_RC=$?

if [ "$RESTORE_RC" -ne 0 ]; then
    echo "PROBE_FAILED: router retrieve/restore failed with exit $RESTORE_RC"
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

python3 ./companion/diagnostics/udp_transport_probe.py compare \
    --host-csv "$SESSION/host_packets.csv" \
    --android-csv "$SESSION/android_packets.csv" \
    --output-dir "$SESSION" >/dev/null

python3 ./tools/analyze_opal_bridge_boundary_pcap.py --session "$SESSION"

trap - EXIT
rm -f "$KNOWN_HOSTS"
