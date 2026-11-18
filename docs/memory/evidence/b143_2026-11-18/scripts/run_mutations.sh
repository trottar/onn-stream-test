#!/bin/bash
# Queue AX: the mutations — each a copy of the work copy (or of the board's tree) with one change, the suite that must
# catch it run once; FAIL expected. usage: run_mutations.sh <work copy> <repo> <out file> <board repo> <scratch>
W="$1"; REPO="$2"; OUT="$3"; BOARD="$4"; SCR="$5"
export H7_GIT_REPO="$REPO"
: > "$OUT"
mutate() {   # name, file, python replacement (old, new), test target
  local name="$1" file="$2" old="$3" new="$4" target="$5"
  local M="$SCR/mut_$name"; rm -rf "$M"; cp -r "$W" "$M"
  python3 - "$M/$file" "$old" "$new" <<'PY'
import sys; from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text(); assert s.count(sys.argv[2]) == 1, "mutation anchor"; p.write_text(s.replace(sys.argv[2], sys.argv[3]))
PY
  r=$( (cd "$M" && timeout 1800 python3 -m unittest $target 2>&1) | grep -E "^Ran|^OK|^FAILED" | tr '\n' ' ')
  echo "$name ($file): $r" >> "$OUT"
  rm -rf "$M"
}
mutate b143_no_arm companion/party_minigame.py "        if callable(arm):
            arm(pid)

    @staticmethod
    def _arm_banner" "        if False:
            arm(pid)

    @staticmethod
    def _arm_banner" "discover -s tests/b143_party_audio_switch -p test_b143.py -k AcrossSwitches"
mutate b143_any_pid companion/native_session_io.py "if armed is not None and armed == int(process_id) and last is not None:" "if last is not None:" "discover -s tests/b143_party_audio_switch -p test_b143.py -k UsersStart"
mutate b144_no_arm companion/party_minigame.py "        arm = getattr(type(ns), \"party_banner_next\", None) and getattr(ns, \"party_banner_next\", None)
        if callable(arm):" "        arm = None
        if callable(arm):" "discover -s tests/b144_party_practice_banner -p test_b144.py -k EncoderCommands"
mutate b144_always companion/native_stream.py "if getattr(self, \"_party_banner_on\", False):" "if True:" "discover -s tests/b144_party_practice_banner -p test_b144.py -k EncoderCommands"
mutate b145_hold_off_in_practice companion/party_minigame.py "        if not go[\"practice\"]:                              # B145: held through a practice too, until a real go
            self._hold_select(mg, False)" "        if True:
            self._hold_select(mg, False)" "discover -s tests/b145_party_small_things"
# the board: my file mutated in a copy of the board's tree, the check run in its scratch
bmut() {   # name, old, new
  local name="$1" old="$2" new="$3"
  local B="$SCR/bmut_$name"; rm -rf "$B"; mkdir -p "$B"
  git -C "$BOARD" archive HEAD | tar -x -C "$B"
  cp "$BOARD/minigames/hub_minigame.gd" "$BOARD/checks/hub_minigame_check.gd" "$B/" 2>/dev/null
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
bmut no_show_at_handover "			elif state == \"playing\" and practising and not behind:
				# a practice handed over: the load screen again behind it, every mark clear (the gate keeps the
				# pads from it while the hub's game is on), so the way back lands on it
				stage.show_minigame_loading(str(titles.get(id, \"\")), players)
				behind = true
				phase = \"\"
			elif state == \"playing\" and shown and not practising:" "			elif state == \"playing\" and shown:"
bmut no_go_line "					print(\"PrivyParty: hub mini game: %s\" % choice)" "					pass"
bmut no_gate_in_practice "					if gate == null:
						gate = PadGate.new()" "					if gate == null and not practising:
						gate = PadGate.new()"
