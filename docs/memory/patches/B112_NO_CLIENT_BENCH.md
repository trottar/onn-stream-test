---
memory_schema: 1
as_of: 2026-11-16
baseline_commit: 0a3d78e2
---

# B112 — a bench way to run a game with no client, behind PRIVYHUB_H7=1 (loopback only, never with a client's stream up)

**Result:** `evidence/B112_NO_CLIENT_BENCH_2026-11-16.md`.

- **Files:** `companion/h7_minigame.py` (`bench_release`, the `bench` word in the start), `companion/plugins/games.py`
  (`POST bench-release`; `h7-start?bench=1`; `party-minigame-start?…&bench=1`), `companion/party_minigame.py` (the
  word passed to the watcher), `tests/b112_no_client_bench/test_b112.py` (new); `evidence/b112_2026-11-16/b112.diff`
  (applies after `b110.diff`).
- **Switch:** `PRIVYHUB_H7=1` (+ `PRIVYHUB_PARTY=1` for the party word) — loopback callers only, refused while a
  client's stream is up; no stream started, no codec declared, no session made. Absent → today, byte for byte.
- **Live:** not adopted; PP-H3 part 1 uses it unattended.
- **Rollback:** `git apply -R b112.diff`.
