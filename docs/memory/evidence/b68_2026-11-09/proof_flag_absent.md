# B68 — absent = today (`PRIVYHUB_IMPORT` not `1`): the tool does nothing; nothing else changed

- `tools/library_m3u.py` is new and reached only when run by hand. Without the flag every command (`plan`, `apply`,
  `undo`) prints the refusal and exits 9 before reading or writing anything (`test_the_flag_and_a_running_game`: no
  `.m3u`, no `data/`).
- No companion, plugin or list code changed: the list's `.m3u` rule (an `.m3u` hides what it names) is today's code,
  so the list changes only when an `.m3u` file exists.
- **B did not apply it.** The hub's library was only read (`hub_plan_counts.txt`: `make_plan` called directly, no plan
  file, no log written).
