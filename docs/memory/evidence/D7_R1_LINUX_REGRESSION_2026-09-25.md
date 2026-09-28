---
memory_schema: 1
as_of: 2026-09-25
status: D7-R1 DONE — the D7 native Linux regression scripted (tools/d7_regression.py) and run twice, 10 min apart, on the adopted build (adopted APK f31b1c18…8ae7, profile adopted, no override); 8 of 10 rows PASS in both passes, restart/recovery VALIDATED (cited, not re-run: needs nft), profiles/cheats/mod state FAIL as scripted in both passes because of a script defect (the cheat count is per source) — every field it checks read as expected, the corrected count read 12 on recheck; NEEDS USER: controller feel and the picture (a 10-minute list); user save slots and the slot index hash-identical before and after; scratch removed
---

# D7-R1 — the native Linux regression, scripted where it can be

Task: `handoffs/D7-R1_LINUX_REGRESSION_TASK.md` (weekend queue 2, item 3,
authorized by the user 2026-09-25). Script: `tools/d7_regression.py`, a
new tools-only file with no companion, client or profile change. Evidence:
`d7_r1_2026-09-25/` (`d7_P1.{json,txt}`, `d7_P2.{json,txt}`,
`d7_profiles_recheck.json`, the D136 outputs, `d7_r1_all.{sh,log}`,
`slot_hashes_end.txt`, manifest).

**Gate.** Task 2's teardown was complete before the first pass:

- the adopted APK was on the onn (device hash `f31b1c18…`);
- `PRIVYHUB_*` read 0 in the manager and the companion's environ;
- `fec.version` read `xor8_1` and `any_override` false;
- the stream was inactive, and scratch slot 3 was empty.

**Passes.** P1 ran 05:59-06:05Z and P2 06:14-06:20Z, 10 min apart. Each
restarted the companion through its unit in row 1 only.

## The table

| D7 row | P1 | P2 | evidence (P1 / P2) |
| --- | --- | --- | --- |
| server boot/start | **PASS** | **PASS** | `systemctl --user restart`: MainPID owned 8765 in 1.1 s; `/status` 200, service PrivyHub; `native-stream-status` ready with the adopted profile (cap 90,000, cushion 12/17, redundancy 2/4, `xor8_1`, `any_override` false); 0 `PRIVYHUB_*` |
| client discovery/control | **PASS** | **PASS** | cold-started app: the journal shows the client's `GET /sources` and `GET /plugins/games/status` (counted, no address kept); the launcher shows the library; controller transport active once the stream was up |
| media | **PASS** | **PASS** | the `D136` probe as it runs today: `D136_FOCUSED_TV_MEDIA_AUTOMATED_REGRESSION_VALIDATED`, no problems. It re-runs `D122` fresh and reads `D133` / `D135` from their 2026-09-17 files; it does not prove visible playback |
| Games launch | **PASS** | **PASS** | `POST launch` Tekken 3 (PS1 reference) → active; RESUME PLAYING → `NativeStreamActivity`, recovery PLAYING |
| video/audio/controller | **PASS** + NEEDS USER | **PASS** + NEEDS USER | 3-min hold: 89 heartbeats; rendered fps 59.9 / 60.0; audio sent +36,002 / +36,001 and the client's audio rx +35,429 / +35,431; controller received +77,862 / +77,866; video lost 44 / 0. **Feel and picture: NEEDS USER** |
| pause/resume | **PASS** | **PASS** | there is no pause route; the user's pause is BACK. After BACK: active, paused (report stored). RESUME PLAYING → paused false, recovery PLAYING, 13 / 12 heartbeats in the next 25 s |
| Save/Load | **PASS** | **PASS** | scratch slot 3 (empty before): save 200 (2,061,944 / 2,061,325 B state), load 200, the game left paused; cleanup: slot 3 removed, the slot index and the title's slot-0 `.state` restored from backup, **all hashes as before**, 54 other state files hash-identical |
| profiles/cheats/mod state | **FAIL (script defect)** | **FAIL (script defect)** | see below |
| End/teardown | **PASS** | **PASS** | RESUME, then BACK → a decoder report stored (journal: 1 stored, 0 WARNING; cap in force); `POST stop` 200 → inactive; the launcher shows no "NOW PLAYING"; the companion still serving |
| restart/recovery | **VALIDATED (cited)** | **VALIDATED (cited)** | `R3`-`R3d` (N05, N15b, E30 PASS on real loss) and `R3c2` (resume, copy, discard). Not re-run: real link loss needs the user's `nft` |

**Rows scripted: 9.**

- 8 PASS in both passes. Nothing is flaky across the two.
- 1 FAIL in both, from a defect in the script.
- 1 cited.

**Profiles/cheats/mod state, the FAIL.** In both passes every route
answered 200, with a game active:

- `cheat-catalog` cached;
- `cheat-profiles` 0 profiles;
- `mod-catalog` / `mod-profiles` unsupported, `core_softpatching_unsupported`
  (PS1 has no softpatching);
- `active-cheats` inactive;
- `input-profiles` read;
- no cheat or mod session;
- **no residue**: `cheats.json` and the cheat- and mod-profile trees
  hash-identical.

The script's check `cheat_count > 0` read the count at the top level, but
the route reports it per source (`sources[i].cheat_count`). So it read
null and the row failed.

