#!/usr/bin/env bash
set -u

ROOT="/home/privyhub/Projects/onn-stream-test"
cd "$ROOT" || { echo "PROBE_FAILED: project root unavailable"; exit 1; }

D080_RUNNER="./tools/run_opal_dual_boundary_probe.sh"
D080_ANALYZER="./tools/analyze_opal_dual_boundary_pcap.py"
EXPECTED_RUNNER_SHA="25b220aad4c9ba82372be7673846eca8ef6b4a454353fc8af8f8fc99d69e1b66"
EXPECTED_ANALYZER_SHA="3c26f5d4aa82c0de6f99cad8ba77882c2d1b27e89c9efea3eb6fbf283fb18942"

if [ ! -f "$D080_RUNNER" ] || [ ! -f "$D080_ANALYZER" ]; then
    echo "PROBE_FAILED: required D080 diagnostic files are missing"
    exit 1
fi

RUNNER_SHA="$(sha256sum "$D080_RUNNER" | awk '{print $1}')"
ANALYZER_SHA="$(sha256sum "$D080_ANALYZER" | awk '{print $1}')"

if [ "$RUNNER_SHA" != "$EXPECTED_RUNNER_SHA" ]; then
    echo "PROBE_FAILED: unexpected D080 runner hash"
    exit 1
fi
if [ "$ANALYZER_SHA" != "$EXPECTED_ANALYZER_SHA" ]; then
    echo "PROBE_FAILED: unexpected D080R1 analyzer hash"
    exit 1
fi

GW="$(ip route show default 2>/dev/null | awk 'NR==1 {print $3}')"
[ -n "$GW" ] || { echo "PROBE_FAILED: local gateway discovery failed"; exit 1; }

KNOWN_HOSTS="$(mktemp)"
ACCEL_ARMED=0

ssh_router() {
    ssh -tt \
        -o HostKeyAlgorithms=+ssh-rsa \
        -o PreferredAuthentications=password,keyboard-interactive \
        -o PubkeyAuthentication=no \
        -o ConnectTimeout=5 \
        -o ConnectionAttempts=1 \
        -o StrictHostKeyChecking=accept-new \
        -o UserKnownHostsFile="$KNOWN_HOSTS" \
        -o LogLevel=ERROR \
        root@"$GW" "$1"
}

