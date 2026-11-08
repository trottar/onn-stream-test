# B64 — the default proof (no flag: the hold-to-join rows' own fields)

- **A client that sends no `players_joined`** (B34-B46's rows): `stale` needs `bool(players_joined)`, so it is never
  set. The row and the heartbeat values are byte for byte (`test_no_join_client_is_byte_for_byte` compares the whole
  row and the value keys).
- **`since_start`** only gates the new tag; `last` / `last_chosen` / `last_joined` are updated exactly as before, so
  which heartbeats write a change row is unchanged.
- **The only difference** is the key `stale: true` on the first unclaimed carry-over row after a start, and
  `pad_slots_stale: true` on its heartbeat row.
- `tests/pad_slots` 5, `tests/pad_slots_changes` 7 and `tests/player_prompt` 11 are green unchanged; every host suite
  reads as the baseline plus the new suites (`tests_host_b64.txt`).
