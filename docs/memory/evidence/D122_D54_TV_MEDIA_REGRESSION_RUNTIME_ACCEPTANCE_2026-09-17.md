# D-122 — D5.4 TV/media regression runtime acceptance — 2026-09-17

**Status:** runtime validated / accepted

Automated classification:

`D122_D5_TV_MEDIA_AUTOMATED_REGRESSION_BASELINE_VALIDATED`

Measured automated baseline:

- companion `/status`: HTTP 200;
- companion `/sources`: HTTP 200;
- source count: 1;
- EPG plugin: HTTP 200 / ready true;
- Linux TV-state revision: 8;
- onn remembered TV-state revision: 8;
- Linux and onn canonical durable-state SHA-256:
  `cea4fa1fba5ad7a903cf0c60ffbc528dc7d754932402ab77d11f9696ec65f2c3`;
- exact TV-state parity: true;
- last successful sync action: `pulled`;
- last successful sync revision: 8;
- retained conflict evidence: base revision 6 / server revision 7;
- automated baseline: true.

Manual onn regression was also reported clean:

- normal Live TV navigation works;
- Live TV playback remains functional;
- Program Guide shows real schedules across multiple channels;
- VOD playback remains functional;
- back/return navigation remains functional;
- TV Settings -> Catalog / EPG Status still exposes the D-120 state diagnostics.

## D5.4 disposition

D5.4 Linux-authoritative TV durable-state synchronization is complete and
runtime validated.

Accepted end-to-end properties:

1. Linux revisioned durable authority;
2. first-run onn seed when Linux is uninitialized;
3. onn durable-state push;
4. Linux-to-onn authoritative pull;
5. exact canonical parity;
6. normal top-level TV-entry synchronization;
7. stale-write rejection;
8. conflict diagnostics;
9. authoritative recovery;
10. no regression in mature Live TV / EPG / VOD paths.

No further D5.4 synchronization production change is indicated.
