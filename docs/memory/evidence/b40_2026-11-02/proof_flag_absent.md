# B40 — `PRIVYHUB_VOD_DROP_TEST` absent = today: PROVEN

`proof_flag_absent.py /tmp/b_q02m_base /tmp/b_q02m_b40` → `proof_flag_absent_output.txt`:
1. **Existing files changed:** `companion/range_server.py` and B35's `tests/vod_log/test_vod_log.py` only.
   - The test change is one filter line. B35's AST count of the nodes added since queue L's base skips B40's two
     nodes, which B40's own suite checks instead.
2. **`range_server.py`:** exactly two top-level nodes are added, `VOD_DROP_TEST = None` and the guarded
   `if os.environ.get('PRIVYHUB_VOD_DROP_TEST', '').strip() == '1':`. Every other node equals the predecessor's, node
   for node (the class included).
3. **A fresh process with the line unset / `""` / `0` / `true` / `yes`:**
   - `vod_drop_test` not imported;
   - `RangeRequestHandler.copyfile` is today's;
   - no `vod-drop-test` thread.

Also, in the suite (`Absent.test_the_same_bytes_from_the_base_and_the_new_server`): the base and the new range
servers, run with no `PRIVYHUB_*`, return the same bytes for five requests (Date lines masked). A trigger file
appended to during the run changes nothing: the server is alive, and no `logs/` is written.
