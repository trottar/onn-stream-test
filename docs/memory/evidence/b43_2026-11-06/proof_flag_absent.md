# B43 — flag absent = the CONFIRMED build's behaviour (`0132b944…`): PROVEN

`proof_flag_absent.py /tmp/b_q06n_base /tmp/b_q06n_b43` → `proof_flag_absent_output.txt`, **PROVEN**.

- **Client: absent `debug.privyhub.vod_retry`** (or empty / `0` / junk) builds no controller. `VodRetryFlag` and
  `VodRetryController.wanted` are unchanged, so every `vodRetry?.` call in MainActivity is a no-op, as in `0132b944…`.
  - MainActivity's one change sits inside the flag-only construction: `{ player }` gains a comma and the new
    `{ getCompanionHost() }` argument follows it.
  - The identity layer (`IdentitySession.kt`, `AndroidIdentity.kt`, `MediaDataSource.kt`) is byte-equal.
- **Host, absent `PRIVYHUB_VOD_DROP_TEST`** (or `""` / `0` / `yes`): a fresh process imports no `vod_drop_test`, and
  `range_server.VOD_DROP_TEST` is None. `range_server.py` is byte-equal to the base.
- **Host, `PRIVYHUB_VOD_DROP_TEST=1` with B40's plain line or `drop 0`: B40 as built.** The row's keys are B40's
  exactly (no `refuse_s`), and no window opens (`test_a_plain_line_is_b40_as_built_its_row_byte_for_byte`,
  `test_drop_0_is_a_plain_line`). B40's 14 tests are unedited and green.
- **Host, `PRIVYHUB_VOD_LOG=1` with a B35 client:** its rows are written field for field as before
  (`test_a_b35_row_is_written_as_before`). B35's 9 tests are unedited and green.
  - The module's only new / changed top-level nodes are `CLIENT_REASONS`, `CLIENT_KINDS` and `ClientLog` (three
    `elif` branches in `accept`).
- **Inside the flag, without the token port** (as B35 built the controller): the rows carry no `reason` / `kind` /
  `token_refetched`, and the Retry dialog is B35's (`withoutTheTokenPortTheRowsAreB35sAsBuilt`). B35's 8 JVM tests are
  unedited and green.
