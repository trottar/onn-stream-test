---
memory_schema: 1
as_of: 2026-10-07
baseline_commit: ccee2f5
---

# E3-S4 — a lighter SNES core (Snes9x 1.63), run

**Classification: ACCEPTED by the pre-registered bar.** Every clause
holds in both runs, and the row is REPEATABLE at 20 min
(`e3_s4_verdict.json`).

- **RetroArch: 8.2 / 9.3 % of a core** with Snes9x, against bsnes's
  436 / 517 % in E2.
- **Host CPU: 7.4 / 7.9 %**, against 43.4 / 50.0.
- 60.0 fps everywhere: RetroArch, capture and rendered.
- **This supersedes `E3_S4_SNES_LIGHTER_CORE_2026-10-06.md`** (NOT RUN,
  no core).
- **The core is a fidelity choice and a licence point
  ("Non-commercial").** Nothing perceptual gated this task; **the look is
  the user's** (§4).
- One change, behind `PRIVYHUB_SNES_CORE=snes9x`. **NOT ADOPTED**;
  nothing committed. The flag is absent at the end, and the adopted
  state is restored.

**Context:**

- Task: `handoffs/E3-S4_SNES_LIGHTER_CORE_TASK.md` as written, item 3 of
  `handoffs/QUEUE_2026-10-07.md`.
- The user placed the core by hand; **this task fetched nothing and
  deleted nothing**.
- **Baseline commit: `ccee2f5`.** It ran on the adopted state (E3-S6A).
- Files: `e3_s4_2026-10-07/`.
- Timeline (UTC, 2026-10-07):

  | time | what |
  | --- | --- |
  | 07:42:18 | preconditions held (`precondition.json`) |
  | 07:42-07:43 | the inventory; the change applied |
  | 07:43-07:47 | the 3-min smoke |
  | **07:47:35** | **pre-registration hashed** (`0f16ec55…9ffa`) |
  | 07:47:35-08:44:18 | the 600-s gap, run 1, run 2; both OK (run 1 PLAYING on its second tap, as usual) |

## 1. Inventory (`inventory.txt`)

- **The core is present**:
  - `runtime/emulators/retroarch/cores-linux/snes9x_libretro.so`:
    2,841,720 bytes, **sha256 `9b2b6ea9…7a31`**;
  - beside it `snes9x_libretro.so.zip`: 917,066 bytes, **sha256
    `cfe816af…ad04`**;
  - the zip's one member hashes the same as the `.so`;
  - both stay.
- **What the core reports** (`retro_get_system_info`, read in its own
  process): "Snes9x" / **"1.63 fae2fea"**.
- **The bundled `.info`:** corename "Snes9x", licence
  **"Non-commercial"**. Its `display_version` 1.61 is older than the
  binary.
- bsnes (`ab130614…b4f8`, "115") and the other cores are unchanged.
- **How the row selects the core:**
  - `emulators.json` gives `bsnes_libretro.so`;
  - the one line that selects another is `PRIVYHUB_SNES_CORE=snes9x`;
  - the runner puts its counter override in `config/Snes9x/`.

## 2. The change and the smoke

- **The change** (`patches/E3-S4_SNES_CORE_FLAG.md`,
  `e3_s4_snes_core.diff`). It is the 2026-10-06 prepared diff, unchanged:
  `companion/games/emulator_manager.py`, `_resolve_game`.
  - With `PRIVYHUB_SNES_CORE=<name>`, the core is `<name>_libretro.so`
    from the same directory.
  - Absent: bsnes, unchanged.
  - No core options or per-title settings were written by the task; the
    shared base config (resolution, fullscreen) and the 4x PS1 files are
    untouched.
- **What RetroArch wrote on its own, additive:**
  `~/.config/retroarch/config/Snes9x/Snes9x.opt` (the core's default
  options) and `data/games/retroarch/saves/Snes9x/`.
  - bsnes's `bsnes.opt` is untouched.
  - The runner's counter override was removed after every run.
- **The smoke** (`smoke.json`, `smoke_read.txt`):
  - the core loads (window title "RetroArch Snes9x 1.63 fae2fea");
  - the demo loop runs (59.999 frames/s, 8.5 % of a core);
  - the stream reached PLAYING on attempt 1 (rendered 59.91).
  - The script's own `/proc/<pid>/maps` check came back empty, so
    `smoke.json` says `smoke_ok: false`. That is a defect of the check:
    RetroArch's session log names the core it loaded, and the title
    shows it. Read by hand in `smoke_read.txt`.

## 3. The runs and the bar

From `e3_s4_table.md` (`tools/e3_table.py`), `e3_s4_verdict.json` and
`repeat/repeatability.md` (`tools/e1_suite.py compare`, unchanged, on the
flagged pair), via `e3_s4_analysis.py`:

