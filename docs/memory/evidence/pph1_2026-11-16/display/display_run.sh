#!/bin/bash
# PP-H1 stage 4, one run: display_run.sh <label> <method> <driver> <vsync on|off> <mist 1|0> <hold seconds>
# The game's own main scene through probe_dark.gd on DISPLAY=:0, 1920x1080, the owner's pictures; Godot's --print-fps;
# samples once a second; closed with F10 (the quit action) to the activated window. Output under runs/<label>/.
label=$1; method=$2; driver=$3; vsync=$4; mist=$5; hold=$6
G=<the tools folder>/Godot_v4.7.2-stable_linux.x86_64
O=<A's working folder>/runs/$label; mkdir -p $O
export DISPLAY=:0 TMPDIR=<A's working folder>/tmp
extra=""; [ "$vsync" = off ] && extra="--disable-vsync --max-fps 0"
cd <the board game's repo>
echo "$G --path . --rendering-method $method --rendering-driver $driver --resolution 1920x1080 --position 0,0 --print-fps $extra -s <probe> -- --content=<pictures> --mist=$mist" > $O/cmd.txt
start=$(date +%s.%N)
$G --path . --rendering-method $method --rendering-driver $driver --resolution 1920x1080 --position 0,0 --print-fps $extra \
   -s <A's working folder>/probe_dark.gd -- --content=<the pictures folder> --mist=$mist > $O/out.txt 2>&1 &
pid=$!
echo "started $(date -u +%Y-%m-%dT%H:%M:%S.%3NZ) pid $pid" > $O/run.txt
# the window
wid=""
for i in $(seq 1 60); do
  wid=$(xdotool search --onlyvisible --pid $pid 2>/dev/null | head -1)
  [ -n "$wid" ] && break
  kill -0 $pid 2>/dev/null || break
  sleep 0.5
done
echo "window after $(echo "$(date +%s.%N)-$start" | bc) s: id ${wid:-none}" >> $O/run.txt
if [ -n "$wid" ]; then
  xwininfo -id $wid | grep -E "Width|Height|Absolute upper-left|Map State" >> $O/run.txt
  xprop -id $wid WM_CLASS _NET_WM_PID >> $O/run.txt
fi
# samples once a second while held
hz=$(getconf CLK_TCK); prev=$(awk '{print $14+$15}' /proc/$pid/stat 2>/dev/null)
echo -e "utc\tgodot_cpu_pct\tgpu_busy_pct\tvram_mb\tgtt_mb\tload1\tcpu_c\tgpu_c\trss_mb" > $O/samples.tsv
for s in $(seq 1 $hold); do
  sleep 1
  kill -0 $pid 2>/dev/null || break
  now=$(awk '{print $14+$15}' /proc/$pid/stat)
  cpu=$(echo "scale=1; ($now-$prev)*100/$hz" | bc); prev=$now
  k10=$(for t in /sys/class/hwmon/hwmon*; do [ "$(cat $t/name)" = k10temp ] && echo $(( $(cat $t/temp1_input)/1000 )); done)
  gpt=$(for t in /sys/class/hwmon/hwmon*; do [ "$(cat $t/name)" = amdgpu ] && echo $(( $(cat $t/temp1_input)/1000 )); done)
  echo -e "$(date -u +%H:%M:%S)\t$cpu\t$(cat /sys/class/drm/card0/device/gpu_busy_percent)\t$(( $(cat /sys/class/drm/card0/device/mem_info_vram_used)/1048576 ))\t$(( $(cat /sys/class/drm/card0/device/mem_info_gtt_used)/1048576 ))\t$(cut -d' ' -f1 /proc/loadavg)\t$k10\t$gpt\t$(( $(awk '/VmRSS/{print $2}' /proc/$pid/status)/1024 ))" >> $O/samples.tsv
done
# the close: F10 (the quit action) to the activated window
if kill -0 $pid 2>/dev/null; then
  c0=$(date +%s.%N)
  if [ -n "$wid" ]; then xdotool windowactivate --sync $wid 2>>$O/run.txt; sleep 0.3; xdotool key F10 2>>$O/run.txt; how="F10 (xdotool key, XTEST) to the activated window"; fi
  for i in $(seq 1 60); do kill -0 $pid 2>/dev/null || break; sleep 0.25; done
  if kill -0 $pid 2>/dev/null; then
    how="$how — did not close in 15 s; ended the plain way (SIGTERM)"; kill -TERM $pid
  fi
  wait $pid; rc=$?
  echo "close: $how; exit code $rc; seconds $(echo "$(date +%s.%N)-$c0" | bc)" >> $O/run.txt
else
  wait $pid; rc=$?
  echo "the process had ended by itself before the close: exit code $rc" >> $O/run.txt
fi
echo "ended $(date -u +%Y-%m-%dT%H:%M:%S.%3NZ); godot processes left $(pgrep -c -f Godot_v4.7.2)" >> $O/run.txt
