# B83 — absent = today

`b83.diff` adds `tests/art_systems/test_b83.py` and nothing else: no file under `companion/` or `tools/` changes, no
knob is read. With B83 applied the companion, the tools and the onn behave exactly as with B82 alone (whose absent
proof is `b82_2026-11-10/proof_flag_absent.md`). The test file imports B82's test helpers (`test_b82.py`) and reads
`tests/gamecube_session/fake_dolphin.py`; it writes only inside its own temporary trees, which are removed at exit.
