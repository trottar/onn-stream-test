#!/bin/bash
# C5-M4A V5 -- the measurement-only game override for Tekken 3: RetroArch's frame counter in the window title
# (fps_show / framecount_show) with the OSD font and widgets off, so nothing is drawn on the picture. It stacks
# on the adopted core override (RetroArch appends core, then game overrides); it sets nothing about the window.
#   c5_m4a_counter.sh set | clear | show
set -u
F="$HOME/.config/retroarch/config/Beetle PSX HW/Tekken 3 (USA).cfg"
case "$1" in
  set) printf 'fps_show = "true"\nframecount_show = "true"\nmenu_enable_widgets = "false"\nvideo_font_enable = "false"\n' > "$F" ;;
  clear) rm -f "$F" ;;
  show) ls -la "$(dirname "$F")"; [ -f "$F" ] && cat "$F" ;;
esac
