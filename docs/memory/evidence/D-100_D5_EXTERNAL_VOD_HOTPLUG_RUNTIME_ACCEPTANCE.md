---
memory_schema: 1
as_of: 2026-09-16
evidence: D-100_D5_EXTERNAL_VOD_HOTPLUG_RUNTIME_ACCEPTANCE
status: runtime_validated
---

# D-100 external VOD hotplug runtime acceptance

## Previously validated host behavior

- configured VOD storage boundary reports available when present;
- 91 VOD sources;
- Aviator stable source ID preserved;
- source-start HTTP 200 / ready;
- one-byte logical `/vod` Range request HTTP 206;
- managed companion lifecycle clean;
- absent removable storage no longer throws ENODEV through `/sources`;
- absent-storage requests no longer block until Android reports Companion
  unavailable.

## Final onn physical E2E

With normal Companion operation:
- external VOD was unplugged physically;
- VOD showed no movies;
- onn refresh succeeded;
- external VOD was reinserted without Linux file-manager activation;
- movies returned automatically;
- Continue Watching reappeared and worked;
- external VOD was unplugged again;
- VOD again showed no movies;
- onn refresh again succeeded.

## Result

Classification:
`D5_EXTERNAL_VOD_HOTPLUG_RUNTIME_ACCEPTED`

External/removable VOD storage is accepted as a stable Prototype-1 subsystem.
