# D-126 Android EPG prefetch runtime acceptance — 2026-09-17

**Classification:**

`D126_ANDROID_TV_ENTRY_AND_PAGE_PREFETCH_VALIDATED`

## Measured result

- baseline prefetch timestamp: `0`;
- observed prefetch timestamp: `1789662883839`;
- requested channel identities: `21`;
- queued channel identities: `21`;
- newer prefetch observed: `true`;
- requested positive: `true`;
- queued positive: `true`.

## User-visible observation

During the same runtime check:

- top-level TV entry spent a few seconds on `Loading TV catalog...`;
- Favorites loaded immediately.

## Conclusion

The D-126 Android warm-ahead integration reaches the Linux D-125 prefetch seam
from normal TV/Favorites navigation and is accepted.

The residual initial TV-entry delay is a separate catalog/state-entry path. It
does not reopen the validated non-blocking EPG cache-miss boundary.

Source runtime log:

`logs/tv/d126_android_epg_prefetch_probe.txt`
