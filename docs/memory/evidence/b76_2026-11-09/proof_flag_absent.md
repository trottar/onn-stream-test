# B76 — `PRIVYHUB_ART_SYSTEMS` absent = today, hunk by hunk (`b76.diff`)

| file | hunk | absent (or any value but `1`) |
| --- | --- | --- |
| `companion/games/metadata_importer.py` | `import os` | no behaviour |
| | `ART_SYSTEMS_ENV`, `EXTRA_SYSTEM_SPECS`, `art_systems_on`, `system_specs` | `system_specs()` returns `SYSTEM_SPECS`'s four items (`test_absent_or_other_values_are_todays_four`); `SYSTEM_SPECS` itself unchanged (the cheat tool's import is today's) |
| | `LibretroProvider(…, specs=None)` → `self.system_specs` | the four (`test_provider_default_reads_the_environment`) |
| | `prepare_system` / `_artwork_url` / `fetch_artwork` read `self.system_specs` | the same four entries as `SYSTEM_SPECS`: the same refusals (`test_three_systems_unavailable_without_any_fetch`: `provider_unavailable` + `preserve_prior`, `invalid_match`, no fetcher call) |
| | new `run_metadata_dry_run` | only reached by `--dry-run` |
| `tools/update_game_metadata.py` | the import; `choices=sorted(system_specs())` | the same four choices |
| | `--dry-run` | a new option; without it the tool runs today's code path |

`run_metadata_update` and `startup_reconcile` are untouched: they build the provider as before, which now reads the
knob; absent → the four. A run without the knob keeps the three systems' prior records
(`test_prior_records_kept_by_a_run_without_the_knob`), so art fetched once (A's ART-1, the knob in that command's
environment only) survives later companion starts.
