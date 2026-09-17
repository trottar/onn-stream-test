# D-111 — D5 Android companion EPG runtime acceptance — 2026-09-16

**Status:** runtime validated / accepted

D-111 completed end-to-end Android runtime validation.

## Read-only onn EPG probe

Classification:

`D111_ANDROID_COMPANION_EPG_RUNTIME_VALIDATED`

Measured:

- ADB status: ready;
- EPG database snapshot: successful;
- total cached programmes: 65;
- companion-success channel: `10Bold.au@Sydney`;
- declared companion programme count: 65;
- SQLite programme rows for that channel: 65;
- companion response cached: true;
- companion response stale: false.

## UI evidence

The onn Program Guide displayed real schedule data with programme times and
titles.

This establishes the full D5.3 data path:

```text
Linux EPG acquisition/cache
        |
companion /plugins/epg/guide
        |
Android TvEpgRepository
        |
onn privyhub_epg.db
        |
Program Guide UI
```

## Acceptance

D5.3 EPG data flow is runtime validated and accepted.

One presentation defect was observed after functional acceptance:
the Program Guide renderer appends the literal string `\n` between programmes,
so backslash-n artifacts appear onscreen.

That defect is isolated to `MainActivity.showTvProgramGuide()` and does not
invalidate EPG acquisition/cache acceptance.

D-112 fixes only that presentation bug before D5.4 TV-state sync work begins.
