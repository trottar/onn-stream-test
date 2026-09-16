---
memory_schema: 1
as_of: 2026-09-16
status: diagnosed
classification: LINUX_MULTITAP_METADATA_PROJECT_ROOT_ASSUMPTION
---

# D-087R1 Linux multitap metadata-path evidence

After D-087, runtime reached the correct Linux target under RetroArch's user
Config tree, then raised that the game-specific `.opt` was not in the subpath of
the PrivyHub project root.

Source cause: the returned `options_file` metadata still calls
`target_options.relative_to(self.project_root)` after file materialization and
byte verification.

R1 preserves the actual Config-root/write logic. It changes only metadata:
- Windows -> existing project-relative portable path;
- Linux -> `retroarch-config/<core>/<game>.opt` relative to the trusted Config
  directory.
