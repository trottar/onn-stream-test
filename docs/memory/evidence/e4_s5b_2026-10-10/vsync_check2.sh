#!/usr/bin/env bash
# E4-S5B diagnostic, second form (vsync_check.sh used an explicit -r, which is the FIX's case, not the fault's): the
# fault is a stream whose declared rate (the probed tbr) is 59 / 59.94 while frames arrive at 60/s, with NO output -r
# (the encoder adopts the declared rate). Emulated: lavfi testsrc2 declared at R, timestamps rewritten to 60/s
# (setpts=N/60/TB), 60 s of output, no -r; -f null with ffmpeg's default frame-rate mode (the bench's sink) vs
# -fps_mode cfr (the mode the default picks for the companion's rtp muxer); and, for the fix, the same with -r 60.
for R in 59 59.94 60; do
  for M in default cfr fix_r60; do
    X=(); [ "$M" = cfr ] && X=(-fps_mode cfr); [ "$M" = fix_r60 ] && X=(-r 60)
    L=$(ffmpeg -hide_banner -nostdin -f lavfi -i "testsrc2=rate=$R:size=160x120,setpts=N/60/TB" -t 60 "${X[@]}" -f null - 2>&1 | tr '\r' '\n' | grep -a 'frame=' | tail -1)
    echo "declared_rate=$R mode=$M :: $L"
  done
done
