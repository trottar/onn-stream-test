#!/usr/bin/env bash
set -u

ROOT="/home/privyhub/Projects/onn-stream-test"
cd "$ROOT" || { echo "PROBE_FAILED: project root unavailable"; exit 1; }

PACKAGE="com.safeiot.privyhub"
ACTIVITY=".diagnostics.UdpTransportProbeActivity"
PORT=48120
DURATION=20
STAMP="$(date +%Y%m%d_%H%M%S)"
SESSION="logs/transport_probe/opal_dual_boundary_${STAMP}"
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
    try:
        a = ipaddress.ip_address(value)
    except Exception:
        raise SystemExit(1)
    if a.version != 4:
        raise SystemExit(1)
PY
then
    echo "PROBE_FAILED: local address discovery failed"
    exit 1
fi

if ss -lun 2>/dev/null | awk '{print $5}' | grep -Eq '(^|:)'$PORT'$'; then
    echo "PROBE_FAILED: UDP $PORT already in use"
    exit 1
fi

KNOWN_HOSTS="$(mktemp)"
REMOTE_SETUP="$SESSION/remote_setup.txt"

REMOTE_CMD="$(
python3 - "$HOST_IP" "$ONN_IP" "$PORT" <<'PY'
import shlex, sys
host, onn, port = sys.argv[1:4]
script = r'''
HOST_IP="$1"
ONN_IP="$2"
PORT="$3"
STATE="/tmp/privyhub_dual_boundary_state"
PKGBEFORE="/tmp/privyhub_dual_boundary_pkgs_before"
LISTDIR="/var/opkg-lists"
PCAP_IN="/tmp/privyhub_linux_radio.pcap"
PCAP_OUT="/tmp/privyhub_onn_radio.pcap"
LOG_IN="/tmp/privyhub_linux_radio_tcpdump.log"
LOG_OUT="/tmp/privyhub_onn_radio_tcpdump.log"
PID_IN=""
PID_OUT=""
INSTALLED_BY_PROBE=0

cleanup_setup_failure() {
    [ -n "$PID_IN" ] && kill -INT "$PID_IN" 2>/dev/null || true
    [ -n "$PID_OUT" ] && kill -INT "$PID_OUT" 2>/dev/null || true
    if [ "$INSTALLED_BY_PROBE" -eq 1 ]; then
        opkg remove tcpdump-mini >/dev/null 2>&1 || true
    fi
    rm -f "$LISTDIR"/* 2>/dev/null
    rm -f "$STATE" "$PKGBEFORE" /tmp/privyhub_dual_boundary_pkgs_after \
          /tmp/privyhub_opkg_update.log /tmp/privyhub_opkg_install.log \
          /tmp/privyhub_opkg_remove.log \
          "$PCAP_IN" "$PCAP_OUT" "$LOG_IN" "$LOG_OUT"
}

fail() {
    REASON="$1"
    cleanup_setup_failure
    echo "router_setup=FAILED:$REASON"
    exit 1
}

[ "$(find "$LISTDIR" -type f 2>/dev/null | wc -l)" -eq 0 ] || fail "package_lists_not_empty"
command -v iw >/dev/null 2>&1 || fail "iw_missing"
command -v opkg >/dev/null 2>&1 || fail "opkg_missing"
command -v tcpdump >/dev/null 2>&1 && fail "tcpdump_already_installed_unexpected"
opkg list-installed | sort > "$PKGBEFORE" || fail "package_snapshot_failed"

resolve_mac() {
    TARGET="$1"
    M="$(ip neigh show "$TARGET" 2>/dev/null | sed -n "s/.*lladdr \([^ ]*\).*/\1/p" | head -n1)"
    if [ -z "$M" ]; then
        ping -c 1 -W 1 "$TARGET" >/dev/null 2>&1 || true
        M="$(ip neigh show "$TARGET" 2>/dev/null | sed -n "s/.*lladdr \([^ ]*\).*/\1/p" | head -n1)"
    fi
    printf "%s" "$M"
}
find_radio() {
    M="$1"
    [ -n "$M" ] || { echo "UNKNOWN"; return; }
    for I in wlan0 wlan1; do
        if iw dev "$I" station dump 2>/dev/null | grep -i -q "^Station $M "; then
            echo "$I"; return
        fi
    done
    echo "UNKNOWN"
}

HOST_MAC="$(resolve_mac "$HOST_IP")"
ONN_MAC="$(resolve_mac "$ONN_IP")"
HOST_RADIO="$(find_radio "$HOST_MAC")"
ONN_RADIO="$(find_radio "$ONN_MAC")"
[ "$HOST_RADIO" != "UNKNOWN" ] || fail "linux_radio_unknown"
[ "$ONN_RADIO" != "UNKNOWN" ] || fail "onn_radio_unknown"
[ "$HOST_RADIO" != "$ONN_RADIO" ] || fail "endpoints_on_same_radio"

opkg update >/tmp/privyhub_opkg_update.log 2>&1 || fail "opkg_update_failed"
opkg install tcpdump-mini >/tmp/privyhub_opkg_install.log 2>&1 || fail "tcpdump_mini_install_failed"
INSTALLED_BY_PROBE=1
command -v tcpdump >/dev/null 2>&1 || fail "tcpdump_not_available_after_install"

rm -f "$PCAP_IN" "$PCAP_OUT" "$LOG_IN" "$LOG_OUT" "$STATE"

tcpdump -i "$HOST_RADIO" -nn -s 0 -w "$PCAP_IN"     "udp port $PORT and host $HOST_IP and host $ONN_IP"     >"$LOG_IN" 2>&1 &
PID_IN=$!

tcpdump -i "$ONN_RADIO" -nn -s 0 -w "$PCAP_OUT"     "udp port $PORT and host $HOST_IP and host $ONN_IP"     >"$LOG_OUT" 2>&1 &
PID_OUT=$!

sleep 1
kill -0 "$PID_IN" 2>/dev/null || fail "linux_radio_capture_not_running"
kill -0 "$PID_OUT" 2>/dev/null || fail "onn_radio_capture_not_running"

(
    sleep 300
    if [ -r "$STATE" ]; then
        . "$STATE"
        kill -INT "$PID_IN" "$PID_OUT" 2>/dev/null || true
        sleep 1
        opkg remove tcpdump-mini >/dev/null 2>&1 || true
        rm -f "$LISTDIR"/* 2>/dev/null
        rm -f "$STATE" "$PKGBEFORE" /tmp/privyhub_dual_boundary_pkgs_after \
              /tmp/privyhub_opkg_update.log /tmp/privyhub_opkg_install.log \
              /tmp/privyhub_opkg_remove.log \
              "$PCAP_IN" "$PCAP_OUT" "$LOG_IN" "$LOG_OUT"
    fi
) >/dev/null 2>&1 &
WATCHDOG=$!

{
    echo "PID_IN=$PID_IN"
    echo "PID_OUT=$PID_OUT"
    echo "WATCHDOG=$WATCHDOG"
    echo "HOST_RADIO=$HOST_RADIO"
    echo "ONN_RADIO=$ONN_RADIO"
} > "$STATE"

echo "router_setup=OK"
echo "linux_radio=$HOST_RADIO"
echo "onn_radio=$ONN_RADIO"
echo "tcpdump_package=tcpdump-mini"
echo "capture_ready=YES"
'''
print("sh -c " + shlex.quote(script) + " sh " + " ".join(map(shlex.quote, [host, onn, port])))
PY
)"

