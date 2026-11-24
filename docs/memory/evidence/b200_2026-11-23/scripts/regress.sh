#!/bin/bash
# Queue BM: T90's and T91's label and learn again on copies (the title's add_game folder, its verdicts, the rules
# folder — read only, copied to <scratch>), the tree's code; each verdict file compared with the committed one.
# usage: regress.sh <repo> <work copy> <scratch> <code...>
R="$1"; W="$2"; S="$3"; shift 3
for C in "$@"; do
  rm -rf "$S/$C"; mkdir -p "$S/$C/home" "$S/$C/ev" "$S/$C/tmp"
  cp -a "$HOME/privyhub_h7/add_game/$C" "$S/$C/home/"; cp -a "$R/docs/memory/evidence/add_game/$C" "$S/$C/ev/"
  cp -a "$HOME/privyhub_h7/rules" "$S/$C/rules"
  ( export PRIVYHUB_ADD_GAME_HOME="$S/$C/home" PRIVYHUB_ADD_GAME_EVIDENCE="$S/$C/ev" PRIVYHUB_H7_RULES="$S/$C/rules" \
           PRIVYHUB_ADD_GAME_ASK="$S/$C/ask" PARTY_ADD_GAME_CAPTURE=nocapture:none TMPDIR="$S/$C/tmp"
    cd "$W" && for st in label learn; do echo "$C $st: $(python3 tools/party_add_game.py $st $C 2>&1 | head -1)"; done )
  for st in label learn; do
    if cmp -s "$R/docs/memory/evidence/add_game/$C/$st.json" "$S/$C/ev/$C/$st.json"; then echo "$C $st.json: the same bytes"
    else echo "$C $st.json: DIFFERS"; fi
  done
done
