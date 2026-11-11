# SESSION B — done, 2026-11-11 AK (QUEUE_2026-11-11AK: B98 the acceptance rule in the search, B99 the live read behind PRIVYHUB_H7=1; run 20:44Z-22:14Z)

- **Baseline:** `6cb4663b` (H7-P3 committed). **Checked first:** only the companion and `privyhub-diag` active;
  `git status --short` empty (the prompt files tracked and unchanged).
- **Not done:** nothing committed or adopted; no companion or keeper restart (B99's flag exists only after one), no
  stream, no adb, no sudo, no nft, the Opal not touched; `privyhub-diag` and `~/privyhub_diag/` untouched; nothing
  fetched; nothing written to the drive; nothing deleted but B's own scratch (test temp folders, work copies, the stopped
  first B98 batch's copy) under `~/.cache/b_q22ak_tmp/`; **the kept H7 folder, A's working folders, the user's saves
  and A's copies not opened or read; no real title started.**
- **RetroArch was run by B, headless, on synthetic fixtures only** (B61's form: B94's PS-X EXE and SNES ROM, B61's N64
  ROM and a store-program variant of it; temp folders under `~/.cache`; the companion's display; no stream, no pad) — in
  B99's settle and B96-B98's suite. B99's tests use a fake RetroArch. **Counted by process: 0 at the end**; intermediate counts of 2 were the other item's batch's session, running beside it (noted in the files).
- **The hub launches a game paused** (seen in the fake's command log: GET_STATUS, GET_STATUS, PAUSE_TOGGLE, GET_STATUS;
  the stream's start resumes it): the read says `paused: true` until the stream starts.

## What was found and built

| Item | Found | Built | Tests | Mutations |
| --- | --- | --- | --- | --- |
| **B98** | H7-P3's (b2) read "strong" with 1 of 4 folds run (its training sets over the cap) | `_verdict`: a strong answer decides only as template a or b, a hinted family, or a hinted set (h); (b2) / (c) under `not_accepted` with the reason in words; `ranking_pick` + count; `--accept-loose` = B97's output byte for byte (checked against B97's commit) | 9 new + B96 / B97's 37 (46 ×3 green, none skipped) | 6 / 6 |
| **B99** | **a read once a second does not disturb the frames** (60 s windows, no reads / reads: SNES 3,603 / 3,600 / 3,603 / 3,600, PS1 3,603 / 3,601 / 3,603 / 3,600 — 60.0 a second in each); an answer takes one frame (median ~16.4 ms, worst 17.7 ms); paused reads answer; status / reads / saves / the hold's pause interleaved: 0 lost, 0 crossed; N64's read answers, no byte order anchored (the synthetic ROM leaves RDRAM empty) | `companion/h7_live_read.py` + the flagged route `GET /plugins/games/h7-read`: the kept rule read from the running game (GET_STATUS + READ_CORE_* only, the manager's lock, bounded 0.6 s, one read per 0.25 s, a row per read); absent / 0 = today byte for byte (the baseline's companion vs this one through the real route) | 15 (×3 green; B90's 10 and the contract's 5 green) | 10 / 10 |

**One line for the user:** the hub can now (with a test switch on) look at the game you're playing on the TV and say
who is ahead, using the rule it learned from your saves — reading it once a second doesn't slow the game at all; the
next step is you playing one fight while it watches.

**What I would change (the queue's items were done as written):** (1) **a fold skipped because its training search was
"not testable" should not count as passed** — H7-P3's (b2) was "strong" on 1 of 4 folds; harmless after B98 for (b2),
but the same gap applies to any template; I would make such a template "weak". (2) **N64:** before an N64 rule search,
a small synthetic N64 ROM whose code actually lands in RDRAM (or a known value the core's boot writes) is needed to pin
the byte order; B61's ROM leaves RDRAM empty. (3) The read holds the manager's lock for ~50 ms; at one read a second
that is invisible, but a mini game that reads faster should get its own lighter path (no lock; per-command sockets
already keep answers apart).

## A — H7-L1, the live read beside the user's own eyes (attended, ~10 min at the TV)

The user with the onn and the pads paired to the onn over Bluetooth, as always; **nothing asked of the user on the
hub**; every message to the user starts "YOU, now:". T88 = HOME-12V's 2-player PS1 title. **The rule:** T88's kept
`rule.json` (H7-P3: P1's and P2's 2-byte level, the larger leads, equal → no winner yet).

### Stage 1 — unattended (before the user is asked)

1. **Preconditions:** HEAD with queue AK committed and the tree clean (else "YOU, now: commit queue AK first"); only the
   companion and `privyhub-diag`; no game running (`curl -s http://127.0.0.1:8765/plugins/games/status` →
   `"active": false`); outside 04:30-05:30Z; eighteen `PRIVYHUB_` lines, `--check` ok.
2. **The bench drop-in for the sitting only:** `evidence/b99_2026-11-11/b99-h7-live-read.conf` exactly as B wrote it →
   `~/.config/systemd/user/privyhub-companion.service.d/b99-h7-live-read.conf`; `systemctl --user daemon-reload`;
   `systemctl --user restart privyhub-companion`; its MainPID owns 8765; **nineteen** `PRIVYHUB_` lines read back
   (`--check` not ok on the environ only — the bench flag, named).
3. **The rule in place:** `mkdir -p ~/privyhub_h7/rules`; T88's kept `rule.json` copied to
   `~/privyhub_h7/rules/<the hub's game id for T88>.json` (the id from the hub's own library; not written in any record);
   the copy's sha256 = the kept file's.
4. `curl -s http://127.0.0.1:8765/plugins/games/h7-read` → `{"ok": true, "running": false}` (recorded).
5. **The watcher (read-only, GET only, once a second):**
   `while :; do printf '%s ' "$(date -u +%FT%T.%3NZ)"; curl -s -m 2 http://127.0.0.1:8765/plugins/games/h7-read; echo; sleep 1; done >> $W/h7_watch.txt`
   (`$W` = A's working folder for H7-L1 under `~/.cache`).

### Stage 2 — the fight (the user)

- **"YOU, now: start [T88] from the list as usual and go into a 2-player fight. Once it starts, don't press anything for
  a few seconds. Tell me 'started'."** → A checks the watcher: the read `"winner": null`, `"reason": "no winner yet"` (or
  equal values) while both bars are untouched.
- **"YOU, now: play. Three times, at moments you pick, press Home to pause and tell me in one line who is ahead and
  roughly how full each bar is (for example 'P1 ahead, P1 about three quarters, P2 about half'). Then resume and keep
  playing."** (A counts the presses to Resume in the Home menu first and says them.) For each pause A sets the user's
  line beside the watcher's rows during that pause (`"paused": true`, the values, the leader).
- **"YOU, now: finish the fight with a knockout and tell me who won."** → the rows at the knockout.

**Pre-registered (hashed before stage 2):** at every pause **the read's leader is the user's leader** (equal values
only if the user says "even"); **the values move the way the bars moved** — between two pauses a bar the user saw drop
reads lower, and the read never names a leader the user did not see; at the knockout the read names the winner. **The
stream's own rows during the sitting** — the adaptive bitrate's rows and the recovery log — read as on a normal session:
no stall, no orphan, no recovery row caused by the reads (`logs/games/h7_reads.jsonl`'s read times against them). All
met → **MET**; any pause wrong → **NOT MET** (the lines recorded, nothing changed).

### The close

The watcher stopped; the drop-in removed; `systemctl --user daemon-reload`; the companion restarted (MainPID owns 8765);
**eighteen** lines, `--check` ok; `curl -s http://127.0.0.1:8765/plugins/games/h7-read` → 400 "Unknown Games plugin
action: h7-read" (the route gone). `~/privyhub_h7/rules/` kept (off the repo; nothing deleted). Nothing running that A
started.

### The record

`evidence/H7_L1_<date>.md` + `h7l1_<date>/` (`pre/`: HEAD, units, the drop-in's hash, nineteen lines, the rule copy's
hash, the first `running: false`; `run/`: `h7_watch.txt` (values and leaders only), `h7_reads.jsonl`'s rows for the
sitting, the table — moment | the user's line (verbatim, a character replaced by its label) | the read at that second
(P1, P2, leader, paused) | met; the stream rows' summary; `close/`; `preregistration.md` + `.sha256`; title, redact and
cheat-name checks; `manifest.sha256`); `logs/h7l1_git_status.txt`. No title, character name, cheat name, serial, game id
or path; nothing committed.

## Files

`evidence/B98_H7_ACCEPTANCE_IN_SEARCH_2026-11-11.md` + `b98_2026-11-11/`; `evidence/B99_H7_LIVE_READ_2026-11-11.md` +
`b99_2026-11-11/` (each: the design + hash, the diff, tests ×3, mutations, scripts, `sha256_before_after.txt`, redact / title /
cheat-name checks (0 FAILS each), manifest; B99 also `settle/` and `b99-h7-live-read.conf`); patch notes `patches/B98_H7_ACCEPTANCE_IN_SEARCH.md`,
`B99_H7_LIVE_READ.md`; code `tools/h7_rule_search.py`, `tests/h7_rule_search/` (`test_b98_acceptance.py` new,
`test_h7_rule_search.py`), `companion/h7_live_read.py` (new), `companion/plugins/games.py`,
`tests/b99_h7_live_read/` (new); `docs/ROADMAP.md` §H7 and `docs/KNOWN_ISSUES.md` (insertions);
`logs/b98_git_status.txt`, `logs/b99_git_status.txt`; `handoffs/SESSION_B_STATUS.txt`. Left (not deleted):
`~/.cache/b_q22ak_tmp/`, `/tmp/b_q23ak_b98/`, `/tmp/b_q23ak_b99/` (snapshots: `companion/`, `tools/`, `tests/`,
`PrivyHub/` only).

Written last, 2026-11-11T22:15:27Z, after the status line, the logs and both manifests.
