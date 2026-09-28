---
memory_schema: 1
as_of: 2026-09-25
status: TASK HANDOFF — D7-R1: run the roadmap's D7 native Linux regression as far as it can be run without a person — one script, one row per D7 item, PASS / FAIL / NEEDS USER with the evidence for each — on the adopted build; no code change outside tools/; authorized by the user 2026-09-25
---

# D7-R1 — the native Linux regression, scripted where it can be

**Why.** `docs/ROADMAP.md` D7 lists the minimum normal-use regression:
server boot/start, client discovery/control, media, Games launch,
video/audio/controller, pause/resume, Save/Load, profiles/cheats/mod
state, End/teardown, restart/recovery. D8 needs it passed. Most rows are
exercised by probes that already exist and are runtime-validated
(`D136` focused TV-media automated acceptance, `R3c2`'s seven adb-driven
checks, the `p9_run.sh` session harness, the companion's own status
surfaces); nobody has run them as one D7 pass on the build as it stands.
Rows that need a person (controller feel, the TV's look) are reported as
NEEDS USER with what the user must do, not faked.

Read first: `docs/ROADMAP.md` §D7 and §D8, `docs/PROJECT_STATUS.md`,
`evidence/D136_FOCUSED_TV_MEDIA_AUTOMATED_ACCEPTANCE_2026-09-17.md` and
its probe, `evidence/D_BASE_R3C2_RECOVERY_FLOW_2026-09-23.md`
(`r3c2_checks.py`: launcher navigation by `uiautomator` text), `TOOLS.md`
(host-shell sessions, save-state slots, teardown, the companion unit),
`evidence/D090_D4_LINUX_GAMES_ACCEPTANCE_2026-09-16.md`, `D088…MULTITAP…`,
`evidence/H3_COMPANION_AUTOSTART_DESIGN_2026-09-23.md`, the games plugin
routes (`companion/plugins/games.py`: launch / stop / pause / resume /
save / load / cheats / mods / status).

**Scope.** One new script `tools/d7_regression.py` (plus its report),
using existing routes, probes and adb; **no companion, client or profile
change**; the adopted profile; the companion restarted only through its
unit and only where the row requires it (boot/start). ROMs, saves and
savestates stay out of git; anything the script writes to a save slot is
written to a scratch slot the record names and is removed at the end,
never over the user's slots (`r3c2` used `slot_backup/` — do the same,
hash before and after). No `nft` — the restart/recovery row cites `R3`/`R3d`
and is marked "validated 2026-09-20/22, not re-run" unless a no-`nft`
check exists. Never retry a failing action more than twice; a failing row
is FAIL with the evidence, and the pass continues.

## Rows (one each, in the report)

| D7 row | how, unattended | verdict space |
| --- | --- | --- |
| server boot/start | `systemctl --user restart privyhub-companion`; MainPID owns 8765 within N s; `/status` ok; `native-stream-status` ready with the adopted profile | PASS/FAIL |
| client discovery/control | the onn app cold-started by adb reaches the library; its status poll hits the companion (journal); controller transport active on `native-stream-status` once a stream is up | PASS/FAIL |
| media | the `D136` focused TV-media automated acceptance probe as it runs today | PASS/FAIL |
| Games launch | `POST launch` of the PS1 reference title → active, PLAYING via the launcher's RESUME PLAYING (`p9_run.sh` path) | PASS/FAIL |
| video/audio/controller | 3-minute hold: heartbeats flow, rendered fps ≥ 59.5, audio packets sent and the client's audio counters advance, controller `packets_received` advancing; **feel and picture: NEEDS USER** | PASS/FAIL + NEEDS USER |
| pause/resume | the companion's pause and resume routes: game `paused` true/false, the stream survives, heartbeats continue | PASS/FAIL |
| Save/Load | save to a scratch slot, load it, the slot's state file appears with the expected size/hash pattern; user's slots untouched (hashes before/after) | PASS/FAIL |
| profiles/cheats/mod state | the routes report the expected state for the reference title (read-only unless a scratch toggle exists that leaves no residue) | PASS/FAIL |
| End/teardown | BACK → decoder report stored (cap in force), `POST stop` → inactive, banner cleared (`uiautomator` has no "NOW PLAYING"), companion still serving | PASS/FAIL |
| restart/recovery | cite `R3`-`R3d`, `R3c2` — validated on real loss; not re-run (no `nft` unattended) | VALIDATED (cited) |

Two full passes, ≥ 10 minutes apart, so a flaky row shows as such.

## Record and memory

`evidence/D7_R1_LINUX_REGRESSION_<date>.md` with the table (two passes),
the evidence per row, the NEEDS USER list as numbered steps the user can
do in ten minutes with a controller, and D8's acceptance rows marked;
evidence dir with the script's outputs, reports, journal extracts
(redacted), slot hashes, manifest; `docs/ROADMAP.md` D7/D8 lines;
`docs/PROJECT_STATUS.md`; `CURRENT.md`; `investigations/ACTIVE.md`; the
daily file; `TOOLS.md` (the script). No addresses or device identifiers.
Nothing committed.