| | Snes9x r1 | Snes9x r2 | E2 bsnes r1 | E2 bsnes r2 |
| --- | --- | --- | --- | --- |
| **RetroArch CPU, % of a core** | **8.2** | **9.3** | 436.3 | 516.5 |
| **host CPU mean %** | **7.4** | **7.9** | 43.4 | 50.0 |
| RetroArch PSS MB; threads (≥ 30 % of a core) | 110.7; 17 (0) | 110.6; 17 (0) | 241.4; 27 (11) | 241.3; 27 (12) |
| busiest core p95 % | 18.5 | 17.0 | 54.7 | 62.5 |
| PSI cpu some ms/s | 10.4 | 12.0 | 45.3 | 103.0 |
| GPU busy % | 7.4 | 8.0 | 8.0 | 7.0 |
| socket / CPU W | 15.0 / 8.1 | 14.9 / 7.9 | 21.7 / 14.8 | 21.2 / 14.3 |
| Tctl mean / core max °C | 47.8 / 59.5 | 49.1 / 57.0 | 58.6 / 68.5 | 60.5 / 68.8 |
| RetroArch fps; capture fps; rendered fps | 60.0; 60.0; 59.99 | 60.0; 60.0; 59.97 | 60.0; 60.0; 59.66 | 60.0; 60.0; 59.98 |
| encoder dup + drop per min | 0.1 | 0.1 | 0.1 | 0.1 |
| video loss/min (the link's) | 1.9 | 5.4 | 49.1 | 2.5 |
| audio underruns; resyncs | 7; 0 | 11; 0 | 7; 0 | 15; 0 |
| report: spikes ≥ 20 ms/min; stale drops; max gap ms | 37.9; 18; 111 | 36.3; 8; 104 | 39.1; 24; 182 | 40.3; 13; 168 |
| companion CPU % | 24.8 | 25.3 | 24.9 | 24.4 |

| clause | needed (both runs) | got | holds |
| --- | --- | --- | --- |
| a. RetroArch CPU | ≤ 150 % | 8.2 / 9.3 | yes |
| b. host CPU mean | ≤ 20 % | 7.4 / 7.9 | yes |
| c. RetroArch ≥ 59.9; capture 60 ± 0.5; rendered ≥ 59.5 | | 59.999 / 59.999; 59.99 / 59.99; 59.99 / 59.97 | yes |
| d. REPEATABLE on E1's bands | host CPU ± 2, GPU ± 3, RSS ± 5 %, RetroArch ± 0.5, rendered ± 0.5 | 7.44 / 7.86; 7.4 / 8.0; 147.4 / 147.2 MB; 59.999 / 59.999; 59.99 / 59.97 | **REPEATABLE** |
| e. encoder dup + drop | ≤ 0.2 per min | 0.1 / 0.1 | yes |

**Verdict: ACCEPTED.**

**Read beside the bar:**

- **The SNES row stops being the host's heaviest.**
  - With Snes9x it costs less host CPU than PS1-STREAM (7.4-7.9 % vs
    10.4-11.7 %).
  - RetroArch's eleven-plus busy threads are gone: 17 threads, none at
    30 % of a core.
  - PSI cpu falls from 45-103 to 10-12 ms/s; the socket from ~21.5 to
    ~15 W; Tctl by ~11 °C.
- **E2's NOT-YET-REPEATABLE SNES row becomes REPEATABLE.** That fits bsnes's own
  run-to-run variance having moved it (not tested further).
- The stream side is unchanged: the encoder, the companion, spikes and
  the C2 gap are at E2's levels.

## 4. What the user decides — the look, the licence, the line

- **The core:** Snes9x 1.63 (`snes9x_libretro.so`, sha256 `9b2b6ea9…7a31`),
  licence "Non-commercial". It is a different emulator: accuracy and
  look differ from bsnes.
- **A look by hand** (`TOOLS.md`, "The E3 flags"):

  ```bash
  printf '[Service]\nEnvironment=PRIVYHUB_SNES_CORE=snes9x\n' > ~/.config/systemd/user/privyhub-companion.service.d/e3_flag.conf
  systemctl --user daemon-reload && systemctl --user restart privyhub-companion
  # start Super Mario World from the launcher on the TV, as usual (or: curl -X POST 'localhost:8765/plugins/games/launch?id=game_snes_c6fecdcdddb35398')
  # ... look ...
  rm ~/.config/systemd/user/privyhub-companion.service.d/e3_flag.conf
  systemctl --user daemon-reload && systemctl --user restart privyhub-companion
  python3 tools/e3_state.py      # "ok": true -- the adopted state again
  ```

  Note: saves are per core. Snes9x writes its own `saves/Snes9x/`, so
  bsnes's saves are not seen during a look.
- **Adoption, if the look and the licence are acceptable:** one drop-in
  line, `Environment=PRIVYHUB_SNES_CORE=snes9x`, in its own file (e.g.
  `snes-core.conf`), with `ADOPTED` gaining that name.
  - Gain: ~4-5 cores of CPU and ~6.5 W while a SNES game streams; the row
    becomes repeatable.
  - Cost: bsnes's accuracy, and the licence.
  - Changing `emulators.json`'s `snes` core is the alternative, without a
    flag.
- **Revert:** unset the flag (delete the line). The `.so` and
  RetroArch's `Snes9x/` files may stay.

## 5. State at the end; files

- **Final state** (`runs/final_state.json`, 08:44:18Z):
  - manager none;
  - environ exactly the adopted two lines;
  - the e3 drop-in absent;
  - no game, RetroArch or encoder;
  - the PS1 files identical; **APK CONFIRMED**.
- No `nft`, no real `sudo`, the Opal untouched; nothing fetched, nothing
  deleted.
- Files (`e3_s4_2026-10-07/`):
  - `precondition.json`, `inventory.txt`, `e3_s4_snes_core.diff`;
  - `e3_s4_smoke.py`, `smoke/`, `smoke.json`, `smoke_console.log`,
    `smoke_read.txt`;
  - the pre-registration and its `.sha256`;
  - `runs/` (2 runs, `manifest.sha256`, `--check` OK in
    `runs/check.txt`), `runs_console.log`;
  - `e3_s4_analysis.py`, `e3_s4_table.md/.json`, `repeat/`,
    `e3_s4_verdict.json`, `redact_check.txt`.
- Git status: `logs/e3_s4_git_status.txt` (supersedes the 2026-10-06 one).
