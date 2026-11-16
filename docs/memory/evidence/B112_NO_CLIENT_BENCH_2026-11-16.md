---
memory_schema: 1
as_of: 2026-11-16
status: BUILT (session B, queue AP) — behind PRIVYHUB_H7=1 only (the party word also needs PRIVYHUB_PARTY=1, as its route does), loopback callers only, refused whenever a client's stream is up, never touching the adopted audio line or the client's identity (no stream started, no codec declared, no session made): `POST /plugins/games/bench-release` releases a launched game's pause with no stream; `h7-start?bench=1` runs the end-screen watch with no stream (the watcher reads the game's window itself); `party-minigame-start?…&bench=1` runs a party mini game with no stream (no switch). Absent → today byte for byte through the real HTTP routes against HEAD 0a3d78e2's companion. Tests through the real HTTP server on loopback: 7, 3 runs green (with B110 and B111); mutations 5 / 5. Nothing adopted; nothing committed
---

# B112 — a bench way to run a game with no client (2026-11-16)

**Why:** H7-V3 stopped at its step 8 — a game launched from loopback with no client stays paused, the stream to nobody
is refused by the adopted audio line (no signed opus declaration for loopback; `audio_codec.py:358-374`, the session
setup refusing a loopback media host), `native-stream-ready` (the only resume) needs the stream, and `h7-start`
refused "the stream is not up". **Baseline:** HEAD `0a3d78e2` + B110. **Design** hashed 18:24:20Z, before code.

## What the stream was needed for, and what is skipped without it

The stream carries the picture and sound to the onn and the onn's pads back; for the watcher it was only a guard that
a client is there — **the watcher reads the game's window itself** (Pillow's X11 grab), never the stream. **Skipped on
the bench:** the picture and sound to an onn (none), the onn's pads (none), the recovery's monitor (it starts at
`native-stream-ready`, never reached), the party mini game's stream switch.

## What was built

- **`POST /plugins/games/bench-release`** — the manager's own `resume` with no stream (RetroArch: PAUSE_TOGGLE; the
  board: its first release, no key); a `bench_release` row. Refused: "the bench is for loopback callers only" (any
  address the handler gives the plugin that is not `127.0.0.1` / `::1` — a session's caller is given its declared
  media address, never loopback), "a client's stream is up: not on the bench", "no game is running".
- **`POST /plugins/games/h7-start?bench=1`** — B103 / B105's start without the stream check (the same refusals for
  everything else; `bench` in the `watching` row); refused for a non-loopback caller and while a client's stream is up.
- **`POST /plugins/games/party-minigame-start?…&bench=1`** — B110's mini game with the watcher on the bench word and
  no switch; the same three refusals.
- Without `bench` every route is as before (B103 / B105 / B110).

## Tests (`tests/b112_no_client_bench/`, 7; the real HTTP server on loopback, the stream down unless a case puts it up)

- A PS1 title launched with no client is paused; `native-stream-ready` refused (today's: it needs the stream);
  **`bench-release` → released, the fake RetroArch playing**.
- `h7-start` → 400 "the stream is not up"; **`h7-start?bench=1` → watching → recognised true → ended `end_P1`**; no
  stream start asked.
- The board launched with no client → `bench-release` (its first release); **`party-minigame-start?…&bench=1` → ended
  with scores [0, 1]** → end; no stream start at all; the board's session back.
- **A caller that is not loopback** (the plugin given another address for that call, as a session's would be): all
  three refused with the plain line. **A client's stream up:** `bench-release` and `h7-start?bench=1` refused.
- No game → `bench-release` refused.
- **The flag absent** (and PARTY only, and H7=0): `bench-release`, `h7-start?bench=1`, `party-minigame-start?…&bench=1`
  answer **byte for byte as `git archive 0a3d78e2`'s companion** ("Unknown Games plugin POST action: bench-release").
- Results: in `b110_2026-11-16/tests_x3.txt` (with B110 and B111), `tests_mutations.txt` — **3 runs × 7 green; mutations 5 / 5 caught** (bench-release for a non-loopback caller, the bench while a stream is up, the bench word ignored by the watcher, the party bench for a non-loopback caller, a release that releases nothing).

## Files

`b112_2026-11-16/`: start files, the design + hash, `b112.diff` (applies after `b110.diff`), `scripts/`
(`mutate.py`, `mutations.json`; the batch is B110's `run_all.sh`), `tests_mutations.txt`, redact / title checks,
`manifest.sha256`. Patch note: `patches/B112_NO_CLIENT_BENCH.md`.
