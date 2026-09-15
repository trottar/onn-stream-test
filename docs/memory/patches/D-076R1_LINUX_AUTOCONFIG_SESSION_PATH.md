# D-076R1 Linux managed RetroArch autoconfig session path

Date: 2026-09-15
Status: **HOST-SIDE MANAGED RUNTIME VALIDATED / ONN E2E PENDING**

## Purpose

Correct the Linux managed-launch path semantics discovered after D-076. This is
a narrow session-config correction; the D-076 uinput backend and mappings are
unchanged.

## Fresh failure evidence

The first managed RetroArch D-076 probe established:

- controller preflight active: true;
- backend: `linux_uinput`;
- four players created before launch;
- RetroArch launched and reached `PLAYING`;
- udev saw P1-P4 on event19-event22;
- each pad was reported `not configured`;
- manager fallback stop was graceful;
- controller cleanup removed all virtual pads.

Source/path inspection then proved:

- manager process cwd: `executable.parent`;
- persistent setting: `joypad_autoconfig_dir = "data/games/retroarch/autoconfig"`;
- project-owned autoconfig directory exists;
- the same relative path below the managed cwd does not exist.

Conclusion: **Baseline 45 validated relative-path behavior only when RetroArch
was launched from the project root. That portability assumption does not hold
for the production EmulatorManager cwd.**

## Production correction

`EmulatorManager._prepare_retroarch_session_config()` now, on Linux only:

1. requires exactly one `joypad_autoconfig_dir` setting in the persistent
   RetroArch config;
2. resolves a relative value through the project root;
3. requires the resolved directory to exist and remain inside the project;
4. replaces only the generated session-config assignment with the normalized
   absolute project-owned path.

The checked-in persistent RetroArch config remains portable and relative. The
RetroArch process cwd is not changed. Windows is untouched.

## Runtime acceptance

Managed revalidation passed after D-076R2: the generated absolute project-owned
autoconfig path was consumed by the real EmulatorManager launch and P1-P4
autoconfigured in deterministic ports 1-4. Live PHI1, Pause/Resume, raw-log
Save/Load, graceful production End, and cleanup also passed. Full onn E2E remains
pending.

## D-076R1 runtime implementation failure

The first managed revalidation did not reach RetroArch startup because the new
Linux branch referenced `sys.platform` without importing `sys`. D-076R2 corrects
only that missing standard-library import. The D-076R1 path-resolution design
remains authoritative and still requires managed runtime revalidation.