build_disable_command() {
python3 <<'PY_REMOTE'
import shlex
script = r'''STATE="/tmp/privyhub_acceleration_probe_state"
RESTORE="/tmp/privyhub_acceleration_probe_restore.sh"
WATCHDOG_LOG="/tmp/privyhub_acceleration_probe_watchdog.log"
STATE_CREATED=0
WATCHDOG_PID=""

fail() {
    REASON="$1"
    if [ "$STATE_CREATED" -eq 1 ]; then
        [ -z "$WATCHDOG_PID" ] || kill "$WATCHDOG_PID" 2>/dev/null || true
        if [ -x "$RESTORE" ]; then
            "$RESTORE" >/dev/null 2>&1 || true
        else
            rm -f "$STATE" "$RESTORE" "$WATCHDOG_LOG"
        fi
    fi
    echo "acceleration_setup=FAILED:$REASON"
    exit 1
}

[ ! -e "$STATE" ] || fail "existing_probe_state"
[ ! -e "$RESTORE" ] || fail "existing_restore_script"

ORIG_FLOW="$(uci -q get firewall.@defaults[0].flow_offloading 2>/dev/null)"
ORIG_HW="$(uci -q get firewall.@defaults[0].flow_offloading_hw 2>/dev/null)"

case "$ORIG_FLOW" in 0|1) ;; *) fail "unexpected_flow_offloading_value" ;; esac
case "$ORIG_HW" in 0|1) ;; *) fail "unexpected_flow_offloading_hw_value" ;; esac

[ "$ORIG_FLOW" = "1" ] && [ "$ORIG_HW" = "1" ] || fail "acceleration_not_in_expected_enabled_state"

printf 'ORIG_FLOW=%s\nORIG_HW=%s\n' "$ORIG_FLOW" "$ORIG_HW" > "$STATE" || fail "state_write_failed"
STATE_CREATED=1

cat > "$RESTORE" <<'EOS'
#!/bin/sh
STATE="/tmp/privyhub_acceleration_probe_state"
SELF="/tmp/privyhub_acceleration_probe_restore.sh"
[ -r "$STATE" ] || exit 0
. "$STATE"
uci set firewall.@defaults[0].flow_offloading="$ORIG_FLOW" || exit 31
uci set firewall.@defaults[0].flow_offloading_hw="$ORIG_HW" || exit 32
uci commit firewall || exit 33
/etc/init.d/firewall restart >/tmp/privyhub_acceleration_probe_firewall_restore.log 2>&1 || exit 34
FLOW="$(uci -q get firewall.@defaults[0].flow_offloading 2>/dev/null)"
HW="$(uci -q get firewall.@defaults[0].flow_offloading_hw 2>/dev/null)"
[ "$FLOW" = "$ORIG_FLOW" ] || exit 35
[ "$HW" = "$ORIG_HW" ] || exit 36
rm -f "$STATE" "$SELF" /tmp/privyhub_acceleration_probe_watchdog.pid /tmp/privyhub_acceleration_probe_firewall_restore.log
exit 0
EOS
chmod 700 "$RESTORE" || fail "restore_script_chmod_failed"

nohup sh -c 'sleep 600; /tmp/privyhub_acceleration_probe_restore.sh' >"$WATCHDOG_LOG" 2>&1 &
WATCHDOG_PID=$!
printf 'WATCHDOG_PID=%s\n' "$WATCHDOG_PID" >> "$STATE" || fail "watchdog_state_write_failed"

uci set firewall.@defaults[0].flow_offloading='0' || fail "disable_flow_failed"
uci set firewall.@defaults[0].flow_offloading_hw='0' || fail "disable_hw_failed"
uci commit firewall || fail "firewall_commit_failed"
/etc/init.d/firewall restart >/tmp/privyhub_acceleration_probe_firewall_disable.log 2>&1 || fail "firewall_restart_failed"
sleep 2

FLOW="$(uci -q get firewall.@defaults[0].flow_offloading 2>/dev/null)"
HW="$(uci -q get firewall.@defaults[0].flow_offloading_hw 2>/dev/null)"
[ "$FLOW" = "0" ] || fail "flow_disable_verification_failed"
[ "$HW" = "0" ] || fail "hw_disable_verification_failed"

if grep -q '^sfhnat ' /proc/modules 2>/dev/null; then SFHNAT="LOADED"; else SFHNAT="NOT_LOADED"; fi

echo "acceleration_setup=OK"
echo "original_flow_offloading=$ORIG_FLOW"
echo "original_flow_offloading_hw=$ORIG_HW"
echo "test_flow_offloading=$FLOW"
echo "test_flow_offloading_hw=$HW"
echo "sfhnat_module=$SFHNAT"
echo "restore_watchdog=ARMED_600_SECONDS"
'''
print('sh -c ' + shlex.quote(script))
PY_REMOTE
}

