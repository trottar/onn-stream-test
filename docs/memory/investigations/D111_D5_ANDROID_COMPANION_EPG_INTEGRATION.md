# D-111 — D5 Android companion-EPG integration

<!-- PRIVYHUB_D112_D5_GUIDE_NEWLINE:D111_RESULT:BEGIN -->
## Runtime result — 2026-09-16

D-111 passed.

Classification:

`D111_ANDROID_COMPANION_EPG_RUNTIME_VALIDATED`

Measured onn state:
- 65 total EPG programmes;
- last companion-success channel `10Bold.au@Sydney`;
- declared programme count 65;
- 65 SQLite rows for that channel;
- companion response cached: true;
- stale: false.

The Program Guide also displayed real time/title schedule data.

D5.3 EPG data flow is therefore accepted.

Observed follow-up defect:
literal `\n` separators appear between programme rows because the renderer uses
`append("\\n")`.

D-112 fixes only that presentation issue.
<!-- PRIVYHUB_D112_D5_GUIDE_NEWLINE:D111_RESULT:END -->

**Status:** development patch / Android runtime validation next

## Purpose

Connect the existing Android `TvEpgRepository` to the runtime-validated Linux
EPG companion endpoint without rewriting the TV UI or removing the onn cache.

## Production scope

Only:

`PrivyHub/app/src/main/java/com/safeiot/privyhub/TvEpgRepository.kt`

is changed.

The repository reads the existing:

- shared preferences file `privyhub_settings`;
- `companion_host` value;
- control port 8765.

No new settings surface is introduced.

## Fetch order

1. return a fresh nonempty onn SQLite guide immediately;
2. otherwise query
   `/plugins/epg/guide?channel_id=<canonical-id>`;
3. when companion returns programmes:
   - replace that channel's local SQLite programmes;
   - update the existing channel refresh timestamp;
   - record companion-success diagnostic markers;
   - return the existing `TvGuideSummary`;
4. when companion is reachable but has no guide and this is not a forced
   refresh, fail soft to the existing local cache;
5. when companion is unavailable:
   - keep stale/nonempty local cache for normal navigation;
   - otherwise preserve the previous public hosted-guide fallback path.

A forced refresh may still exercise the existing fallback after a companion miss.

## Identity

The Android client sends the existing exact `channelId` unchanged.

This preserves the D-107/D-110 `channel[@feed]` canonical identity.

No fuzzy matching is introduced.

## Timeouts

Companion:

- connect: 3 seconds;
- read: 30 seconds.

This covers the measured D-110 uncached requests (9.105 to 19.538 seconds) while
failing faster than an unbounded network call.

## Database

No SQLite schema migration.

Existing `programmes` and `meta` tables are reused.

On companion success, diagnostic meta keys record:

- last successful channel;
- success time;
- programme count;
- whether the Linux response was cached;
- whether it was stale.

## Runtime validation

After APK installation:

1. keep the validated Linux companion running;
2. open a known matched channel such as `10 Bold` and open Program Guide;
3. verify real programme data appears;
4. run `tools/probes/d111_android_companion_epg_probe.py`;
5. require classification
   `D111_ANDROID_COMPANION_EPG_RUNTIME_VALIDATED`.

No Android DB is modified by the probe.