echo "=== OPAL DUAL-BOUNDARY SETUP ==="
ssh -tt     -o HostKeyAlgorithms=+ssh-rsa     -o PreferredAuthentications=password,keyboard-interactive     -o PubkeyAuthentication=no     -o ConnectTimeout=5     -o ConnectionAttempts=1     -o StrictHostKeyChecking=accept-new     -o UserKnownHostsFile="$KNOWN_HOSTS"     -o LogLevel=ERROR     root@"$GW" "$REMOTE_CMD" | tee "$REMOTE_SETUP"
SSH_SETUP_RC=${PIPESTATUS[0]}

if [ "$SSH_SETUP_RC" -ne 0 ] || ! grep -q '^capture_ready=YES' "$REMOTE_SETUP"; then
    rm -f "$KNOWN_HOSTS"
    echo "PROBE_FAILED: router capture setup failed"
    exit 1
fi

adb -s "$ONN" shell run-as "$PACKAGE"     rm -f files/transport_probe/latest_packets.csv files/transport_probe/latest_summary.json     >/dev/null 2>&1 || true

START_OUT="$(
    adb -s "$ONN" shell am start         -n "$PACKAGE/$ACTIVITY"         --ei udp_port "$PORT"         --ei duration_seconds "$((DURATION + 3))"         --es label "opal_dual_boundary"         --es receiver_priority "default"         --es receive_mode "kernel_timestamp"         --es wifi_lock_mode "none"         2>&1
)"

SENDER_RC=0
if printf '%s\n' "$START_OUT" | grep -Eq 'Error type|Activity class.*does not exist|Permission Denial'; then
    echo "PROBE_FAILED: Android diagnostic Activity could not start"
    SENDER_RC=1
else
    sleep 1
    python3 ./companion/diagnostics/udp_transport_probe.py send         --target "$ONN_IP"         --port "$PORT"         --duration-seconds "$DURATION"         --interval-ms 5         --output-dir "$SESSION"
    SENDER_RC=$?
fi

sleep 4

READY=0
for _ in $(seq 1 20); do
    if adb -s "$ONN" shell run-as "$PACKAGE"         ls files/transport_probe/latest_summary.json >/dev/null 2>&1
    then
        READY=1
        break
    fi
    sleep 0.25
done

