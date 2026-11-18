#!/bin/bash
# Queue AY: the mutations — each one change in a copy (of the work copy, or of the board's tree), the suite or check
# that must catch it run once; FAIL expected. usage: run_mutations.sh <work copy> <repo> <out file> <board repo> <scratch>
W="$1"; REPO="$2"; OUT="$3"; BOARD="$4"; SCR="$5"
export H7_GIT_REPO="$REPO"
: > "$OUT"
mutate() {   # name, file, old, new, unittest target
  local name="$1" file="$2" old="$3" new="$4" target="$5"
  local M="$SCR/mut_$name"; rm -rf "$M"; cp -r "$W" "$M"
  python3 - "$M/$file" "$old" "$new" <<'PY'
import sys; from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text(); assert s.count(sys.argv[2]) == 1, "mutation anchor"; p.write_text(s.replace(sys.argv[2], sys.argv[3]))
PY
  r=$( (cd "$M" && env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO timeout 1800 python3 -m unittest $target 2>&1) | grep -E "^Ran|^OK|^FAILED" | tr '\n' ' ')
  echo "$name ($file): $r" >> "$OUT"
  rm -rf "$M"
}
mutate b147_old_band companion/native_stream.py "y=h*5/100+10:box=1:boxcolor=black@0.72:boxborderw=10|16|10|16" "y=(h*56/720-text_h)/2:box=1:boxcolor=black@0.72:boxborderw=14|4096|14|4096" "discover -s tests/b147_party_band_inside"
mutate b148_no_prepare companion/party_session.py "    needed = import_needed(cfg[\"project\"])
    if not needed:" "    needed = import_needed(cfg[\"project\"])
    if True:" "discover -s tests/b148_party_board_prepared"
mutate b148_no_bound companion/party_session.py "        fields[\"rc\"] = proc.wait(timeout=bound)" "        fields[\"rc\"] = proc.wait()" "discover -s tests/b148_party_board_prepared"
mutate b148_import_while_running companion/party_session.py "    if (running or _board_running)(cfg):" "    if False:" "discover -s tests/b148_party_board_prepared"
bmut() {   # name, old, new
  local name="$1" old="$2" new="$3"
  local B="$SCR/bmut_$name"; rm -rf "$B"; mkdir -p "$B"
  git -C "$BOARD" archive HEAD | tar -x -C "$B"
  cp "$BOARD/minigames/hub_minigame.gd" "$B/minigames/hub_minigame.gd"; cp "$BOARD/checks/hub_minigame_check.gd" "$B/checks/hub_minigame_check.gd"
  python3 - "$B/minigames/hub_minigame.gd" "$old" "$new" <<'PY'
import sys; from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text(); assert s.count(sys.argv[2]) == 1, "mutation anchor"; p.write_text(s.replace(sys.argv[2], sys.argv[3]))
PY
  (cd "$B" && git init -q && git add -A && git -c user.name=m -c user.email=m@m commit -qm m)
  r=$(TMPDIR="$SCR" sh "$REPO/docs/memory/evidence/b145_2026-11-18/scripts/run_check.sh" "$B" 1 | tr '\n' ' ' | cut -c1-400)
  echo "board_$name: $r" >> "$OUT"
  rm -rf "$B"
}
bmut no_unseen_branch "				elif went and practices > practices_at_go:" "				elif false:"
bmut no_again_line "					print(\"PrivyParty: hub mini game: load screen again\")
					shown = true" "					shown = true"
