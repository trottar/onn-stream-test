# SESSION B — done, 2026-11-12 AL (QUEUE_2026-11-12AL: B100 a fold not tested is not passed, B101 the timed contest behind PRIVYHUB_H7=1; run 01:00Z-02:03Z)

- **Baseline:** `33d8d2cf` (H7-L1 committed). **Checked first:** only the companion and `privyhub-diag` active;
  `git status --short` empty (the prompt files tracked and unchanged).
- **Not done:** nothing committed or adopted; no companion or keeper restart (B101's routes exist only after one with
  the flag), no stream, no adb, no sudo, no nft, the Opal not touched; `privyhub-diag` and `~/privyhub_diag/` untouched;
  nothing fetched; nothing written to the drive; nothing deleted but B's own scratch under `~/.cache/b_q23al_tmp/`;
  **the kept H7 folder, the rules folder, A's working folders and the user's saves not opened or read; no real title
  started.**
- **RetroArch was run by B, headless, on synthetic fixtures only** (B61's form: B94's PS-X EXE and SNES ROM; temp
  folders under `~/.cache`; the companion's display) — B101's settle and B96-B100's suite. B101's tests use a fake.
  **Counted by process: 0 at the end**; intermediate counts of 2 were the other item's batch's session, running beside it (noted in the files).
- **The client's source was read** (read-only, a delegated study, its key lines checked by B) for what the onn does when
  the hub pauses the game by itself.

## What was found and built

| Item | Found | Built | Tests | Mutations |
| --- | --- | --- | --- | --- |
| **B100** | H7-P3's (b2) "strong" on 1 of 4 folds (3 over the cap) | a fold "not testable" in a template testable on all states is `not_tested`; such a template reads at most "weak", the words say why; H7-P3's shape → "weak", the answer h unchanged; `--accept-loose` against B97: equal where untouched, the difference stated and asserted where touched | 6 new + B96-B98's 46 (52 ×3 green, none skipped) | 4 / 4 |
| **B101** | a state loads into **running** content in ~33 ms (RetroArch's own line) and reads exactly; **10 / 30 / 60 s by the hub's clock = 600 / 1,800 / 3,600 frames** (SNES and PS1, a read every second); the final read 3 frames after "time is up"; bsnes' state folder `bsnes`; **during a stream the onn never reads `paused`; the hold's pause is ended by the hub itself** | `companion/h7_contest.py` + `POST` / `GET /plugins/games/h7-contest` behind `PRIVYHUB_H7=1`: the kept `<game id>.state` loaded through scratch slot 8, armed when the values leave the state's, N s with a read a second, the leader at the clock, `resets_seen`, **`ended: running`**; absent / 0 = today byte for byte | 14 (×3 green; B99's 15, the contract's 5, B90's 10 green) | 10 / 10 (the first batch 9 / 10: a case added) |

**How the contest ends: running.** The onn does not handle a hub-side pause as it handles the hold's: in-stream it
never reads `paused` (the heartbeat reply is discarded; `paused` is read only on the main screen), and the hold's pause
is ended by the hub itself on the next controller packet. A pause the hub kept would leave a frozen picture with no
in-stream way back. So the contest takes its final read at "time is up" (3 frames late) and leaves the game running.

**One line for the user:** with the test switch on, the hub can now start a saved fight for you, time it, and say who
was ahead when the time ran out — the game keeps running after, so you'll press Home yourself to see the moment.

**What I would change (the queue's items were done as written):** (1) **the end is invisible on the TV** — a mini game
needs the onn to show "time's up" (a client change: read the contest's GET, or let the hub's pause be resumed the way
the hold's is); until then the user must be told the moment. (2) A contest **arms on any change** from the state's
values; a game whose bars do not move at a fight's start, or a state saved mid-fight, would never arm or would arm at
once — a rule-file setting ("arm when every value is above 0") would be clearer. (3) The contest's reads and a
watcher's `h7-read` share B99's lock-held read; for one contest at a time that is fine, but the lighter read path from
queue AK's notes would make both cheaper.

## A — H7-L2, two timed contests on T88 (attended, ~10 min at the TV)

The user with the onn and two pads paired to the onn over Bluetooth, as always; **nothing asked of the user on the
hub**; every message to the user starts "YOU, now:" and is **a complete step** — the screen, the entry, the button —
naming **only choices the onn will offer**, read from the hub at stage 1. T88 = HOME-12V's 2-player PS1 title. **T88 has
no Continue** (its slots 1-3 were erased at H7-P3) — check it, don't assume it.

### Stage 1 — unattended

1. **Preconditions:** HEAD with queue AL committed and the tree clean (else "YOU, now: commit queue AL first"); only the
   companion and `privyhub-diag`; no game running (`curl -s http://127.0.0.1:8765/plugins/games/status` →
   `"active": false`); outside 04:30-05:30Z; eighteen `PRIVYHUB_` lines, `--check` ok.
2. **The bench flag for the sitting only:** `evidence/b99_2026-11-11/b99-h7-live-read.conf` exactly as B wrote it →
   `~/.config/systemd/user/privyhub-companion.service.d/`; `systemctl --user daemon-reload`;
   `systemctl --user restart privyhub-companion`; its MainPID owns 8765; **nineteen** lines (`--check` not ok on the
   environ only — the bench flag, named).
3. **The mini game in place:** `mkdir -p ~/privyhub_h7/rules`; T88's kept `rule.json` →
   `~/privyhub_h7/rules/<T88's hub id>.json` and T88's kept **"begin"** state → `~/privyhub_h7/rules/<T88's hub id>.state`
   (each copy's sha256 = the kept file's; the id from the hub's own library, never written in a record).
4. **Both routes:** `curl -s http://127.0.0.1:8765/plugins/games/h7-read` → `{"ok": true, "running": false}`;
   `curl -s http://127.0.0.1:8765/plugins/games/h7-contest` → `{"ok": true, "contest": null}`.
5. **What the onn will offer, from the hub's own state** (written into the lines below before stage 2):
   `curl -s "http://127.0.0.1:8765/plugins/games/details?id=<T88's hub id>"` → `continue_available` (expected **false**);
   the PlayStation entry's exact name as the onn lists it (`curl -s http://127.0.0.1:8765/plugins/games/systems`, the
   `games_system_ps1` node's name) and T88's place in that list (`games?system=ps1`'s order). If `continue_available` is
   true the start box also offers Continue — the line below still says Start Fresh.
6. **Before:** T88's slot files and every other game's saves (count and sha256, as H7-P3's close); the stream marks
   (bitrate rows, recovery log, `launch_orphaned`) as H7-L1's.
7. **Watchers (read-only, once a second):** H7-L1's `h7-read` watcher, and
   `while :; do printf '%s ' "$(date -u +%FT%T.%3NZ)"; curl -s -m 2 http://127.0.0.1:8765/plugins/games/h7-contest; echo; sleep 1; done >> $W/h7_contest_watch.txt`.
8. **Pre-registration hashed** (below) before stage 2.

### Stage 2 — the user (the lines, filled in at stage 1)

- **"YOU, now: on the onn's PrivyHub home, open Games, then [the PlayStation entry's exact name]. Move to [T88's tile —
  its place in that list] and press OK. In the box that opens choose 'Launch on Companion' and press OK. In the box
  'Start [title]' choose 'Start Fresh' and press OK. When the game's picture shows with 'Hold any button to join' at the
  bottom, hold A on the first pad for a second until 'P1 joined' shows, then hold A on the second pad
  until Player 2 has joined. Then tell me 'ready' — any screen of the game is fine."**
- A starts contest 1: `curl -s -X POST "http://127.0.0.1:8765/plugins/games/h7-contest?seconds=30"` → `"contest":
  "started"` (the saved fight appears on the TV within a second). **"YOU, now: the saved fight is on the TV — both of you
  play it. Keep playing until I write 'time'."**
- When the watcher shows `"state": "done"`, at once: **"YOU, now: time — press Home on the first pad now (the bar RESUME
  PLAYING · SAVE · LOAD · END appears), then tell me in one line who is ahead and roughly how full each bar is."**
- **"YOU, now: press Left once (onto RESUME PLAYING) and then OK. When 'Hold any button to join' shows, hold A on the
  first pad until 'P1 joined', then hold A on the second pad until Player 2 has joined. Then tell me 'ready'."** → contest 2,
  the same lines.

**Pre-registered (hashed before stage 2):** in both contests **the hub's `winner` is the user's leader** (`null` / "no
winner yet" only if the user says "even"); `armed_after_s` and the samples recorded; if the user's line differs, the
`h7-read` rows between the clock's end and the user's Home are set beside it (a lead changing in those seconds is
recorded as such — the cell stays "not met as worded"); **the stream's rows as a normal session's** (no stall, no
orphan, no recovery row caused by the contests or the reads); **T88's slots and every other game's saves before =
after** (the contest touches none). All met → **MET**.

### The close

Watchers stopped; the drop-in removed; `systemctl --user daemon-reload`; the companion restarted (MainPID owns 8765);
**eighteen** lines, `--check` ok; `h7-read` → 400 "Unknown Games plugin action: h7-read" and `h7-contest` → 400
"Unknown Games plugin action: h7-contest" (both routes gone). The rules folder kept (off the repo; nothing deleted).

### The record

`evidence/H7_L2_<date>.md` + `h7l2_<date>/` (`pre/`: HEAD, units, the drop-in's hash, nineteen lines, the copies'
hashes, `continue_available`, the routes' first answers, the saves before; `run/`: the two contest answers (winner,
values, `armed_after_s`, samples, `resets_seen`, `ended`), `h7_contests.jsonl`'s rows, the watchers, the table —
contest | the hub's winner and values at the clock | the user's line (verbatim, a character replaced by its label) |
met; the stream rows' summary; `close/`; `preregistration.md` + `.sha256`; title, redact and cheat-name checks;
`manifest.sha256`); `logs/h7l2_git_status.txt`. No title, character name, cheat name, serial, game id or path; nothing
committed.

## Files

`evidence/B100_H7_UNTESTED_FOLD_2026-11-12.md` + `b100_2026-11-12/`; `evidence/B101_H7_TIMED_CONTEST_2026-11-12.md` +
`b101_2026-11-12/` (each: the design (+ addendum) + hashes, the diff, tests ×3, mutations, scripts,
`sha256_before_after.txt`, redact / title / cheat-name checks (0 FAILS each), manifest; B101 also `settle/`); patch notes `patches/B100_H7_UNTESTED_FOLD.md`,
`B101_H7_TIMED_CONTEST.md`; code `tools/h7_rule_search.py`, `tests/h7_rule_search/test_b100_untested_fold.py` (new),
`companion/h7_contest.py` (new), `companion/plugins/games.py`, `tests/b101_h7_contest/` (new); `docs/ROADMAP.md` §H7 and
`docs/KNOWN_ISSUES.md` (insertions); `logs/b100_git_status.txt`, `logs/b101_git_status.txt`;
`handoffs/SESSION_B_STATUS.txt`. Left (not deleted): `~/.cache/b_q23al_tmp/`, `/tmp/b_q24al_b100/`, `/tmp/b_q24al_b101/`
(snapshots: `companion/`, `tools/`, `tests/`, `PrivyHub/` only).

Written last, 2026-11-12T02:03:57Z, after the status line, the logs and both manifests.
