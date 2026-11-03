# D-119 — D5.4 TV-entry synchronization trigger

<!-- PRIVYHUB_D120_SYNC_DIAGNOSTICS:D119_RESULT:BEGIN -->
## Runtime result — accepted

D-119 passed:

`D119_TOP_LEVEL_TV_ENTRY_SYNC_TRIGGER_AND_RESTORE_VALIDATED`

A true top-level TV entry adopted prepared Linux revision 5 without Refresh.

Cleanup:
- Linux restore revision 6;
- onn revision 6;
- exact local/remote canonical-state parity;
- original Linux/onn content restored;
- session removed.

Conclusion:
normal top-level TV entry reliably invokes synchronization. No production
trigger/lifecycle patch is required.

D-119 is closed.
<!-- PRIVYHUB_D120_SYNC_DIAGNOSTICS:D119_RESULT:END -->

**Status:** diagnostic-only / runtime interaction required

## Narrow question

Does selecting TV from the actual top-level PrivyHub source list reliably invoke
the already-validated Linux-authoritative pull path without pressing Refresh?

Core D5.4 state mechanics are already accepted. D-119 must not redesign them.

## Source boundary

Current `MainActivity` routes the top-level `tv` node into `openTvHome()`.
`openTvHome()` executes `synchronizeTvStateNow()` after local catalog loading and
before rendering the TV home node.

The explicit TV Refresh path also routes through `openTvHome()` and was already
observed pulling Linux revision 4 successfully.

## Probe

`tools/probes/d119_tv_entry_sync_trigger_probe.py`

The probe uses a reversible three-phase sequence.

### Prepare

- require current Linux/onn revision and canonical-state parity;
- save the original Linux user-state content in ignored mode-0600 local probe
  state;
- change only `preferences.country_name` to a D-119 marker;
- keep `country_code` unchanged;
- advance Linux by one revision.

### Verify

The user must:

1. press Back until the top-level PrivyHub source list is visible;
2. select TV exactly once;
3. not press Refresh.

The probe then checks whether the onn adopted the prepared Linux revision and
marker. Regardless of the trigger result, Linux is restored to the original
user-state content if no independent Linux mutation occurred.

### Final

Use the already-validated explicit TV Refresh path once to pull the restoration,
then verify exact Linux/onn revision/hash parity and remove the D-119 session.

## Classifications

Success:

`D119_TOP_LEVEL_TV_ENTRY_SYNC_TRIGGER_AND_RESTORE_VALIDATED`

Trigger defect with safe cleanup:

`D119_TOP_LEVEL_TV_ENTRY_TRIGGER_NOT_OBSERVED_CLEANUP_VALIDATED`

If the second classification occurs with ADB healthy, a narrow production
trigger/lifecycle fix is justified.

## Safety

D-119 does not change Android or companion production code.

The runtime marker changes only the country display name, never the country code,
favorites, hidden state, provider state, channel overrides, catalog, EPG,
playback, or health/recency data.

If Linux changes independently while the marker is active, the probe refuses to
overwrite it.
