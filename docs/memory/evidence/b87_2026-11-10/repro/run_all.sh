#!/bin/bash
# B87's reproduction set (made-up names; the synthetic ROM; temp folders under ~/.cache; the companion's display)
R=/home/privyhub/Projects/onn-stream-test; S=$R/docs/memory/evidence/b87_2026-11-10/repro/b87_repro.py
pid=$(systemctl --user show -p MainPID --value privyhub-companion)
export $(tr '\0' '\n' < /proc/$pid/environ | grep '^DISPLAY=\|^XAUTHORITY=' | xargs)
run() { W=$(mktemp -d -p ~/.cache b87run_XXXX); echo "# $1"; timeout 60 python3 -I -B $S "$R" "$W" "${@:2}"; }
run "a plain name, the file where the hub stages it" --window 6 --v64 --name "Made Up Plain (USA)"
run "a dot in the name, the file where the hub stages it today (the stem): the HOME-12R signature" --window 6 --v64 --name "Made Up (USA) v1.1"
run "the same title, the file under RetroArch's own name (one more suffix stripped)" --window 6 --v64 --name "Made Up (USA) v1.1" --cht-name "Made Up (USA) v1"
run "two dots: RetroArch's name" --window 6 --v64 --name "Ab.Cd.Ef" --cht-name "Ab.Cd"
for i in 1 2 3 4 5; do run "the first cheat pulse: probe every 0.25 s from PLAYING (677 entries), run $i" --window 15 --v64 --name "Made Up" --entries 677 --probe; done
for i in 1 2 3; do run "the hub's order today: one pulse at PLAYING with a 1-s window, run $i" --window 6 --name "Made Up"; done
echo "# RetroArch processes left: $(pgrep -fc 'RetroArch-Linux-x86_64.AppImage' || true)"
