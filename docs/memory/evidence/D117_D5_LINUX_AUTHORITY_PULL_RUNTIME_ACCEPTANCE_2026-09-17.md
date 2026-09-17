# D-117 — D5.4 Linux-authority pull runtime acceptance — 2026-09-17

**Status:** runtime accepted, with classifier correction in D-118

D-117 intentionally advanced Linux TV state from revision 2 to revision 3 with
a harmless temporary `country_name` marker, then restored the original durable
user-state content at revision 4.

The temporary revision-3 marker was not observed on the onn during the first
attempt. The verify phase therefore recorded:

`D117_PULL_NOT_OBSERVED_LINUX_RESTORED`

Linux restoration itself succeeded.

ADB connectivity then became unavailable, causing both D-116 and D-117
read-only onn snapshots to fail temporarily. This was an ADB transport issue,
not a TV-state regression.

After ADB was reconnected, the explicit TV Refresh path executed the existing
`openTvHome()` synchronization path.

Authoritative post-refresh measurements:

- Linux authority revision: 4;
- onn remembered server revision: 4;
- Linux canonical durable-state SHA-256:
  `cea4fa1fba5ad7a903cf0c60ffbc528dc7d754932402ab77d11f9696ec65f2c3`;
- onn canonical durable-state SHA-256:
  `cea4fa1fba5ad7a903cf0c60ffbc528dc7d754932402ab77d11f9696ec65f2c3`;
- local/remote parity: true;
- 25 durable channel rows;
- 22 favorites;
- 3 manual-hidden rows;
- `10 Bold Adelaide` remained manually hidden on both Linux and onn.

A stale onn push could not have produced this outcome because D-115 rejects a
stale `base_revision`. The onn adopting revision 4 with exact canonical parity
therefore validates Linux-authoritative pull of the restored state.

The final D-117 probe itself also measured:

- `onn_country_name: All Countries`;
- `onn_stored_revision: 4`;
- `local_remote_parity: True`;
- `linux_original_content_restored: True`;
- `onn_original_content_restored: True`;
- `session_active: False`.

Its `D117_FINAL_RESTORE_PARITY_FAILED` label was a classifier defect: the probe
required the temporary revision-3 marker to have been observed even when the
later restored revision-4 authority was demonstrably pulled and matched.

D-118 corrects the diagnostic classifier. No Android or companion production
change is required.

Accepted D5.4 directional behavior through D-117:

1. onn -> Linux initial seed: validated;
2. onn -> Linux durable mutation push: validated;
3. Linux -> onn authoritative pull: validated;
4. restored Linux state -> onn exact canonical parity: validated.