- The script was fixed (it now sums the sources), and the row was run
  once more on its own (`d7_profiles_recheck.json`). The count read **12**,
  and no residue.
- That recheck still reads FAIL, because `active-cheats` answers 503 with
  no game active (the passes had one).
- No further session was run for it.

**Reading.** The row's state is as expected on every field. The scripted
verdict stands as FAIL in both passes, attributed to the script. A next
pass with the fixed script will score it directly.

## NEEDS USER — ten minutes with a controller

1. On the TV: GAMES → CONTINUE PLAYING → **Tekken 3 (USA)**, then launch
   it. It opens on the frozen preview, paused.
2. Press **RESUME PLAYING**. Play for two minutes with the controller.
   **Say whether the input feels right**: direction, buttons and
   responsiveness.
3. **Say whether the picture and the sound look and sound right**: no
   tearing, stutter, or audio gaps you can notice.
4. Press **BACK**. The game stays paused; the NOW PLAYING bar shows it.
   Press **RESUME PLAYING** again, and it resumes.
5. From the game's menu or the launcher, **save to a slot** you do not
   mind using, then **load it**. Say whether the loaded state is right.
6. From the NOW PLAYING bar press **END**, then **Don't Save**. The bar
   disappears.

## D8 acceptance, as it stands

| D8 item | status |
| --- | --- |
| Linux is sufficient for normal core server operation | **met on the scripted rows** (boot, discovery, media, games, End); **the user's rows pending** |
| PS1-and-below works through Linux-native A/V/input paths | PS1 **met on the scripted rows** (fps, audio, controller datagrams); feel and picture pending; NES / Genesis have no local fixture (`D090`) |
| onn client remains functional | **met** (discovery, launch, stream, BACK/RESUME, End) |
| media/Live TV remain functional | **met** by `D136` (automated; the visible-playback smoke is the user's) |
| deferred UDP suite replayed/reclassified | **met** (`D6-R1`) |
| no minimum-hardware claim yet | held |
| clean checkpoint/push | pending (the user's) |

## Scope kept

- **User data.** The user's save slots were untouched. Tekken 3's slots
  1-2 stayed empty. The slot index (`18bebda8…`) and the title's slot-0
  `.state` (`05bd85c7…`) are the same as before the queue ran
  (`slot_hashes_end.txt`), and 54 other state files are hash-identical.
- **The scratch backup** was kept under `runtime/d7_r1/` (gitignored). It
  was compared with the live files and removed at the end.
- **Play statistics.** `launch` updated the title's play count in
  `data/games/library_state.json`, as every scripted session does.
- **Nothing else changed.** No `nft`, and nothing written to the Opal.
- **Privacy.** The D136 JSON copies were checked: no serial, no address.
  `--check` reports 0 residual matches on every file.

## R2 — the profiles row, scored with the fixed script (2026-09-25, `D7-R2`)

Task: `handoffs/PHASE_C_PRECONDITIONS_2026-09-25_TASK.md` §2.

**Before the pass:**

- the adopted APK was on the onn (hash `f31b1c18…`);
- `any_override` false;
- the stream was at 7000 with the game inactive;
- scratch slot 3 was empty;
- the slot index read `18bebda8…` and the slot-0 `.state` read `05bd85c7…`.

**Why a full pass.** The script cannot run a single row with a game
active, because its rows depend on the preceding ones. So, as the task
allows, one full pass **P3** ran with the fixed script (06:53:49-06:59:17Z;
`d7_P3.{json,txt}`, `d7_r2_P3.log`).

| D7 row | P3 |
| --- | --- |
| server boot/start | PASS (MainPID owned 8765 in 1.1 s, profile adopted, `xor8_1`, 0 `PRIVYHUB_*`) |
| client discovery/control | PASS |
| media | PASS (`D136` validated) |
| Games launch | PASS |
| video/audio/controller | PASS + NEEDS USER (89 heartbeats, 60.0 fps, audio +36,001 / client +35,431, controller +77,952, video lost 0) |
| pause/resume | PASS |
| Save/Load | PASS (scratch slot 3, 2,051,779 B, hashes restored, 54 other state files identical) |
| **profiles/cheats/mod state** | **PASS** |
| End/teardown | PASS (report stored, 0 WARNING, inactive, no banner) |
| restart/recovery | VALIDATED (cited) |

**The profiles row, scored against the pre-registered rule.** With a game
active, every field read as the R1 record lists:

- `cheat-catalog` cached, **cheat count summed across sources: 12**;
- `cheat-profiles` 0;
- `mod-catalog` / `mod-profiles` unsupported (`core_softpatching_unsupported`,
  PS1);
- `active-cheats` inactive (HTTP 200);
- `input-profiles` read;
- no cheat or mod session;
- **no residue by hash** (`cheats.json` and the cheat- and mod-profile
  trees).

→ **PASS**, first try, no retries.

**The regression now stands at 9 of 9 scripted rows PASS in one pass**
with the fixed script (restart/recovery cited). The NEEDS USER list above
is unchanged.

**After the pass:**

- the slot index and the slot-0 `.state` hash as before (`18bebda8…`,
  `05bd85c7…`);
- slot 3 is removed;
- the scratch backup under `runtime/d7_r1/` was compared with the live
  files and removed;
- the launcher shows no NOW PLAYING banner.