build_restore_command() {
python3 <<'PY_REMOTE'
import shlex
script = r'''STATE="/tmp/privyhub_acceleration_probe_state"
RESTORE="/tmp/privyhub_acceleration_probe_restore.sh"
WATCHDOG_LOG="/tmp/privyhub_acceleration_probe_watchdog.log"

if [ ! -r "$STATE" ]; then
    FLOW="$(uci -q get firewall.@defaults[0].flow_offloading 2>/dev/null)"
    HW="$(uci -q get firewall.@defaults[0].flow_offloading_hw 2>/dev/null)"
    if [ "$FLOW" = "1" ] && [ "$HW" = "1" ]; then
        echo "acceleration_restore=ALREADY_RESTORED"
        echo "restored_flow_offloading=$FLOW"
        echo "restored_flow_offloading_hw=$HW"
        exit 0
    fi
    echo "acceleration_restore=FAILED:NO_STATE_AND_NOT_ENABLED"
    exit 41
fi

. "$STATE"
[ -z "${WATCHDOG_PID:-}" ] || kill "$WATCHDOG_PID" 2>/dev/null || true
"$RESTORE"
RC=$?
FLOW="$(uci -q get firewall.@defaults[0].flow_offloading 2>/dev/null)"
HW="$(uci -q get firewall.@defaults[0].flow_offloading_hw 2>/dev/null)"
rm -f "$WATCHDOG_LOG" /tmp/privyhub_acceleration_probe_firewall_disable.log

if [ "$RC" -ne 0 ]; then
    echo "acceleration_restore=FAILED:$RC"
    exit "$RC"
fi

echo "acceleration_restore=OK"
echo "restored_flow_offloading=$FLOW"
echo "restored_flow_offloading_hw=$HW"
'''
print('sh -c ' + shlex.quote(script))
PY_REMOTE
}

restore_acceleration() {
    if [ "$ACCEL_ARMED" -ne 1 ]; then return 0; fi
    echo
    echo "=== OPAL ACCELERATION RESTORE ==="
    RESTORE_CMD="$(build_restore_command)"
    RESTORE_OUT="$(ssh_router "$RESTORE_CMD")"
    RC=$?
    printf '%s\n' "$RESTORE_OUT"
    if [ "$RC" -eq 0 ] && printf '%s\n' "$RESTORE_OUT" | grep -Eq '^acceleration_restore=(OK|ALREADY_RESTORED)'; then
        ACCEL_ARMED=0
        return 0
    fi
    echo "PROBE_FAILED: explicit acceleration restore did not verify"
    echo "A router-side 600-second restore watchdog was armed before the test."
    return 1
}

on_interrupt() {
    echo
    echo "PROBE_INTERRUPTED"
    restore_acceleration || true
    rm -f "$KNOWN_HOSTS"
    trap - EXIT
    exit 130
}

on_exit() {
    if [ "$ACCEL_ARMED" -eq 1 ]; then restore_acceleration || true; fi
    rm -f "$KNOWN_HOSTS"
}

trap on_interrupt INT TERM
trap on_exit EXIT

DISABLE_CMD="$(build_disable_command)"
echo "=== OPAL ACCELERATION-OFF SETUP ==="
DISABLE_OUT="$(ssh_router "$DISABLE_CMD")"
DISABLE_RC=$?
printf '%s\n' "$DISABLE_OUT"
if [ "$DISABLE_RC" -ne 0 ] || ! printf '%s\n' "$DISABLE_OUT" | grep -q '^acceleration_setup=OK'; then
    echo "PROBE_FAILED: acceleration-off setup failed"
    exit 1
fi
ACCEL_ARMED=1

echo
echo "=== D081 ACCELERATION-OFF D080 REPEAT ==="
bash "$D080_RUNNER"
PROBE_RC=$?

restore_acceleration
RESTORE_RC=$?

trap - EXIT INT TERM
rm -f "$KNOWN_HOSTS"

echo
echo "=== D081 FINAL STATUS ==="
echo "d080_probe_exit_code=$PROBE_RC"
echo "acceleration_restore_exit_code=$RESTORE_RC"
if [ "$RESTORE_RC" -ne 0 ]; then
    echo "d081_result=RESTORE_NOT_EXPLICITLY_VERIFIED"
    exit 1
fi
if [ "$PROBE_RC" -ne 0 ]; then
    echo "d081_result=D080_REPEAT_FAILED"
    exit "$PROBE_RC"
fi
echo "d081_result=COMPLETED_AND_RESTORED"
exit 0