if [ "$READY" -eq 1 ]; then
    adb -s "$ONN" exec-out run-as "$PACKAGE"         cat files/transport_probe/latest_summary.json         > "$SESSION/android_summary.json"
    adb -s "$ONN" exec-out run-as "$PACKAGE"         cat files/transport_probe/latest_packets.csv         > "$SESSION/android_packets.csv"
fi

REMOTE_RESTORE_CMD="$(
python3 <<'PY'
import shlex
script = r'''
STATE="/tmp/privyhub_dual_boundary_state"
PKGBEFORE="/tmp/privyhub_dual_boundary_pkgs_before"
LISTDIR="/var/opkg-lists"
PCAP_IN="/tmp/privyhub_linux_radio.pcap"
PCAP_OUT="/tmp/privyhub_onn_radio.pcap"

[ -r "$STATE" ] || exit 21
. "$STATE"

STATUS=0
kill "$WATCHDOG" 2>/dev/null || true
kill -INT "$PID_IN" "$PID_OUT" 2>/dev/null || true
wait "$PID_IN" 2>/dev/null || true
wait "$PID_OUT" 2>/dev/null || true
sleep 1

if [ ! -s "$PCAP_IN" ]; then
    STATUS=22
elif [ ! -s "$PCAP_OUT" ]; then
    STATUS=23
else
    tar -cf - "$PCAP_IN" "$PCAP_OUT" || STATUS=24
fi

opkg remove tcpdump-mini >/tmp/privyhub_opkg_remove.log 2>&1
REMOVE_RC=$?
rm -f "$LISTDIR"/* 2>/dev/null
opkg list-installed | sort > /tmp/privyhub_dual_boundary_pkgs_after
cmp -s "$PKGBEFORE" /tmp/privyhub_dual_boundary_pkgs_after
PKG_RC=$?
LIST_COUNT="$(find "$LISTDIR" -type f 2>/dev/null | wc -l)"

[ "$REMOVE_RC" -eq 0 ] || [ "$STATUS" -ne 0 ] || STATUS=25
[ "$PKG_RC" -eq 0 ] || [ "$STATUS" -ne 0 ] || STATUS=26
[ "$LIST_COUNT" -eq 0 ] || [ "$STATUS" -ne 0 ] || STATUS=27

rm -f "$STATE" "$PKGBEFORE" /tmp/privyhub_dual_boundary_pkgs_after \
      /tmp/privyhub_opkg_update.log /tmp/privyhub_opkg_install.log \
      /tmp/privyhub_opkg_remove.log \
      /tmp/privyhub_linux_radio_tcpdump.log /tmp/privyhub_onn_radio_tcpdump.log \
      "$PCAP_IN" "$PCAP_OUT"

exit "$STATUS"
'''
print("sh -c " + shlex.quote(script))
PY
)"

BUNDLE="$SESSION/router_pcaps.tar"

echo
echo "=== OPAL DUAL-BOUNDARY RETRIEVE + RESTORE ==="
ssh -T     -o HostKeyAlgorithms=+ssh-rsa     -o PreferredAuthentications=password,keyboard-interactive     -o PubkeyAuthentication=no     -o ConnectTimeout=5     -o ConnectionAttempts=1     -o StrictHostKeyChecking=accept-new     -o UserKnownHostsFile="$KNOWN_HOSTS"     -o LogLevel=ERROR     root@"$GW" "$REMOTE_RESTORE_CMD" > "$BUNDLE"
RESTORE_RC=$?

rm -f "$KNOWN_HOSTS"

if [ "$RESTORE_RC" -ne 0 ]; then
    echo "PROBE_FAILED: router retrieve/restore failed with exit $RESTORE_RC"
    echo "Router package state must be checked before another probe."
    exit 1
fi

mkdir -p "$SESSION/router_raw"
tar -xf "$BUNDLE" -C "$SESSION/router_raw"

IN_PCAP="$(find "$SESSION/router_raw" -type f -name 'privyhub_linux_radio.pcap' | head -n1)"
OUT_PCAP="$(find "$SESSION/router_raw" -type f -name 'privyhub_onn_radio.pcap' | head -n1)"
if [ -z "$IN_PCAP" ] || [ -z "$OUT_PCAP" ]; then
    echo "PROBE_FAILED: router PCAP extraction failed"
    exit 1
fi
cp "$IN_PCAP" "$SESSION/router_linux_radio.pcap"
cp "$OUT_PCAP" "$SESSION/router_onn_radio.pcap"

if [ "$SENDER_RC" -ne 0 ]; then
    echo "PROBE_FAILED: host sender returned $SENDER_RC"
    exit 1
fi
if [ "$READY" -ne 1 ]; then
    echo "PROBE_FAILED: Android summary was not written"
    exit 1
fi

python3 ./companion/diagnostics/udp_transport_probe.py compare     --host-csv "$SESSION/host_packets.csv"     --android-csv "$SESSION/android_packets.csv"     --output-dir "$SESSION" >/dev/null

python3 ./tools/analyze_opal_dual_boundary_pcap.py --session "$SESSION"
