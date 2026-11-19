---
memory_schema: 1
as_of: 2026-11-19
status: BUILT (session B, queue BC) — `rehearse <code>`, a sixth command of tools/party_add_game.py for a title already in the rules folder: its kept states as the tool's roles (which is which, and what is missing, on its page), learn's whole real path run into a scratch rules folder, every kept ending read by the scratch rules and the real ones, the real rules folder's every file sha256 before = after as a cell, the scratch removed. Tested with made-up pictures only; the real picture source (the title started headless) is A's to run and stays unproved until then. **Found: T88's and T89's kept folders have no mid-match state, and the learner cannot learn without one** — rehearse takes that one role from the user's own slot (`--collect other=<slot>`, read only, copied into the scratch only; added after the design was hashed, disclosed). Nothing adopted; nothing committed
---

# B163 — learn rehearsed on a title already added

Queue: `handoffs/QUEUE_2026-11-19BC.md` §B163. The directory is `b163_2026-11-19/`: the design + `.sha256` (hashed
04:26:25Z, before any code), the checks, `manifest.sha256`. The code is in `b162_2026-11-19/b162_b163.diff` (one tool
file holds B162 and B163). Patch: `patches/B163_ADD_GAME_REHEARSE.md`.

## The command

`python3 tools/party_add_game.py rehearse <code> [--collect <role>=<slot> …]` — refused unless the title was
registered from the rules folder (`--rules-players`) and its `learn` is PASS.

- **The roles, by the kept file's name** (`~/privyhub_h7/<code>/`, read only): `begin` → begin; `other*` / `mid*` →
  other; `end_p<k>` → end_P<k>; `end_p<k>_<x>` → another ending of end_P<k> (read, not a learning role); `results_<n>`
  → a results screen whose row the real rules read (a role `end_r<row>` for a `places` title). The page and the
  verdict's `recorded` say which is which and what is missing.
  - **T88** (read by name only, here): `begin.state` → begin, `end_p1.state` → end_P1, `end_p2.state` → end_P2;
    `end_p1_b`, `end_p2_b` → endings read, not roles; **missing: other**.
  - **T89**: `begin.state` → begin; `results_1.state` → a results screen (PP-H4 part 1 read it as the row `1234`);
    **missing: other, and the rows `2341`, `3412`, `4123`** that `register` asks of a `places` title.
- **`--collect role=slot`** (only a role the kept folder lacks; slots 1-3): the user's own slot (the setup's slot index
  when the title has a setup), read only, copied into the scratch kept folder only.
- **Learn's whole real path:** a scratch tree under the title's add_game folder — its own kept copies, a binding as
  `register` writes one for a new title (the game file from the hub's `details`, in memory), register's PASS for those
  states, its own evidence folder, `PRIVYHUB_H7_RULES` pointed at an empty scratch rules folder — then **`learn`
  itself**: the capture (`party_add_game_capture`, the title started headless, B95's Session), the labels, the learner,
  the held-out score, the replays, and on PASS the spec, begin and sidecar written into the scratch rules. The
  environment put back and the scratch removed however it ends; any error a cell, never a trace.
- **Cells:** every cell of the scratch `learn`, named `learn: …`, and its verdict; **`<ending>: the scratch rules read
  it as the real rules`** for every kept ending (each role's and the extra ones), its pictures replayed through both
  specs as learn's replays do — met when both ended, the same, and its own ending; **the real rules folder: every file's
  sha256 before = after**; **the scratch removed**. Exit 0 only on PASS; `rehearse.json` / `.md` in the title's
  evidence folder, nothing named.

## Found: no mid-match state is kept for T88 or T89

T88's real spec was learnt (H7-V1) from three recorded sittings — 449 `other` frames among them; its kept folder holds
only the begin and the endings. `h7_endscreen.learn` refuses without `other` frames ("the labels name no other frames:
the screen's threshold cannot be learnt"). So **`rehearse T88` on its kept states alone FAILs at the learner, every
time** — said plainly by the tool (test 4). The item's words ("its kept states taken as the tool's roles … what is
missing if a role has none") are kept; the narrow addition is `--collect`, so the one missing state can be **one save
by the user** (a mid-match SAVE to a slot the user does not need), exactly as `register --collect` takes a new title's.
`ADD_GAME_TASK.md` §0 now asks for it before `rehearse`. **Added after the design was hashed (disclosed).**

## What rehearse proves, and what stays unproved until A runs it

**Proven here (made-up pictures, B157's `fake_capture`; a made-up title already in a made-up rules folder):** the roles
and the missing ones named; the scratch tree and register's stand-in; `learn` called into it and its cells carried;
the scratch spec and the real one compared on every kept ending; the real rules folder untouched (every sha256); the
scratch gone; the same verdict and bytes twice; nothing named. **Unproved until A runs it on the hub:** the real
capture — RetroArch started headless on the title's own game file, the kept state loaded paused, the screenshots'
timing, and (T88 being under a setup) a setup's state shown in a session without the setup's cheats; and whether
learn's bars hold on those real pictures. That is learn's real picture source, never run until then.

## Tests (`tests/b163_rehearse/`, 6)

A made-up title (its spec learnt from made-up pictures with a mid-match run, its begin, its sidecar as learn writes it),
a kept folder `begin`, `end_p1`, `end_p2`, `end_p1_b` (no `other`, as T88's), a made-up hub answering its game file, a
made-up user's slot 2 holding a mid-match state. **Refused** before register, before learn, and for a title not already
in the rules folder; **`rehearse --collect other=2` PASS**: learn's 13 cells and its PASS, every ending (`end_P1`,
`end_P2`, `end_p1_b`) read the same by both specs, the real folder's 4 files' sha256 before = after, the scratch gone,
the roles `begin.state`, `end_p1.state`, `end_p2.state`, `slot 2`, missing none, the user's slot unchanged, nothing
named, the same verdict twice; **a kept `end_p2_b` that shows P1's screen → only its cell not met** (the real rules
read end_P1); **a learn bar raised past the made-up spec → FAIL `learn: margin_needed`**, the real folder untouched,
the scratch gone; **no `other` → FAIL, missing other, the learner's own words in "learn ran in the scratch"**;
`--collect` of a role already kept → refused. **6 OK ×3** (`b162_2026-11-19/tests_x3.txt`). Mutations below.

## Mutations (B163's three) — and a gap in my own test they found

`b162_2026-11-19/tests_mutations.txt`: **the ending cell always met → caught** (test 2); **the scratch kept → caught**
(tests 1-4). **Learn run into the real rules folder → NOT caught on the first run (disclosed):** my made-up "real" spec
was learnt from the same made-up pictures the scratch learns from once `other` is collected, and the begin and sidecar
were the bytes learn writes — so a learn written into the real folder wrote identical bytes and no sha256 changed. The
test now learns the made-up real spec from shorter runs (12 s, not 20 s), so any spec the scratch learns differs from
it; rerun: **6 OK**, and the mutation **caught** (tests 1 and 2: the real folder's sha256 cell;
`tests_mutations_rehearse_fix.txt`). The tool was not changed for it.
