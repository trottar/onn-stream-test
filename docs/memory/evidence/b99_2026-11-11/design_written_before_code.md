# B99 — the live read behind `PRIVYHUB_H7=1` (design, written before code; queue AK, 2026-11-11)

Baseline: HEAD `6cb4663b`. **Changes the companion** (a new module and one route in `plugins/games.py`), behind
`PRIVYHUB_H7=1`; absent / `0` = today byte for byte. Tests in `tests/b99_h7_live_read/`.

## Settled first (synthetic fixtures, B61's form; `settle/live_read.py`, `settle/live_read_results.jsonl`)

Commands sent the companion's way (a fresh UDP socket per command, one answer from the command port).

| | SNES (snes9x; the fixture's frame counter) | PS1 (Beetle PSX HW; a per-frame word in the core's own memory, found by frame-advance) |
| --- | --- | --- |
| frames in 60 s: no reads / a read every second / no reads / a read every second | 3,603 / 3,600 / 3,603 / 3,600 (60.0 a second in every window; the no-read windows 0.05 s longer) | 3,603 / 3,601 / 3,603 / 3,600 (the same) |
| the read's answer time (GET_STATUS + READ_CORE_RAM, 240 commands) | median 16.3-16.6 ms, worst 17.5 ms (one frame: RetroArch answers once a frame) | median 16.3-16.4 ms, worst 17.7 ms |
| answers lost or wrong | 0 | 0 |

- **A read while paused** answers (median 16.6 ms, worst 17.0 ms); the frame counter does not move.
- **Interleaved for 30 s while running** (a status poll every 0.1 s, a read every 0.25 s, a save every 3 s, the hold's
  pause — PAUSE_TOGGLE, GET_STATUS, 0.5 s, PAUSE_TOGGLE — every 4 s): 260 / 260 status, 114 / 114 reads, 7 / 7 hold
  answers, each matched to its own command; **0 lost, 0 crossed** — each command has its own socket, so a late answer
  can only reach a closed one (B93's crossing came from one shared socket).
- **N64** (B61's ROM): `READ_CORE_RAM` and `READ_CORE_MEMORY` (0x… and 0x80…) answer in the same form and time
  (15-17 ms); the fixture's RDRAM is all zeros (its code never lands in RDRAM — a 4 MiB dump and a store-program variant,
  `settle/fixture_n64_store.py`), so **no byte order is anchored here**. Stated for the route: an N64 rule's addresses
  are read with the same `READ_CORE_*` command and byte order its search would read (B94: the read is word-swapped
  against the core's own state file), so a rule found by reads is read back consistently; no N64 rule exists yet.

## The route — `GET /plugins/games/h7-read` (only with `PRIVYHUB_H7=1`)

New module `companion/h7_live_read.py`, imported by `plugins/games.py` only with the flag (absent / `0`: not imported;
the route falls through to today's `Unknown Games plugin action: h7-read`, 400; no rules folder looked at; no row).

- **No game** (no RetroArch / PCSX2 / Dolphin process active) → 200 `{"ok": true, "running": false}`.
- **PS2 / GameCube sessions** (PCSX2, Dolphin) → 400, "reading a PS2 game's memory is not supported yet" / "… a
  GameCube game's …". Other RetroArch systems than PS1, SNES, N64 → 400 "… not supported yet".
- **The rule:** `<rules folder>/<the hub's game id>.json`, the folder `~/privyhub_h7/rules` or `PRIVYHUB_H7_RULES`; the
  id must be a plain file name (letters, digits, `._-`; else "no rule for this game"). B93's rule JSON (per-player
  fields or B94's single field; `memory` ram / memory; 1, 2, 4 bytes; endian; `winner` max / min; `none_when` equal /
  floor), checked as B93's `parse_rule` does. Missing → 400 "no rule for this game"; unreadable / malformed → 400
  "the rule for this game cannot be read: …".
- **The read:** through the companion's own `EmulatorManager._retroarch_network_request` (its socket form, its command
  log), **holding the manager's `lock`** — the same lock the save, load, launch and status paths hold, so the read is
  serialised with them; the lock waited for at most **0.3 s** (else 502 "the game is busy (a save or a load); not
  read"). Commands: `GET_STATUS` (paused or not), then one `READ_CORE_RAM` / `READ_CORE_MEMORY` per player field (or the
  single field), each `timeout` the time left in the bound, `retries=1` — **the whole read bounded at 0.6 s**; past it
  → 502 "the game's memory did not answer in time; not read", nothing retried. Each answer must be its own command's:
  the same command word, the same address, n bytes; `-1` (memory the core does not have) → 502 "the game's memory has
  no address 0x…"; anything else → 502 "an unexpected answer from RetroArch; not read".
- **The answer** (200): `{"ok": true, "game": id, "running": true, "paused": bool, "values": {"P1": v, …},
  "winner": "P1" | … | null, "reason": "no winner yet" | "tie" | null, "read_ms": n}` — the winner as B93 / B95's
  `answer` (equal → "no winner yet" with `none_when: equal`; a shared top otherwise → "tie"; a single field's
  `none_value` → "no winner yet").
- **It changes nothing:** only `GET_STATUS` and `READ_CORE_*` are sent — no pause, save, load, write or cheat command.
- **The floor:** at most one read per **0.25 s**; a call sooner gets the last answer (same game) with `"cached": true`
  and `"age_ms"`; never a queue.
- **The log:** one JSON row per read actually sent (errors included) in `logs/games/h7_reads.jsonl` (with the other
  game logs; `logs/` is git-ignored): `time_unix`, `game` (the hub's id), `values`, `winner`, `reason`, `paused`,
  `read_ms`, or `error`.
- The route is the hub's own (A's watcher at the TV), **not a client call**: `tests/client_contract` unchanged and green.

## Tests (`tests/b99_h7_live_read/`, the companion's real HTTP server on loopback)

B90's harness: a child `python3 -I` on B82 / B83's fixture tree with its own `companion/`, `privyhub_service`'s
handler on `ThreadingHTTPServer` 127.0.0.1:0, RetroArch a fake on the configured UDP command port, **extended with core
memory** (bytes the test changes over time; `-1` beyond its size; an optional delay) and **a command log**. A PS1 title
launched through `POST /plugins/games/launch`. Cases: a rule → values and winner; the fake's memory changed → the new
leader; equal → "no winner yet"; paused (PAUSE_TOGGLE to the fake) → `paused` true, the same values; the fake's
command log during reads: `GET_STATUS` and `READ_CORE_*` only; no game → `running: false`; no rule; a rule beyond the
core's memory → the plain error; a slow fake → the timeout's plain error, the call answered within the bound + 0.3 s;
reads racing `POST save-state` and status polls → every read answered with its own values or a plain "busy" (never
another command's answer), the save's own answer intact; the floor (a second call within 0.25 s → cached with its age,
no new command); a PS2-kind session → "not supported yet"; the log rows. **Flag absent and `0`:** the same calls through
the real route on HEAD's companion (`git archive HEAD`) and on this one — the JSON answers byte for byte equal (status
codes and bodies), no file opened under the rules folder (an audit hook in the child), no `h7_reads` row.
`tests/client_contract` green.
