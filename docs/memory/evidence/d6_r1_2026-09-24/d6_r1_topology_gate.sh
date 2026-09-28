#!/bin/bash
# D6-R1 topology gate, as B2 checked it. Prints booleans and labels only;
# (stored copy: the one public address literal used for `ip route get` is written <public-ipv4>)
# every address stays in this process's variables.
set -u
DEV=$(ip -4 route show default | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1);exit}}')
GW=$(ip -4 route show default | awk '{print $3; exit}')
echo "default route interface: $DEV"
echo "default routes: $(ip -4 route show default | wc -l)"
echo "interfaces UP (non-loopback): $(ip -br link | awk '$1!="lo" && $2=="UP"{print $1}' | tr '\n' ' ')"
echo "wireless interfaces on host: $(ls /sys/class/net/*/wireless 2>/dev/null | wc -l)"
echo "tunnel interfaces: $(ip -br link | grep -cE '^(tun|wg|tap)')"
case "$DEV" in en*|eth*) echo "default route on wired ethernet: yes";; *) echo "default route on wired ethernet: NO";; esac
ping -c1 -W2 "$GW" >/dev/null 2>&1
GWMAC=$(ip neigh show "$GW" | awk '{print $5; exit}')
OUI=$(echo "$GWMAC" | cut -c1-8 | tr a-f A-F)
# No OUI database on this host: the gateway's OUI is compared with the Opal's
# own wired MAC read over the read-only `ssh opal` alias (both in memory only).
OPALMACS=$(ssh -o BatchMode=yes -o ConnectTimeout=8 opal 'cat /sys/class/net/*/address' 2>/dev/null | cut -c1-8 | tr a-f A-F | sort -u)
echo "gateway OUI equals an OUI of the Opal's own interfaces (read over ssh opal): $(echo "$OPALMACS" | grep -qx "$OUI" && echo yes || echo no)"
OPALADDR=$(ssh -G opal 2>/dev/null | awk '$1=="hostname"{print $2}')
echo "the ssh alias opal is the default gateway: $( [ "$OPALADDR" = "$GW" ] && echo yes || echo no)"
SSHB=$(timeout 4 bash -c "exec 3<>/dev/tcp/$GW/22; head -c 64 <&3" 2>/dev/null | tr -d '\r\n\0' | grep -aoiE 'dropbear[^ ]*' | head -1)
echo "gateway ssh banner: ${SSHB:-none}"
HTTPS=$(curl -skI --max-time 4 "http://$GW/" | grep -i '^server:' | tr -d '\r' | cut -c1-40)
echo "gateway http server header: ${HTTPS:-none}"
DNS=$(timeout 4 getent ahostsv4 example.com >/dev/null 2>&1 && grep -c "^nameserver" /etc/resolv.conf)
python3 - "$GW" <<'PY'
import socket, sys, struct, random
gw = sys.argv[1]
q = struct.pack(">HHHHHH", random.randint(0, 65535), 0x0100, 1, 0, 0, 0) + b"\x07example\x03com\x00\x00\x01\x00\x01"
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(3)
try:
    s.sendto(q, (gw, 53)); d, _ = s.recvfrom(512); print("gateway answers DNS on 53: yes (%d-byte reply)" % len(d))
except Exception as e:
    print("gateway answers DNS on 53: no (%s)" % type(e).__name__)
PY
ONN=$(adb shell ip -4 addr show wlan0 2>/dev/null | awk '/inet /{print $2; exit}')
HOSTNET=$(ip -4 -o addr show dev "$DEV" | awk '{print $4; exit}')
python3 - "$ONN" "$HOSTNET" <<'PY'
import ipaddress, sys
onn, host = sys.argv[1], sys.argv[2]
try:
    o = ipaddress.ip_interface(onn); h = ipaddress.ip_interface(host)
    print(f"host prefix /{h.network.prefixlen}; onn prefix /{o.network.prefixlen}; onn address inside the host's network: {o.ip in h.network}")
except Exception as e:
    print("same-subnet check failed:", type(e).__name__)
PY
echo "onn address on its wireless interface (wlan0): $([ -n "$ONN" ] && echo yes || echo no)"
echo "adb shell answers: $(adb shell echo ok 2>/dev/null | tr -d '\r')"
INET=$(ip -4 route get <public-ipv4> | awk '{for(i=1;i<=NF;i++){if($i=="dev")d=$(i+1); if($i=="via")v=$(i+1)}} END{print d, (v!="")}')
echo "internet route: dev $(echo $INET | cut -d' ' -f1), via the default gateway: $( [ "$(ip -4 route get <public-ipv4> | awk '{for(i=1;i<=NF;i++) if($i=="via") print $(i+1)}')" = "$GW" ] && echo yes || echo no)"
echo "internet reachable: $(curl -s -o /dev/null -w '%{http_code}' --max-time 5 https://example.com)"
echo "stream active: $(curl -s localhost:8765/plugins/games/native-stream-status | python3 -c 'import sys,json;print(json.load(sys.stdin).get("active"))'); game active: $(curl -s localhost:8765/plugins/games/status | python3 -c 'import sys,json;print(json.load(sys.stdin)["active"])')"
