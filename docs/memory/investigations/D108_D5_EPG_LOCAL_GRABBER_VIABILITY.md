# D-108 — D5 EPG local-grabber viability

<!-- PRIVYHUB_D109_D5_EPG_PORTABLE_NODE:D108_RESULT:BEGIN -->
## Result — 2026-09-16

D-108 completed with:
`D108_ENVIRONMENT_NODE_UNSUPPORTED`.

Host:
- Git 2.47.3;
- Node unavailable;
- npm unavailable.

The probe intentionally stopped before reading the onn TV DB, fetching guide
metadata, checking out the upstream EPG repository, installing dependencies, or
attempting a grab.

Therefore local EPG acquisition remains untested.

D-109 continues the same diagnostic using a temporary checksum-verified official
Node runtime. Do not install Node globally for this probe.
<!-- PRIVYHUB_D109_D5_EPG_PORTABLE_NODE:D108_RESULT:END -->

**Status:** diagnostic-only / runtime evidence next

## Narrow question

Can the Linux companion host use the current IPTV-org EPG grabber to produce
real XMLTV programme data for a small representative set of exact D-107 channel
matches without changing PrivyHub production state?

## Why this is the next boundary

D-107 measured approximately 40% exact canonical guide-metadata coverage for the
built-in IPTV-org provider, but only two canonical IDs currently expose hosted
XML/GZIP sources.

The metadata is therefore useful enough to test local acquisition. Hosted-guide
availability remains the blocker.

## Upstream toolchain reviewed

Pinned upstream EPG commit:

`78e94adb76841a63d94a53e80dbd0d52bb7c2c5c`

The reviewed upstream package:

- supports custom `*.channels.xml` input;
- loads site-specific grabber configs;
- writes XMLTV output;
- requires Node >= 20.20.0;
- downloads IPTV-org API data during its install/postinstall path.

D-108 does not install or upgrade system Node/npm/git.

## Probe

`tools/probes/d108_epg_local_grabber_viability_probe.py`

The probe:

1. reads the current onn built-in IPTV-org channel IDs through authorized ADB
   `run-as`;
2. fetches current `guides.json`;
3. selects exact English feed-aware matches with usable `site` and `site_id`;
4. creates a disposable temporary checkout of the pinned upstream EPG commit;
5. uses a disposable npm cache and dependency tree;
6. selects up to three distinct configured guide sites, preferring D-107's
   highest-coverage sites;
7. runs the upstream grabber for one day and one channel per selected site;
8. parses generated XMLTV and counts target-channel programmes and current/
   upcoming 48-hour programmes;
9. removes the temporary checkout, dependencies, npm cache, channel files, and
   generated XMLTV when the probe exits.

## Decision boundary

- multi-site real programme output -> Linux-local acquisition is technically
  viable; design a narrow companion cache/service seam next;
- single-site output -> viable but source-diversity risk remains;
- toolchain setup/environment blocker -> decide whether to provide an isolated
  runtime or implement a lighter native acquisition path;
- zero programme output -> inspect the first failing site/grab boundary before
  any production architecture change.

No Android or companion production change belongs in D-108.
