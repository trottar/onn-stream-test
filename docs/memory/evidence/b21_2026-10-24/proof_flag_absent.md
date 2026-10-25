# B21 — absent = today

- `companion/plugins/games.py`, B20's items removed from both: 3 / 3 — `_link_recovery = None`; `if (os.environ.get('PRIVYHUB_LINK_RECOVERY') or '').strip():`; `if _link_recovery is not None:` → **identical**.
- Present, the ASTs (unparsed) differ only in:
  - `-            self._recovery._log('link_recovery_config', **_link_recovery.apply(os.environ))`
  - `+            self._recovery._log('link_recovery_config', **_link_recovery.config_row(os.environ))`
- `companion/link_recovery.py`: imported only under the umbrella (B20's `test_absent_nothing_read_nothing_imported`, B21's `test_absent_no_row`); `apply` returns / environ effects = the predecessor's (`test_apply_returns_and_effect_equal_the_predecessor`).

The row under the umbrella alone, fresh process, the service's import order (`plugins/games.py` → `emulator_manager` first):
- predecessor (13ccff5; a scratch copy under `/tmp/b21_pred_*`): `{"umbrella": true, "implied": [], "explicit": {"PRIVYHUB_INPUT_HOLD": "1", "PRIVYHUB_INPUT_HOLD_B6": "1", "PRIVYHUB_INPUT_HOLD_B8": "1", "PRIVYHUB_INPUT_HOLD_REWIND": "1", "PRIVYHUB_STALL_SIGNAL": "1", "PRIVYHUB_STALL_RESUME": "1"}}`
- B21: `{"umbrella": true, "implied": ["PRIVYHUB_INPUT_HOLD", "PRIVYHUB_INPUT_HOLD_B6", "PRIVYHUB_INPUT_HOLD_B8", "PRIVYHUB_INPUT_HOLD_REWIND", "PRIVYHUB_STALL_RESUME", "PRIVYHUB_STALL_SIGNAL"], "explicit": {}, "at": "import", "reapply": []}`

Result: **PROVEN**.
