#!/bin/bash
# C5-M4 -- the measurement source config, for Tekken 3 only, outside the adopted files.
#   c5_m4_source.sh set <1x|2x|4x|8x|...>  write the game-specific override "Tekken 3 (USA).cfg"
#       (RetroArch fullscreen = a 1920x1080 window on the headless display; the frame counter in the
#       window title with the OSD font and widgets off) and the game-specific core options
#       "Tekken 3 (USA).opt" = the base "Beetle PSX HW.opt" with beetle_psx_hw_internal_resolution
#       set. Neither file existed before this task (prestate_sha256.txt); the base files are only read.
#   c5_m4_source.sh window720 <scale>  as set, but the override keeps today's window (879x720):
#       only the frame counter keys (for T's re-capture at 1x).
#   c5_m4_source.sh clear  delete both game-specific files.
#   c5_m4_source.sh show   print what is in force.
set -u
D="$HOME/.config/retroarch/config/Beetle PSX HW"
BASE="$D/Beetle PSX HW.opt"; OPT="$D/Tekken 3 (USA).opt"; CFG="$D/Tekken 3 (USA).cfg"
counter() { printf 'fps_show = "true"\nframecount_show = "true"\nmenu_enable_widgets = "false"\nvideo_font_enable = "false"\n'; }
case "$1" in
  set|window720)
    [ "$1" = set ] && printf 'video_fullscreen = "true"\nvideo_windowed_fullscreen = "true"\n' > "$CFG" || : > "$CFG"
    counter >> "$CFG"
    sed "s/^beetle_psx_hw_internal_resolution = .*/beetle_psx_hw_internal_resolution = \"$2\"/" "$BASE" > "$OPT"
    grep -q "^beetle_psx_hw_internal_resolution = \"$2\"$" "$OPT" || { echo "FAILED to set $2"; exit 1; } ;;
  clear) rm -f "$OPT" "$CFG" ;;
  show) ls -la "$D"; [ -f "$CFG" ] && cat "$CFG"; [ -f "$OPT" ] && grep internal_resolution "$OPT" ;;
esac
