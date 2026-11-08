# B63 — the knob `PRIVYHUB_PS1_MULTITAP_CAPABILITY=0` = today; the default-on change, hunk by hunk

B63 is **default-on** (disclosed): with the knob absent, the rule applies to PS1 titles. `=0` restores today:
- **`players_session.plan`:** `capable` is `None` when the launch reads the knob `0` (`ps1_capable = … if … and
  capability_rule_on() else None`), so `available` is today's expression, no `capable` / `capped_from` keys, and the
  plan is byte for byte (test: `capable=None` → today's dict exactly);
- **`ports_set`:** the plan echo copies `capable` / `capped_from` only if present (never with `0`); the metadata
  fallback's new branch is skipped when `capability_rule_on()` is false (test: the knob `0` → `multitap_available`
  true, no `capable` key);
- **`relaunch_ports.run`:** the refusal needs `capability_rule_on()`, so it is skipped with `0`;
- **`EmulatorManager.ps1_multitap_capable`:** a new method, called only through those branches;
- **the launch's log line:** only when the plan carries `capped_from` (never with `0`).

**Shown:**
- `test_the_knob_zero_is_today`: a real PS1 launch through the fake tree, the incapable title with 3 joined → four
  `--device`, the multitap enabled, no `capable` key;
- `tests/players_session` 19 and `tests/relaunch_ports` 19 (B54 / B57) green unchanged; their fakes carry no
  `ps1_multitap_capable`, so they read today's path;
- **non-PS1 systems: unchanged with the rule on too** (`plan` for snes / ps2 / n64 equal with and without `capable`).
