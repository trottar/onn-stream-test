---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 6e4563f7109f6dd1b4227a264e96e2acbd7e112d
---

# C3 fixed 5000 kbps runtime disposition

## Classification

**RUNTIME TESTED / NOT ACCEPTED AS LADDER CANDIDATE**

Current bitrate state:
- 7000 kbps: validated reference/max;
- 6000 kbps: validated lower candidate;
- 5000 kbps: runtime tested / not accepted;
- current lower-bound bracket: 5000–6000 kbps;
- next candidate: 5500 kbps;
- production minimum: unset;
- automatic controller: not implemented.

## Runtime result

`C3_FIXED_5000_EVIDENCE_CAPTURED_WITH_FINDINGS`

Measurements:
- session duration: 57,498 ms;
- sequence resyncs: 1;
- SSRC changes: 1;
- packets dropped waiting for IDR: 0;
- resync-to-IDR: 17 ms;
- waiting for IDR at end: false;
- lost video packets: 100;
- FEC recovered packets: 6;
- unrecoverable FEC groups: 15;
- decoder rendered frames: 3,080;
- decoder dropped frames: 11;
- decoder queue-overflow drops: 11;
- decoder max output gap: 1,010 ms;
- decoder max receive-to-decode: 1,019 ms;
- audio lost packets: 47;
- audio write errors: 0;
- audio underruns: 203;
- audio stale drops: 1,083;
- audio max queue depth: 8;
- audio concealed loss packets: 19;
- audio concealed underruns: 1,223;
- audio prolonged starvation events: 135;
- audio smooth latency trims: 1,083;
- audio crossfaded packets: 628;
- audio max queue residence: 49 ms;
- audio average queue residence: 26.305714374938912 ms;
- controller packets sent: 24,905;
- controller send errors: 0.

## Focused observation

- image was definitely clearer;
- initial lag remained;
- after the initial period, gameplay could run very nicely and feel smooth;
- over longer focused play, visual stutters were definitely more frequent than
  at the other validated bitrate settings;
- possible slightly worse input lag was noticed but remained uncertain.

## Decision

The increased steady-state visual stuttering is sufficient to withhold ladder
acceptance at 5000 kbps.

The clearer image and clean 17-ms restart recovery remain useful positive
evidence, but smoothness takes priority for this low-latency game-stream
profile.

The known audio burst/gap behavior remains separate and deferred to Linux +
Home-Opal replay.

D-065 brackets the lower boundary between 5000 and 6000 kbps and selects
5500 kbps as the next single characterization point.
