#!/bin/bash
# C5-M4A: a recursive sha256 listing of ~/.config/retroarch (paths relative to it), sorted. usage: c5_m4a_listing.sh <out>
OUT=$(realpath -m "$1"); cd "$HOME/.config/retroarch" && find . -type f -print0 | sort -z | xargs -0 sha256sum > "$OUT"
