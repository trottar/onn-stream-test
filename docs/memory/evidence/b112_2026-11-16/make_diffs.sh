#!/bin/bash
# B110 / B112: the two diffs in order. The B110-only state = the tree with B112's own edits undone in a copy (the exact
# strings B112 added, removed again; h7_minigame.py = HEAD's). Then HEAD → B110 → now in a throwaway git repo; both
# applied in order on `git archive HEAD` and compared with the tree.
set -e
R=/home/privyhub/Projects/onn-stream-test; E=$R/docs/memory/evidence
T=$(mktemp -d -p ~/.cache/b_q28ap_tmp state_XXXX); cp -r $R/companion $R/tests $T/
cd $T && python3 - <<'PY'
from pathlib import Path
p=Path("companion/party_minigame.py"); s=p.read_text()
for new, old in (('''                runner.start("1", "", bench=not self.stream_needed)''','''                runner.start("1")'''),
                 ('''    def start(self, token: str, seats_text: str, bench: bool = False) -> dict:
        self.stream_needed = not bench           # B112: with the bench word, the watcher runs with no stream
        if not party.active(self.emu):''','''    def start(self, token: str, seats_text: str) -> dict:
        if not party.active(self.emu):''')):
    assert s.count(new)==1; s=s.replace(new, old)
p.write_text(s)
g=Path("companion/plugins/games.py"); s=g.read_text()
a=s.index("            # B112: ?bench=1 — no stream check"); b=s.index("            return self._h7_minigame_runner().start(self._first(q, \"load\"), self._first(q, \"keep\"))\n", a); s=s[:a]+s[b:]
a=s.index("        # B112: the running game's pause released with no stream"); end="            return self._h7_minigame_runner().bench_release(client_ip)\n"; b=s.index(end, a)+len(end); s=s[:a]+s[b:]
old='''            q = parse_qs(raw_query)
            bench = False'''
a=s.index(old); b=s.index("            return self._party_minigame_runner().start(self._first(q, \"id\"), self._first(q, \"seats\"), bench=bench)", a)
s=s[:a]+'''            q = parse_qs(raw_query)
            return self._party_minigame_runner().start(self._first(q, "id"), self._first(q, "seats"))'''+s[b+len("            return self._party_minigame_runner().start(self._first(q, \"id\"), self._first(q, \"seats\"), bench=bench)"):]
g.write_text(s)
PY
git -C $R show HEAD:companion/h7_minigame.py > $T/companion/h7_minigame.py
W=$(mktemp -d -p ~/.cache/b_q28ap_tmp diffs_XXXX); cd $W && git init -q . && git -C $R archive HEAD companion tests | tar -x && git add -A && git -c user.email=b@x -c user.name=b commit -qm head
for f in companion/native_session_io.py companion/games/emulator_manager.py companion/plugins/games.py companion/party_minigame.py tests/b110_party_minigame/test_b110.py; do mkdir -p $(dirname $f); cp $T/$f $f; done
git add -N companion/party_minigame.py tests/b110_party_minigame/test_b110.py; git diff > $E/b110_2026-11-16/b110.diff; git add -A && git -c user.email=b@x -c user.name=b commit -qm b110
for f in companion/h7_minigame.py companion/party_minigame.py companion/plugins/games.py tests/b112_no_client_bench/test_b112.py; do mkdir -p $(dirname $f); cp $R/$f $f; done
git add -N tests/b112_no_client_bench/test_b112.py; git diff > $E/b112_2026-11-16/b112.diff
cd $R; git diff --no-index /dev/null tests/b111_party_board/test_b111.py > $E/b111_2026-11-16/b111_test.diff || true
V=$(mktemp -d -p ~/.cache/b_q28ap_tmp apply_XXXX); git archive HEAD companion tests | tar -x -C $V
(cd $V && git init -q . && git apply --check $E/b110_2026-11-16/b110.diff && git apply $E/b110_2026-11-16/b110.diff && git apply --check $E/b112_2026-11-16/b112.diff && git apply $E/b112_2026-11-16/b112.diff && git apply $E/b111_2026-11-16/b111_test.diff)
r=0; for f in companion/native_session_io.py companion/games/emulator_manager.py companion/plugins/games.py companion/party_minigame.py companion/h7_minigame.py tests/b110_party_minigame/test_b110.py tests/b112_no_client_bench/test_b112.py tests/b111_party_board/test_b111.py; do cmp $f $V/$f || r=1; done
echo "applied in order = the tree: $([ $r = 0 ] && echo yes || echo NO)"
rm -rf $T $W $V
