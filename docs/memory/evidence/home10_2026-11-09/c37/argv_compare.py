#!/usr/bin/env python3
"""HOME-10 C37 host half: the live argv carries -draw_mouse 0 once, before -window_id; with that pair and the adopted
E4-S5 output -r taken out it equals C5-M1's pinned pre-B70 argv (tools/test_c5_m1_profile_selector.py)."""
import sys
live = [l for l in open(sys.argv[1]).read().splitlines() if l and not l.startswith("#")][0].split()
pinned = ("/usr/bin/ffmpeg -hide_banner -loglevel info -nostdin -vaapi_device /dev/dri/renderD128 -f x11grab -framerate 60 -window_id <id> -i :0 -vf scale=1280:720:force_original_aspect_ratio=decrease:flags=fast_bilinear,pad=1280:720:(ow-iw)/2:(oh-ih)/2:black,format=nv12,hwupload -an -c:v h264_vaapi -profile:v high -b:v 7000k -maxrate 7000k -bufsize 7000k -max_frame_size 90000 -g 15 -bf 0 -payload_type 96 -f rtp rtp://127.0.0.1:48110?pkt_size=1200").split()
i = live.index("-draw_mouse")
print("draw_mouse", live[i:i + 2], "count", live.count("-draw_mouse"), "before -window_id", live[i + 2] == "-window_id")
rest = live[:i] + live[i + 2:]
j = rest.index("-r"); print("output -r pair (line 5, E4-S5 output_rate):", rest[j:j + 2])
print("the rest = C5-M1's pinned pre-B70 argv:", rest[:j] + rest[j + 2:] == pinned)
