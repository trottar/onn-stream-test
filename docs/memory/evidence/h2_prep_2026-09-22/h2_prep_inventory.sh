#!/usr/bin/env bash
# H2-PREP: read-only inventory of the host display / session / boot path.
#
# Every command here READS. Nothing is written outside the output file, no
# sudo, no `xrandr --output`, no file under /etc touched, no unit enabled,
# no reboot. Run it with the monitor still attached; run it again after the
# DisplayPort dummy plug is in and diff the two.
#
#   ./h2_prep_inventory.sh > raw.txt 2>&1
#
# Redact with h2_prep_redact.py before anything is copied into a memory or
# evidence file: this raw output contains the EDID (which carries the
# monitor's serial), the root filesystem UUID and socket addresses.

set -u
export DISPLAY="${DISPLAY:-:0}"

section() { printf '\n===== %s =====\n' "$1"; }

section "1a session type"
echo "XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-<unset>}"
echo "DISPLAY=${DISPLAY:-<unset>}"
echo "WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-<unset>}"
loginctl list-sessions
for s in $(loginctl list-sessions --no-legend 2>/dev/null | awk '{print $1}'); do
  echo "--- session $s ---"
  loginctl show-session "$s" -p Type -p Class -p Desktop -p State -p Active -p Service -p Display
done

section "1b display manager"
systemctl status display-manager --no-pager 2>&1 | head -12
ps -eo user,pid,comm,args | grep -E '(^|/)(Xorg|Xwayland|lightdm|gdm3|sddm|xfce4-session|gnome-shell|kwin_x11)' | grep -v grep

section "1c autologin"
ls -l /etc/lightdm/ 2>&1
grep -rniE '^[^#]*autologin' /etc/lightdm/ 2>&1 || echo "(no uncommented autologin directive)"

section "2 outputs and modes"
xrandr --listmonitors
xrandr
for c in /sys/class/drm/card*-*/; do
  printf '%-40s status=%s enabled=%s\n' "$c" "$(cat "$c/status" 2>/dev/null)" "$(cat "$c/enabled" 2>/dev/null)"
done
for c in /sys/class/drm/card*-DP-*/; do echo "## $c modes"; tr '\n' ' ' < "$c/modes" 2>/dev/null; echo; done
xrandr --verbose | sed -n '1,80p'

section "3a gpu and cmdline"
lspci -k | grep -A3 -iE 'VGA|Display controller'
/sbin/modinfo amdgpu 2>&1 | grep -iE '^(version|vermagic):'
cat /proc/cmdline
uname -r

section "3b xorg configuration"
ls -l /etc/X11/xorg.conf /etc/X11/xorg.conf.d/ /usr/share/X11/xorg.conf.d/ 2>&1
grep -rniE 'Section *"(Monitor|Screen|Device|ServerLayout|ServerFlags)"' \
  /etc/X11/ /usr/share/X11/xorg.conf.d/ 2>&1 || echo "(no Monitor/Screen/Device section anywhere)"
cat /usr/share/X11/xorg.conf.d/10-amdgpu.conf 2>&1
grep -iE 'Using system config|loading driver|no monitor section|initial mode|no screens found' \
  /var/log/Xorg.0.log 2>&1 | head -20

section "3c desktop display persistence"
ls -l ~/.config/monitors.xml 2>&1
cat ~/.config/xfce4/xfconf/xfce-perchannel-xml/displays.xml 2>&1
xset q | grep -A4 'DPMS (Display'
xset q | sed -n '/Screen Saver/,+2p'
cat ~/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-power-manager.xml 2>&1

section "4 boot and login"
systemctl list-unit-files --state=enabled --no-pager |
  grep -iE 'ssh|display|getty|companion|privyhub|retroarch|lightdm|network'
systemctl --user list-unit-files --state=enabled --no-pager
ls -l ~/.config/autostart/ 2>&1
ls /etc/xdg/autostart/ 2>&1
crontab -l 2>&1
loginctl show-user "$USER" -p Linger

section "5 ssh console"
systemctl list-unit-files --no-pager | grep -iE '^(ssh|sshd)' || echo "(no ssh server unit file)"
for u in ssh sshd ssh.socket; do printf '%-12s %s\n' "$u" "$(systemctl is-enabled $u 2>&1)"; done
ls -l /usr/sbin/sshd 2>&1
ss -tln | awk 'NR>1 {n=split($4,a,":"); print a[n]}' | sort -un | tr '\n' ' '; echo
command -v ssh && ssh -V 2>&1

section "6 capture geometry"
curl -s "localhost:8765/plugins/games/native-stream-status" 2>&1 | head -c 4000; echo
grep -aoE '\-f x11grab.*' logs/games/native_video_alpha.log 2>/dev/null | tail -1
command -v xdotool && xdotool --version 2>&1

section "7 adb"
adb devices
ls -l ~/.android/adbkey ~/.android/adbkey.pub 2>&1
