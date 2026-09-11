---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B3 Sunshine/Moonlight dependency inventory result

Fresh classification:

`B3_SUNSHINE_MOONLIGHT_INVENTORY_CAPTURED`

Top-level counts:
- text occurrences: 1687;
- legacy-named artifacts: 163;
- MUST PRESERVE native guard files: 7;
- ACTIVE DEPENDENCY classifications: 236;
- DEAD COMPATIBILITY CODE: 1486;
- INSTALL/UNINSTALL ARTIFACT: 53;
- DOCUMENTATION/HISTORY: 74;
- SAFE TO REMOVE: 0;
- MUST PRESERVE: 8.

Windows system state:
- matching processes: 0;
- matching services: 0;
- matching scheduled tasks: 0;
- matching firewall rules: 0;
- matching installed-software registrations: 0.

Important interpretation:
- the raw ACTIVE count is intentionally conservative and inflated by archive
  backups, Sunshine's vendored runtime/web tree, and path/name matches;
- do not use the 236 count as a deletion list;
- current production source still contains a real Games `StreamManager` edge;
- current Android source still contains Moonlight/com.limelight UI/intent and
  manifest visibility;
- the validated native streaming/controller paths were separately identified as
  MUST PRESERVE.

B3.1 narrows the question to the current production call graph before B4.
