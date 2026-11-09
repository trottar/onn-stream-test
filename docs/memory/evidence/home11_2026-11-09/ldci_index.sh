#!/bin/sh
# HOME-11: T17's RetroArch disk index record (the hub's only .ldci under Beetle PSX's saves): image_index as a number only; no path printed
f=$(find "$HOME" -name '*.ldci' -path '*Beetle PSX*' 2>/dev/null)
n=$(printf '%s\n' "$f" | grep -c .)
printf '%s records %s image_index %s mtime_utc %s\n' "$(date -u +%FT%TZ)" "$n" "$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["image_index"])' "$f")" "$(date -u -r "$f" +%FT%TZ)"
