#!/bin/bash
# Queue AZ: B151's mutations — each one change in a copy of the work copy, the suites that must catch it run once;
# FAIL expected. usage: run_mutations.sh <work copy> <repo> <out file> <scratch>
W="$1"; REPO="$2"; OUT="$3"; SCR="$4"
export H7_GIT_REPO="$REPO"
: > "$OUT"
mutate() {   # name, file, old, new, suites...
  local name="$1" file="$2" old="$3" new="$4"; shift 4
  local M="$SCR/mut_$name"; rm -rf "$M"; cp -r "$W" "$M"
  python3 - "$M/$file" "$old" "$new" <<'PY'
import sys; from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text(); assert s.count(sys.argv[2]) == 1, "mutation anchor"; p.write_text(s.replace(sys.argv[2], sys.argv[3]))
PY
  if [ $? -ne 0 ]; then echo "$name ($file): ANCHOR MISSING - not run" >> "$OUT"; rm -rf "$M"; return; fi
  for t in "$@"; do
    r=$( (cd "$M" && env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO timeout 1800 python3 -m unittest discover -s "tests/$t" 2>&1) | grep -E "^Ran|^OK|^FAILED|^FAIL:|^ERROR:" | tr '\n' ' ' | cut -c1-600)
    echo "$name ($file) -> $t: $r" >> "$OUT"
  done
  rm -rf "$M"
}
# 1. Start kept as the way out (HEAD's hook)
mutate start_is_the_way_out companion/party_minigame.py \
  '            down = bool(int(buttons) & XUSB_BACK)' '            down = bool(int(buttons) & 0x0010)' \
  b151_party_select_leaves b134_party_practice
# 2. the hook's first state "up" (a Select held across the hand-over counts)
mutate no_seed companion/party_minigame.py \
  '                last[player] = bool(seen(player)) if callable(seen) else False' '                last[player] = False' \
  b151_party_select_leaves
# 3. the route's neutral writes taken as the players' (the record not kept across them)
mutate route_neutral_counts companion/native_session_io.py \
  '            seen.update(kept)' '            pass' \
  b151_party_select_leaves
# 4. the band's old words
mutate old_words companion/native_stream.py \
  'press Select (Share) to go back"' 'press Start to go back"' \
  b151_party_select_leaves b144_party_practice_banner
echo "temp dirs left: $(ls "$TMPDIR" | wc -l)" >> "$OUT"
