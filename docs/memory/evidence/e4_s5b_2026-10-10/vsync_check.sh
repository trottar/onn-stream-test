#!/usr/bin/env bash
# E4-S5B, after the runs (diagnostic, reported; changes no verdict): does the bench's sink (-f null) hide the drops?
# A synthetic 60-fps source (lavfi testsrc2, 160x120, 60 s of content, generated as fast as it can) is written at an
# output rate of 59 / 59.94 (what the encoder adopts from a bad probe) to -f null with ffmpeg's default frame-rate mode
# (the bench's case) and with -fps_mode cfr (constant frame rate: what the default mode picks for the companion's rtp
# muxer). No window, no device, no network. Prints frames / dup / drop per case.
for R in 59 59.94 60; do
  for M in default cfr; do
    X=(); [ "$M" = cfr ] && X=(-fps_mode cfr)
    L=$(ffmpeg -hide_banner -nostdin -f lavfi -i testsrc2=rate=60:size=160x120 -t 60 -r "$R" "${X[@]}" -f null - 2>&1 | tr '\r' '\n' | grep -a 'frame=' | tail -1)
    echo "output_rate=$R mode=$M :: $L"
  done
done
