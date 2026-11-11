# SESSION B — done, 2026-11-11 AI (QUEUE_2026-11-11AI: B94 the win-rule search, B95 a state read as it stands; run 08:25-10:40Z)

- **Baseline:** `0f881ae5` (HOME-12V committed). **Checked first:** only the companion and `privyhub-diag` active;
  `git status --short` empty (the prompt files tracked and unchanged).
- **Not done:** nothing committed or adopted; the companion unchanged (tools and tests only); no companion or keeper
  restart, no stream, no adb, no sudo, no nft; `privyhub-diag` and `~/privyhub_diag/` untouched; nothing fetched; nothing
  written to the drive; nothing deleted; nothing of A's touched; **the user's save states not read, copied, loaded or
  deleted; no real title started.**
- **RetroArch was run by B, headless, on synthetic fixtures only** (B61's form: a PS-X EXE, SNES ROMs and B61's N64 ROM,
  all with no game; temp folders under `~/.cache`; the companion's display; no stream, no pad). **Counted by process
  after every set: 0.** One count read 2: B95's runs were counted while B94's job was running its own RetroArch at the
  same time; the runs were redone one after the other — 0.

## What was found and built

| Item | Found | Built | Tests | Mutations |
| --- | --- | --- | --- | --- |
| **B94** | one read answers ≤ ~21,000 B on all three cores; whole memory: SNES 0.11 s, PS1 2 MiB 1.66 s, N64 4 MiB 3.33 s; **a state loaded paused reads exactly (0 frames, 0 bytes changed, 3 loads equal)**, loaded running then paused PS1 differs in 104 bytes; the state files (RZIP) hold main memory as one block, located only by a planted pattern → the search loads, it does not parse files | `tools/h7_rule_search.py`: labelled states → candidate rules in B93's JSON, three templates (a per-player counter; a level that empties; a single winner field), merged reads, ranked, **"decided" only when a template leaves exactly one**, else the counts and the state that would split them | 10 (×3 green; the read of 3 × 3 loads on 2 MiB 44 s, the search 0.17 s) | 7 / 7 |
| **B95** | B93's load check accepted RetroArch's failure line; a paused RetroArch ignores QUIT (5 s per run); B93 copied the game into its temp folder | `--as-is` / `--seconds 0` (0 frames run, measured), `"none_when"` ("no winner yet" ≠ a tie), B94's single-field rules read, `--runs N` with the agreement ("k of N"; "disagree" never hidden), the load check tightened, `--make-state` written and saved paused, the game read in place, a faster close; the proof's statement in the help and ROADMAP §H7 | 8 new (+ B93's 5 unchanged; ×3 green) | 5 / 5 |

**What the search decides with two states against three (fixture):** begin + one end is **not decided** (both block
templates keep more than one candidate — decoys and zero-padded blocks fit; the single-field template is untestable);
**an end won by the other player decides it** — the planted rule alone. Found on the way: memory that changes with time
(even on a BIOS-less PS1 core) sometimes fits a template by chance when states are saved at different moments — the tool
then answers "not decided", as it should.

**One line for the user:** the hub can now look at your PS1 save states and work out where the game keeps who's winning —
but from "before the fight" and "player 1 won" alone it will very likely say "not sure yet"; one more save of the same
fight where player 2 wins should settle it.

**What I would change (the queue's items were done as written):** the single-winner-field template (c) as written —
any value that differs between a P1 end and a P2 end and is constant at "begin" — also matches every byte of memory that
merely changes over time (about 1,600 addresses on the PS1 fixture); it never decides anything on a real game. A stricter (c) (the end
values must look like a player number: 0/1, 1/2 or 1/2/4…) would make it useful.

## A — H7-P1, the real search and proof on T88's states (unattended: no TV, no stream, nothing asked of the user)

**Inputs:** T88 (a PS1 title; HOME-12V's 2-player test). **Its states by slot (HOME-12V):** slot 3 = **"begin"** (just
before the fight); slot 2 = **"end", player 1 won** (the user: "Player 1 … wins!"); **and any further T88 state the user
made since, with the fact the user gave** (e.g. "slot 1: player 2 won") — taken only from the user's own words in A's
prompt. **The hub's saves are never changed: A copies them into a temp folder and the tools load only the copies.**

### Preconditions

HEAD with queue AI committed and the tree clean (else "YOU, now: commit queue AI first, then send the read line again");
only the companion and `privyhub-diag`; **no game running on the hub** (`curl -s http://127.0.0.1:8765/plugins/games/status`
→ `"active": false`) — RetroArch runs on the hub's display; `/tmp` ≥ 1 GB; outside 04:30-05:30Z.

### The run

```
pid=$(systemctl --user show -p MainPID --value privyhub-companion)
export $(tr '\0' '\n' < /proc/$pid/environ | grep '^DISPLAY=\|^XAUTHORITY=' | xargs)
W=$(mktemp -d -p ~/.cache h7p1_XXXX)                  # off the repo; holds copies only
cp <T88's slot-3 state> $W/begin.state; cp <T88's slot-2 state> $W/end_p1.state   # (+ any further state the user made)
cat > $W/states.json <<EOF
[{"state": "$W/begin.state", "label": "begin", "winner": null},
 {"state": "$W/end_p1.state", "label": "end", "winner": "P1"}]
EOF
python3 tools/h7_rule_search.py --content <T88's game file> --system ps1 --states $W/states.json --time > $W/search.json
```

Rows to record (counts and template letters; memory addresses may be recorded — they are the game's, not an identifier):
the read and search seconds; `unstable_bytes`; per template the count (`a`, `b`, `c` — `c` "not testable" without a P2
end); `decided`; if decided, the rule and its template.

### If one rule is decided — the proof (pre-registered, hashed before the runs)

`python3 -c 'import json;d=json.load(open("'$W'/search.json"));json.dump(d["rule"],open("'$W'/rule.json","w"))'`, then per
state: `python3 tools/h7_minigame_proof.py --content <T88's game file> --system ps1 --state $W/<state> --as-is --runs 3
--rule $W/rule.json`. **Met** when, read as they stand, `begin.state` → `"winner": null` ("no winner yet") **3 of 3**,
`end_p1.state` → **P1 3 of 3**, and any end won by another player → **that player 3 of 3**. Anything else → not met,
the lines recorded.

### If not decided — the count, and one hand step in the user's terms

Record the counts per template and the tool's `would_split`. The reply names the one step that would split it, e.g.
(only if slot 1 holds nothing the user wants — A checks its date first): **"YOU, now: start [T88] from Continue → Load
slot 3, play that fight and let player 2 win, then press Home → SAVE into slot 1. Tell me when it's saved."** — then the
next H7-P1 runs with three states.

### Erasing T88's proof saves

**Only on the user's explicit word in A's prompt, naming the slots** (the user asked at HOME-12V that they be erased
"when you don't need them"); never by default, never before the proof's verdict. Through the hub's own delete for those
slots; the files' absence read back.

### The record

`evidence/H7_P1_<date>.md` + dir: the inputs by slot and fact (T-labels; no title, character name or path); the search's
seconds, counts, decided or not, the rule; the as-is lines (winner, agreement) per state; the verdict (met / not met /
not decided — the step asked); the temp folder's removal or not (A's choice, stated); redact / title checks;
`logs/h7p1_git_status.txt`; nothing committed.

## Files

`evidence/B94_H7_RULE_SEARCH_2026-11-11.md` + `b94_2026-11-11/` (the design + hash, `settle/`, `b94.diff`,
`diffs_apply_in_order.txt`, tests, mutations, scripts, checks, manifest); `evidence/B95_H7_STATE_AS_IS_2026-11-11.md` +
`b95_2026-11-11/` (the design + addendum + hashes, `b95.diff`, tests, mutations, scripts, checks, manifest); patch notes
`patches/B94_H7_RULE_SEARCH.md`, `B95_H7_STATE_AS_IS.md`; code `tools/h7_rule_search.py`, `tests/h7_rule_search/`,
`tools/h7_minigame_proof.py`, `tests/h7_minigame_proof/test_b95_as_is.py`; `docs/ROADMAP.md` §H7 and
`docs/KNOWN_ISSUES.md` (insertions); `logs/b94_git_status.txt`, `logs/b95_git_status.txt`; `handoffs/SESSION_B_STATUS.txt`.
Left (not deleted): `~/.cache/b_q21ai_tmp/` (the settle runs, test temp, a tree check copy).
