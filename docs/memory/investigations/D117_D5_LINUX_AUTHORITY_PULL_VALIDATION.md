# D-117 — D5.4 Linux-authority pull validation

**Status:** diagnostic-only / runtime interaction required

## Narrow question

When Linux already contains a newer durable TV-state revision, does opening TV
on the onn actually pull and apply that authoritative state?

D-116 validated seed and onn-to-Linux push. It did not deliberately make Linux
newer than the onn.

## Probe design

`tools/probes/d117_linux_authority_pull_probe.py`

Three phases:

1. `prepare`
   - requires current D-116 local/remote parity;
   - saves the original Linux user state privately under ignored
     `data/tv_state/`;
   - changes only `preferences.country_name` to a D-117 marker;
   - leaves `country_code` unchanged;
   - advances Linux by one revision.
2. `verify`
   - checks that opening TV pulled the marker and prepared revision to the onn;
   - restores the original Linux user-state content;
   - advances Linux by one more revision.
3. `final`
   - checks that opening TV again pulled the restored state;
   - requires exact canonical local/remote user-state parity;
   - deletes the private D-117 session.

## Safety

The test does not change:

- country code / channel filtering;
- favorites;
- hidden channels;
- providers;
- custom overrides;
- catalog;
- EPG;
- playback;
- runtime health.

If Linux changes independently while the marker is active, D-117 refuses to
overwrite that newer state.

A successful run restores the original user-state content, while Linux's
monotonic server revision naturally remains two revisions higher.
