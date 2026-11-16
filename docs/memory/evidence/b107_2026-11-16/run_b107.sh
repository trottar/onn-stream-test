#!/bin/bash
# B107: step 19's numbers in scratch copies of the board game's repo (the repo itself read only: `git archive HEAD`, its
# tree clean, + for "as_is" a copy of its git-ignored .godot cache = PP-H1's import). Godot headless; its user data,
# settings and cache folders and the OS temp dir pointed into the scratch folder; the scratch folder removed at the end.
#   as_is      — PP-H1's import, as the 25 checks used it
#   fresh1/2   — a fresh import each (--import), to see whether the import repeats on the hub
#   nocompress — a fresh import with meshes/force_disable_compression=true in that copy's .import only
# Prints numbers only (the copies' paths are replaced by <copy>).
set -u
B=$1; G=$2; OUT=$3; SCRIPT=$(cd "$(dirname "$0")" && pwd)/step19_numbers.gd
S=$(mktemp -d -p ~/.cache/b_q27ao_tmp b107_XXXX)
export XDG_DATA_HOME=$S/xdg/data XDG_CONFIG_HOME=$S/xdg/config XDG_CACHE_HOME=$S/xdg/cache TMPDIR=$S/tmp
mkdir -p $XDG_DATA_HOME $XDG_CONFIG_HOME $XDG_CACHE_HOME $TMPDIR
for v in as_is fresh1 fresh2 nocompress; do
  mkdir -p $S/$v && git -C "$B" archive HEAD | tar -x -C $S/$v
  [ $v = as_is ] && cp -a "$B/.godot" $S/$v/.godot
  [ $v = nocompress ] && sed -i 's/^meshes\/force_disable_compression=false$/meshes\/force_disable_compression=true/' $S/$v/models/template_body.glb.import
  {
    echo "=== $v $(date -u +%FT%TZ)"
    echo "the copy's .import compression line: $(grep force_disable_compression $S/$v/models/template_body.glb.import)"
    if [ $v != as_is ]; then
      t0=$(date +%s.%N); "$G" --headless --path $S/$v --import > $S/$v.import.log 2>&1; rc=$?
      echo "import exit $rc, $(echo "$(date +%s.%N) - $t0" | bc) s"
    fi
    f=$(ls $S/$v/.godot/imported/template_body.glb-*.scn 2>/dev/null | head -1)
    echo "the imported body: $(stat -c %s "$f") bytes, sha256 $(sha256sum "$f" | cut -c1-16)…"
    "$G" --headless --path $S/$v --script "$SCRIPT" 2>&1 | grep -E '^B107|ERROR|SCRIPT ERROR' | sed "s#$S/$v#<copy>#g"
    echo "step 19 itself: $("$G" --headless --path $S/$v --script res://checks/step19_round_bodies.gd 2>&1 | grep -E 'STEP 19 CHECK: (PASS|FAIL)|FAIL:' | tr '\n' ' ')"
  } >> "$OUT"
done
echo "=== scratch folder removed: $(rm -rf $S && [ ! -e $S ] && echo yes)" >> "$OUT"
